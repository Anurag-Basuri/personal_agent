"""Constructs LangGraph workflows for the Agent.

Two graph variants:
  1. agent_app (full): All tools + MCP — for authenticated users
  2. public_agent (restricted): Portfolio-safe tools only — for public chatbot

Graph Architecture:
    router → agent → should_continue? → tools → agent → ... → END
    
The router classifies intent first. Greetings and meta questions
skip tool binding entirely for faster, cheaper responses.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langgraph.graph import END, StateGraph

from app.agent.core.nodes import (
    call_model,
    call_tools,
    make_call_model,
    make_call_tools,
    route_intent,
)
from app.agent.core.state import AgentState


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Determines if the graph should execute tools or end."""
    last_message = state["messages"][-1]

    # If the LLM requested tool calls, route to "tools"
    if getattr(last_message, "tool_calls", []):
        return "tools"

    # Otherwise, finish execution
    return "__end__"


def _build_graph(call_model_node, call_tools_node):
    """Internal helper: constructs a StateGraph with the given node implementations."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", route_intent)
    workflow.add_node("agent", call_model_node)
    workflow.add_node("tools", call_tools_node)

    # Set the entry point — always start with intent classification
    workflow.set_entry_point("router")

    # Router always flows into the agent
    workflow.add_edge("router", "agent")

    # Agent conditionally routes to tools or ends
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    # From tools, it should always route back to the agent to synthesize the response
    workflow.add_edge("tools", "agent")

    # Compile the graph
    return workflow.compile()


def build_agent_graph():
    """Builds the full agent graph (all tools + MCP). Used by authenticated endpoints."""
    return _build_graph(call_model, call_tools)


@lru_cache(maxsize=1)
def build_public_agent():
    """Builds the public portfolio chatbot graph (restricted tools, no MCP).

    Uses lru_cache to avoid recompiling on every request.
    The graph is compiled once and reused for all public chat requests.
    """
    from app.agent.tools import get_public_tools

    public_call_model = make_call_model(get_public_tools)
    public_call_tools = make_call_tools(get_public_tools)
    return _build_graph(public_call_model, public_call_tools)


# Singleton instance of the full agent graph
agent_app = build_agent_graph()
