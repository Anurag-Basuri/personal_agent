"""
Agent service — the core agent loop.

Port of agent.service.ts: system prompt + history + tool-calling loop
with sticky fallback, timeout, and structured logging.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.core.llm_factory import get_bound_llms, llm_info
from app.core.logger import agent_logger
from app.core.memory import get_message_history
from app.core.prompts import SYSTEM_PERSONA
from app.rag.context import get_base_portfolio_context
from app.tools import agent_tools

LLM_TIMEOUT_SECONDS = 20
MAX_LOOPS = 3


@dataclass
class AgentResponse:
    reply: str
    session_id: str


async def _invoke_with_timeout(llm, messages: list, label: str, timeout: float = LLM_TIMEOUT_SECONDS):
    """Race an LLM call against a timeout."""
    try:
        return await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"{label} timed out after {timeout}s")


async def process_user_message(
    message: str,
    session_id: str,
    current_url: str | None = None,
    user_id: str | None = None,
) -> AgentResponse:
    """
    Process a user message through the agent pipeline.

    1. Load history from memory
    2. Build system prompt with portfolio context
    3. Call LLM with tool-calling loop (max 3 iterations)
    4. Sticky fallback: if primary fails, skip it for rest of request
    5. Persist messages and return reply
    """
    request_start = time.time()

    agent_logger.info("SYSTEM", "━━━ New Request ━━━", {
        "session_id": session_id,
        "llm_mode": llm_info.mode,
        "primary": llm_info.primary_provider or "NONE",
        "fallback": llm_info.fallback_provider or "NONE",
        "current_url": current_url or "N/A",
        "message_preview": message[:80],
    })

    llms = get_bound_llms(agent_tools)
    primary = llms["primary"]
    fallback = llms["fallback"]

    # Load session history
    memory = get_message_history(session_id, user_id=user_id)
    history = await memory.get_messages()
    agent_logger.debug("MEMORY", f"Loaded {len(history)} messages from session history", {
        "session_id": session_id,
    })

    # Build context
    portfolio_context = await get_base_portfolio_context()
    location_context = ""
    if current_url:
        location_context = (
            f'\n[SCREEN CONTEXT]\nThe user is currently looking at the page: {current_url}. '
            f'If they use words like "this" or "here", they are referring to this page.\n[END SCREEN CONTEXT]'
        )

    system_prompt = SystemMessage(
        content=f"{SYSTEM_PERSONA}\n\n[PORTFOLIO CONTEXT]\n{portfolio_context}\n[END CONTEXT]{location_context}"
    )

    turn_messages = [system_prompt, *history, HumanMessage(content=message)]

    approx_chars = sum(len(str(m.content)) for m in turn_messages)
    agent_logger.debug("LLM", f"Estimated prompt size: {approx_chars} characters", {"session_id": session_id})

    call_count = 0
    primary_failed = False  # Sticky fallback flag

    while call_count < MAX_LOOPS:
        ai_msg = None
        used_provider = ""

        # ─── LLM Invocation with Sticky Fallback ────────────────
        active_primary = primary if (primary and not primary_failed) else None

        if active_primary:
            start = agent_logger.llm_start(llm_info.primary_provider, llm_info.primary_model)
            try:
                ai_msg = await _invoke_with_timeout(active_primary, turn_messages, llm_info.primary_provider)
                tool_calls = getattr(ai_msg, "tool_calls", []) or []
                agent_logger.llm_success(start, len(tool_calls) > 0, len(tool_calls))
                used_provider = llm_info.primary_provider
            except Exception as primary_error:
                agent_logger.llm_error(start, primary_error)
                primary_failed = True
                agent_logger.warn("LLM", f"🔒 Primary ({llm_info.primary_provider}) disabled for this request")

                # Try fallback
                if fallback:
                    agent_logger.info("LLM", f"🔄 Switching to fallback ({llm_info.fallback_provider})")
                    fb_start = agent_logger.llm_start(llm_info.fallback_provider, llm_info.fallback_model)
                    try:
                        ai_msg = await _invoke_with_timeout(fallback, turn_messages, llm_info.fallback_provider)
                        tool_calls = getattr(ai_msg, "tool_calls", []) or []
                        agent_logger.llm_success(fb_start, len(tool_calls) > 0, len(tool_calls))
                        used_provider = llm_info.fallback_provider
                    except Exception as fallback_error:
                        agent_logger.llm_error(fb_start, fallback_error)
                        agent_logger.error("LLM", "💀 Both primary AND fallback LLMs failed", fallback_error, {
                            "primary_error": str(primary_error)[:100],
                        })
                        raise fallback_error
                else:
                    raise primary_error

        elif fallback:
            if primary_failed:
                agent_logger.debug("LLM", f"⏩ Skipping {llm_info.primary_provider} — using {llm_info.fallback_provider}")
            start = agent_logger.llm_start(llm_info.fallback_provider, llm_info.fallback_model)
            try:
                ai_msg = await _invoke_with_timeout(fallback, turn_messages, llm_info.fallback_provider)
                tool_calls = getattr(ai_msg, "tool_calls", []) or []
                agent_logger.llm_success(start, len(tool_calls) > 0, len(tool_calls))
                used_provider = llm_info.fallback_provider
            except Exception as err:
                agent_logger.llm_error(start, err)
                raise
        else:
            raise RuntimeError("No LLM providers available")

        # ─── Process Response ───────────────────────────────────
        turn_messages.append(ai_msg)
        await memory.add_message(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", []) or []

        if tool_calls:
            agent_logger.info("TOOL", f"Agent ({used_provider}) requested {len(tool_calls)} tool(s)", {
                "tools": [tc["name"] for tc in tool_calls],
                "loop": call_count + 1,
            })

            # Build a name → tool lookup
            tool_map = {t.name: t for t in agent_tools}

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                tool_id = tc.get("id", "")

                selected = tool_map.get(tool_name)
                if not selected:
                    agent_logger.warn("TOOL", f'Tool "{tool_name}" not found in registry', {
                        "available": list(tool_map.keys()),
                    })
                    tool_msg = ToolMessage(
                        tool_call_id=tool_id,
                        content=f"Tool {tool_name} not found.",
                        name=tool_name,
                    )
                    turn_messages.append(tool_msg)
                    await memory.add_message(tool_msg)
                    continue

                t_start = agent_logger.tool_start(tool_name, tool_args)
                try:
                    tool_output = await selected.ainvoke(tool_args)
                    output_str = str(tool_output)
                    agent_logger.tool_success(tool_name, t_start, output_str)

                    tool_msg = ToolMessage(
                        tool_call_id=tool_id,
                        content=output_str,
                        name=tool_name,
                    )
                    turn_messages.append(tool_msg)
                    await memory.add_message(tool_msg)
                except Exception as e:
                    agent_logger.tool_error(tool_name, t_start, e)
                    error_msg = ToolMessage(
                        tool_call_id=tool_id,
                        content=f"Failed to execute tool: {e}",
                        name=tool_name,
                    )
                    turn_messages.append(error_msg)
                    await memory.add_message(error_msg)

            call_count += 1
        else:
            # ─── Final Reply ─────────────────────────────────────
            total_duration = round((time.time() - request_start) * 1000)
            agent_logger.info("SYSTEM", "━━━ Request Complete ━━━", {
                "session_id": session_id,
                "used_provider": used_provider,
                "primary_skipped": primary_failed,
                "total_duration_ms": total_duration,
                "llm_loops": call_count + 1,
                "reply_preview": str(ai_msg.content)[:100],
            })

            # Persist the human message
            await memory.add_message(HumanMessage(content=message))

            return AgentResponse(
                reply=str(ai_msg.content),
                session_id=session_id,
            )

    # Max loops reached
    total_duration = round((time.time() - request_start) * 1000)
    agent_logger.warn("SYSTEM", f"Agent hit MAX_LOOPS ({MAX_LOOPS}) — forced stop", {
        "session_id": session_id,
        "total_duration_ms": total_duration,
    })

    return AgentResponse(
        reply="I had to think too long about that. Could you try asking in a different way?",
        session_id=session_id,
    )
