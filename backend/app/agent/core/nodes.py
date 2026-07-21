"""LangGraph nodes: Intent Router, LLM invocation, and Tool Execution.

Resilience patterns applied:
  - Circuit Breaker around the primary LLM (skips instantly when down)
  - Retry with exponential backoff on LLM and tool calls
  - Graceful degradation tracking via SystemHealth
"""

from langchain_core.messages import HumanMessage, ToolMessage

from app.agent.core.state import AgentState
from app.agent.llm import get_bound_llms, llm_info
from app.agent.tools import get_all_tools
from app.core.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.core.degradation import system_health
from app.core.logger import agent_logger
from app.core.rate_limiter import check_llm_budget
from app.core.retry import retry_with_backoff

# ─── Circuit Breakers ────────────────────────────────────────────
# Primary LLM breaker: trips after 3 consecutive failures, recovers after 60s
primary_llm_breaker = CircuitBreaker(
    name="PrimaryLLM",
    failure_threshold=3,
    recovery_timeout=60,
    expected_exceptions=(Exception,),
)


# ─── Keywords for fast intent classification ─────────────────────

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
    Lightweight intent classifier — routes messages to skip tools when unnecessary.
    
    Intents:
      - "greeting": Simple hello/hi → skip tools, direct LLM reply
      - "meta_question": Questions about the agent itself → skip tools
      - "tool_use": Everything else → full agent+tools cycle
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

    # Fast keyword match — no LLM call needed for obvious intents
    cleaned = user_msg.rstrip("!?.,:;")

    if cleaned in _GREETING_PATTERNS or any(cleaned.startswith(g) for g in _GREETING_PATTERNS):
        agent_logger.debug("ROUTER", f"Intent: greeting — '{user_msg[:40]}'")
        return {"intent": "greeting"}

    if any(p in user_msg for p in _META_PATTERNS):
        agent_logger.debug("ROUTER", f"Intent: meta_question — '{user_msg[:40]}'")
        return {"intent": "meta_question"}

    agent_logger.debug("ROUTER", f"Intent: tool_use — '{user_msg[:40]}'")
    return {"intent": "tool_use"}


async def call_model(state: AgentState):
    """Invokes the dual-LLM setup with circuit breaker + retry for resilience."""
    messages = state["messages"]
    role = state.get("role", "GUEST")
    intent = state.get("intent", "tool_use")

    # ─── Role-Based Access Control (RBAC) ───
    # Filter tools before binding to LLM.
    # Admin tools might have a custom attribute like `requires_admin`
    # For now, if role == GUEST, limit to safe tools (we assume all default are safe until we add dangerous ones)
    allowed_tools = []
    for t in get_all_tools():
        if getattr(t, "requires_admin", False) and role != "ADMIN":
            continue
        allowed_tools.append(t)

    # For greetings and meta questions, don't bind any tools — faster and cheaper
    if intent in ("greeting", "meta_question"):
        allowed_tools = []

    llms = get_bound_llms(allowed_tools)
    primary = llms["primary"]
    fallback = llms["fallback"]

    response = None

    # ─── Attempt Primary (with Circuit Breaker + Retry + Budget) ───
    if primary and check_llm_budget("llm_primary"):
        start = agent_logger.llm_start(llm_info.primary_provider, llm_info.primary_model)
        try:
            response = await primary_llm_breaker.call(
                retry_with_backoff,
                primary.ainvoke,
                messages,
                max_retries=2,
                base_delay=1.0,
                retryable_exceptions=(TimeoutError, ConnectionError, Exception),
                operation_name=f"LLM:{llm_info.primary_provider}",
            )
            tool_calls = getattr(response, "tool_calls", [])
            agent_logger.llm_success(start, len(tool_calls) > 0, len(tool_calls))
            system_health.mark_up("primary_llm")

        except CircuitOpenError:
            agent_logger.warn(
                "LLM",
                f"🔴 Circuit OPEN for {llm_info.primary_provider} — skipping to fallback instantly",
            )
            system_health.mark_down("primary_llm")

        except Exception as e:
            agent_logger.llm_error(start, e)
            agent_logger.warn(
                "LLM",
                f"🔒 Primary failed, switching to fallback ({llm_info.fallback_provider})",
            )

    # ─── Attempt Fallback ───
    if response is None and fallback:
        fb_start = agent_logger.llm_start(llm_info.fallback_provider, llm_info.fallback_model)
        try:
            response = await retry_with_backoff(
                fallback.ainvoke,
                messages,
                max_retries=2,
                base_delay=1.0,
                retryable_exceptions=(TimeoutError, ConnectionError, Exception),
                operation_name=f"LLM:{llm_info.fallback_provider}",
            )
            tool_calls = getattr(response, "tool_calls", [])
            agent_logger.llm_success(fb_start, len(tool_calls) > 0, len(tool_calls))
            system_health.mark_up("fallback_llm")

        except Exception as fb_error:
            agent_logger.llm_error(fb_start, fb_error)
            system_health.mark_down("fallback_llm")
            raise fb_error

    if response is None:
        raise RuntimeError("No LLM providers available — both primary and fallback failed.")

    return {"messages": [response]}


async def call_tools(state: AgentState):
    """Executes the requested tools with retry for transient failures."""
    # The last message is the AIMessage with tool_calls
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])

    if not tool_calls:
        return {"messages": []}

    tool_map = {t.name: t for t in get_all_tools()}
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
