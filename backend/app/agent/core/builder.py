"""Constructs the LangGraph workflow for the Agent.

Graph Architecture:
    router → agent → should_continue? → tools → agent → ... → END
    
The router classifies intent first. Greetings and meta questions
skip tool binding entirely for faster, cheaper responses.
"""

from langgraph.graph import StateGraph, END
from typing import Literal

from app.agent.core.state import AgentState
from app.agent.core.nodes import route_intent, call_model, call_tools

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Determines if the graph should execute tools or end."""
    last_message = state["messages"][-1]
    
    # If the LLM requested tool calls, route to "tools"
    if getattr(last_message, "tool_calls", []):
        return "tools"
        
    # Otherwise, finish execution
    return "__end__"

def build_agent_graph():
    """Builds and compiles the StateGraph with intent routing."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", route_intent)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", call_tools)

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
    app = workflow.compile()
    
    return app

# Singleton instance of the graph
agent_app = build_agent_graph()

