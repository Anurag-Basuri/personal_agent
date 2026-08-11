"""LangGraph nodes: Intent Router, LLM invocation (via orchestrator), and Tool Execution.

Resilience patterns applied:
  - Centralized LLMOrchestrator handles the 6-layer cascade internally
    (circuit breakers, smart error classification, per-tier timeouts)
  - Tool execution uses retry_with_backoff for transient failures
  - Layer 6 static fallback (never crashes)
  - Graceful degradation tracking via SystemHealth

The call_model and call_tools functions use get_all_tools by default.
For the public portfolio chatbot, use make_call_model(tools_getter)
and make_call_tools(tools_getter) to inject a restricted toolset.
"""

from __future__ import annotations

from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.core.state import AgentState
from app.agent.llm import orchestrator
from app.agent.tools import get_all_tools
from app.core.logger import agent_logger
from app.core.retry import retry_with_backoff


# Layer 6: Static Fallback Message
# This is the safety net. If all 5 LLM tiers fail (rate limits,
# network errors, circuit breakers all OPEN), this message is
# returned to the user. It NEVER fails because it's pure Python.
STATIC_FALLBACK_MESSAGE = (
    "I'm temporarily unable to process your request as all my AI providers "
    "are experiencing issues. Please try again in a few minutes. "
    "I apologize for the inconvenience!"
)


# Keywords for fast intent classification
_GREETING_PATTERNS = {
    "hi", "hello", "hey", "howdy", "sup", "yo", "what's up",
    "good morning", "good evening", "good afternoon", "greetings",
    "namaste", "hola",
}

_META_PATTERNS = {
    "who are you", "what can you do", "help", "what are you",
    "how do you work", "what tools", "capabilities",
}


async def route_intent(state: AgentState) -> dict:
    """
    Lightweight intent classifier -- routes messages to skip tools when unnecessary.

    Intents:
      - "greeting": Simple hello/hi -> skip tools, direct LLM reply
      - "meta_question": Questions about the agent itself -> skip tools
      - "tool_use": Everything else -> full agent+tools cycle
    """
    messages = state["messages"]

    # Find the last human message
    user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_msg = str(msg.content).strip().lower()
            break

    if not user_msg:
        return {"intent": "tool_use"}

    intent = classify_intent(user_msg)
    agent_logger.debug("ROUTER", f"Intent: {intent} -- '{user_msg[:40]}'")
    ret = {"intent": intent}

    # Dynamic Tool Routing for Admin (to prevent 233-tool overload)
    if intent == "tool_use" and state.get("role") == "ADMIN":
        try:
            from pydantic import BaseModel, Field
            from app.mcp.client import mcp_manager
            
            available_servers = [k for k, v in mcp_manager.get_status().items() if v == "connected"]
            
            if available_servers:
                class MCPRouting(BaseModel):
                    needed_servers: list[str] = Field(
                        description=f"List of MCP servers needed. Options: {', '.join(available_servers)}"
                    )
                
                providers = orchestrator.get_providers()
                if providers:
                    # Use Tier 1 (fastest model) for classification
                    llm = providers[0].llm
                    structured_llm = llm.with_structured_output(MCPRouting)
                    prompt = (
                        "You are a routing agent. Determine which of the available MCP servers "
                        "are necessary to fulfill the user's request. Only return servers that are strictly required.\n\n"
                        f"User Request: {user_msg}\n"
                        f"Available Servers: {', '.join(available_servers)}"
                    )
                    res = await structured_llm.ainvoke(prompt)
                    
                    # Ensure only valid servers are returned
                    valid_servers = [s for s in res.needed_servers if s in available_servers]
                    ret["active_servers"] = valid_servers
                    agent_logger.debug("ROUTER", f"Activated servers: {valid_servers}")
        except Exception as e:
            agent_logger.warn("ROUTER", f"Failed to dynamically route servers: {e}")
            ret["active_servers"] = None  # fallback to loading everything
            
    return ret


def classify_intent(user_msg: str) -> str:
    """Fast keyword-based intent classification for a single string."""
    cleaned = user_msg.rstrip("!?.,:;")

    if cleaned in _GREETING_PATTERNS or any(cleaned.startswith(g) for g in _GREETING_PATTERNS):
        return "greeting"

    if any(p in user_msg for p in _META_PATTERNS):
        return "meta_question"

    return "tool_use"


def make_call_model(tools_getter=get_all_tools):
    """Factory: returns a call_model node wired to the given tools getter."""

    async def _call_model(state: AgentState):
        """
        Invoke the LLM using the centralized orchestrator.

        The orchestrator handles the entire 6-layer cascade internally:
          - Smart error classification (permanent/rate_limited/transient)
          - Per-tier circuit breakers
          - Hard per-attempt timeouts (10s)
          - Runtime tier disabling for 404s

        If all tiers fail, returns Layer 6 static message (never crashes).
        """
        messages = state["messages"]
        role = state.get("role", "GUEST")
        # Determine which tools to activate
        intent = state.get("intent", "tool_use")
        active_servers = state.get("active_servers")

        # Bind all currently available tools via the getter
        try:
            available_tools = tools_getter(active_servers)
        except TypeError:
            available_tools = tools_getter()

        allowed_tools = []
        for t in available_tools:
            if getattr(t, "requires_admin", False) and role != "ADMIN":
                continue
            allowed_tools.append(t)

        # For greetings and meta questions, skip tools entirely (faster + cheaper)
        if intent in ("greeting", "meta_question"):
            allowed_tools = []

        # Delegate to the orchestrator
        response = await orchestrator.invoke(messages, allowed_tools or None)

        if response is not None:
            return {"messages": [response]}

        # Layer 6: Static Fallback
        agent_logger.error(
            "LLM",
            "[STATIC] ALL LLM tiers exhausted -- returning static fallback",
            None,
            {"tiers_configured": len(orchestrator.get_providers())},
        )
        return {"messages": [AIMessage(content=STATIC_FALLBACK_MESSAGE)]}

    return _call_model


# Default call_model uses get_all_tools (backward compatible)
call_model = make_call_model(get_all_tools)


def make_call_tools(tools_getter: Callable[[], list] = get_all_tools):
    """Factory: returns a call_tools node wired to the given tools getter."""

    async def _call_tools(state: AgentState):
        """Executes the requested tools with retry for transient failures."""
        # The last message is the AIMessage with tool_calls
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        if not tool_calls:
            return {"messages": []}

        tool_map = {t.name: t for t in tools_getter()}
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
                # Retry tool execution for transient failures
                tool_output = await retry_with_backoff(
                    selected.ainvoke,
                    tool_args,
                    max_retries=2,
                    base_delay=0.5,
                    max_delay=5.0,
                    retryable_exceptions=(TimeoutError, ConnectionError),
                    operation_name=f"Tool:{tool_name}",
                )
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

    return _call_tools


# Default call_tools uses get_all_tools (backward compatible)
call_tools = make_call_tools(get_all_tools)
