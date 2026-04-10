"""LangGraph nodes: LLM invocation and Tool Execution."""

import json
from langchain_core.messages import ToolMessage
from app.agent.llm import get_bound_llms, llm_info
from app.core.logger import agent_logger
from app.agent.tools import agent_tools
from app.agent.core.state import AgentState

async def call_model(state: AgentState):
    """Invokes the dual-LLM setup with proper tool binding depending on user role."""
    messages = state["messages"]
    role = state.get("role", "GUEST")
    
    # ─── Role-Based Access Control (RBAC) ───
    # Filter tools before binding to LLM.
    # Admin tools might have a custom attribute like `requires_admin`
    # For now, if role == GUEST, limit to safe tools (we assume all default are safe until we add dangerous ones)
    allowed_tools = []
    for t in agent_tools:
        if getattr(t, "requires_admin", False) and role != "ADMIN":
            continue
        allowed_tools.append(t)
        
    llms = get_bound_llms(allowed_tools)
    primary = llms["primary"]
    fallback = llms["fallback"]
    
    # Attempt Primary
    start = agent_logger.llm_start(llm_info.primary_provider, llm_info.primary_model)
    try:
        if primary:
            # Note: Timeout handling can be configured directly in ChatOpenAI params or via asyncio
            response = await primary.ainvoke(messages)
            tool_calls = getattr(response, "tool_calls", [])
            agent_logger.llm_success(start, len(tool_calls) > 0, len(tool_calls))
        else:
            raise Exception("No primary LLM configured.")
    except Exception as e:
        agent_logger.llm_error(start, e)
        agent_logger.warn("LLM", f"🔒 Primary failed, switching to fallback ({llm_info.fallback_provider})")
        
        # Attempt Fallback
        if fallback:
            fb_start = agent_logger.llm_start(llm_info.fallback_provider, llm_info.fallback_model)
            try:
                response = await fallback.ainvoke(messages)
                tool_calls = getattr(response, "tool_calls", [])
                agent_logger.llm_success(fb_start, len(tool_calls) > 0, len(tool_calls))
            except Exception as fb_error:
                agent_logger.llm_error(fb_start, fb_error)
                raise fb_error
        else:
            raise e

    return {"messages": [response]}


async def call_tools(state: AgentState):
    """Executes the requested tools and logs the results."""
    # The last message is the AIMessage with tool_calls
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])
    
    if not tool_calls:
        return {"messages": []}
        
    tool_map = {t.name: t for t in agent_tools}
    results = []
    
    for tc in tool_calls:
        tool_name = tc.get("name")
        tool_args = tc.get("args", {})
        tool_id = tc.get("id")
        
        selected = tool_map.get(tool_name)
        if not selected:
            agent_logger.warn("TOOL", f'Tool "{tool_name}" not found', {"args": tool_args})
            msg = ToolMessage(
                tool_call_id=tool_id,
                content=f"Tool {tool_name} not found or unauthorized.",
                name=tool_name,
            )
            results.append(msg)
            continue
            
        t_start = agent_logger.tool_start(tool_name, tool_args)
        try:
            # Execute tool
            tool_output = await selected.ainvoke(tool_args)
            output_str = str(tool_output)
            agent_logger.tool_success(tool_name, t_start, output_str)
            
            msg = ToolMessage(
                tool_call_id=tool_id,
                content=output_str,
                name=tool_name,
            )
            results.append(msg)
        except Exception as e:
            agent_logger.tool_error(tool_name, t_start, e)
            msg = ToolMessage(
                tool_call_id=tool_id,
                content=f"Failed to execute tool: {e}",
                name=tool_name,
            )
            results.append(msg)
            
    return {"messages": results}
