"""Constructs the LangGraph workflow for the Agent."""

from langgraph.graph import StateGraph, END
from typing import Literal

from app.graph.state import AgentState
from app.graph.nodes import call_model, call_tools

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Determines if the graph should execute tools or end."""
    last_message = state["messages"][-1]
    
    # If the LLM requested tool calls, route to "tools"
    if getattr(last_message, "tool_calls", []):
        return "tools"
        
    # Otherwise, finish execution
    return "__end__"

def build_agent_graph():
    """Builds and compiles the StateGraph."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", call_tools)

    # Set the entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
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
    app = workflow.compile()
    
    return app

# Singleton instance of the graph
agent_app = build_agent_graph()
