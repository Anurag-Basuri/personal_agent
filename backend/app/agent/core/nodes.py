"""LangGraph nodes: Intent Router, LLM invocation (6-layer cascade), and Tool Execution.

Resilience patterns applied:
  - 5 independent Circuit Breakers (one per LLM tier)
  - Retry with exponential backoff on each tier
  - Layer 6 static fallback — never crashes
  - Graceful degradation tracking via SystemHealth
  - LLM budget checks per tier

The call_model and call_tools functions use get_all_tools by default.
For the public portfolio chatbot, use make_call_model(tools_getter)
and make_call_tools(tools_getter) to inject a restricted toolset.
"""

from __future__ import annotations

from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.core.state import AgentState
from app.agent.llm import get_bound_providers
from app.agent.tools import get_all_tools
from app.core.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.core.degradation import system_health
from app.core.logger import agent_logger
from app.core.rate_limiter import check_llm_budget
from app.core.retry import retry_with_backoff


# ─── Circuit Breakers (one per LLM tier) ─────────────────────────
# Each breaker tracks failures independently. If Tier 1 trips OPEN,
# Tier 2 is unaffected and the cascade skips to it instantly.

_llm_breakers: dict[int, CircuitBreaker] = {
    1: CircuitBreaker(
        name="LLM_Tier1_GitHub_GPT4o",
        failure_threshold=3,
        recovery_timeout=60,
        expected_exceptions=(Exception,),
    ),
    2: CircuitBreaker(
        name="LLM_Tier2_GitHub_Llama",
        failure_threshold=3,
        recovery_timeout=60,
        expected_exceptions=(Exception,),
    ),
    3: CircuitBreaker(
        name="LLM_Tier3_GitHub_GPT4oMini",
        failure_threshold=3,
        recovery_timeout=90,
        expected_exceptions=(Exception,),
    ),
    4: CircuitBreaker(
        name="LLM_Tier4_Groq",
        failure_threshold=3,
        recovery_timeout=120,
        expected_exceptions=(Exception,),
    ),
    5: CircuitBreaker(
        name="LLM_Tier5_HuggingFace",
        failure_threshold=3,
        recovery_timeout=120,
        expected_exceptions=(Exception,),
    ),
}


# ─── Layer 6: Static Fallback Message ────────────────────────────
# This is the safety net. If all 5 LLM tiers fail (rate limits,
# network errors, circuit breakers all OPEN), this message is
# returned to the user. It NEVER fails because it's pure Python.

STATIC_FALLBACK_MESSAGE = (
    "I'm temporarily unable to process your request as all my AI providers "
    "are experiencing issues. Please try again in a few minutes. "
    "I apologize for the inconvenience!"
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


def make_call_model(tools_getter: Callable[[], list] = get_all_tools):
    """Factory: returns a call_model node wired to the given tools getter."""

    async def _call_model(state: AgentState):
        """
        Invoke the LLM using the 6-layer fallback cascade.

        For each tier (1 through 5):
          1. Check LLM budget → skip if exhausted
          2. Check circuit breaker state → skip instantly if OPEN
          3. Attempt invocation with retry_with_backoff (2 retries)
          4. On success → mark tier UP, return response
          5. On failure → mark tier DOWN, fall to next tier

        If all 5 tiers fail → return Layer 6 static message (never crashes).
        """
        messages = state["messages"]
        role = state.get("role", "GUEST")
        intent = state.get("intent", "tool_use")

        # ─── Role-Based Tool Filtering ───
        allowed_tools = []
        for t in tools_getter():
            if getattr(t, "requires_admin", False) and role != "ADMIN":
                continue
            allowed_tools.append(t)

        # For greetings and meta questions, skip tools entirely (faster + cheaper)
        if intent in ("greeting", "meta_question"):
            allowed_tools = []

        # Get all available providers with tools bound
        providers = get_bound_providers(allowed_tools)

        # ─── Cascade through tiers ───
        for provider in providers:
            tier = provider.tier
            breaker = _llm_breakers.get(tier)
            tier_label = f"llm_tier_{tier}"

            # 1. Check LLM budget
            if not check_llm_budget(tier_label):
                agent_logger.warn(
                    "LLM",
                    f"💰 Tier {tier} ({provider.provider_name}) budget exhausted — skipping",
                )
                continue

            # 2. Attempt invocation through circuit breaker + retry
            start = agent_logger.llm_start(provider.provider_name, provider.model_name)

            try:
                if breaker:
                    response = await breaker.call(
                        retry_with_backoff,
                        provider.llm.ainvoke,
                        messages,
                        max_retries=2,
                        base_delay=1.0,
                        retryable_exceptions=(TimeoutError, ConnectionError, Exception),
                        operation_name=f"LLM:Tier{tier}:{provider.model_name}",
                    )
                else:
                    # No breaker (shouldn't happen, but safe fallthrough)
                    response = await retry_with_backoff(
                        provider.llm.ainvoke,
                        messages,
                        max_retries=2,
                        base_delay=1.0,
                        retryable_exceptions=(TimeoutError, ConnectionError, Exception),
                        operation_name=f"LLM:Tier{tier}:{provider.model_name}",
                    )

                # ─── Success! ───
                tool_calls = getattr(response, "tool_calls", [])
                agent_logger.llm_success(start, len(tool_calls) > 0, len(tool_calls))
                system_health.mark_up(tier_label)

                agent_logger.info(
                    "LLM",
                    f"✅ Response from Tier {tier}: {provider.provider_name}/{provider.model_name}",
                )
                return {"messages": [response]}

            except CircuitOpenError:
                # Circuit is OPEN — skip instantly to next tier (no network delay)
                agent_logger.warn(
                    "LLM",
                    f"🔴 Tier {tier} ({provider.provider_name}) circuit OPEN — skipping",
                )
                system_health.mark_down(tier_label)
                continue

            except Exception as e:
                # Retries exhausted or hard error — fall to next tier
                agent_logger.llm_error(start, e)
                agent_logger.warn(
                    "LLM",
                    f"❌ Tier {tier} ({provider.provider_name}) failed — falling to next tier",
                    {"error": str(e)[:100]},
                )
                system_health.mark_down(tier_label)
                continue

        # ─── Layer 6: Static Fallback ───
        # All 5 tiers failed. Return a hardcoded message instead of crashing.
        agent_logger.error(
            "LLM",
            "🚨 ALL LLM tiers exhausted — returning static fallback response",
            None,
            {"tiers_attempted": len(providers)},
        )
        system_health.mark_down("all_llms")
        return {"messages": [AIMessage(content=STATIC_FALLBACK_MESSAGE)]}

    return _call_model


# Default call_model uses get_all_tools (backward-compatible)
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


# Default call_tools uses get_all_tools (backward-compatible)
call_tools = make_call_tools(get_all_tools)
