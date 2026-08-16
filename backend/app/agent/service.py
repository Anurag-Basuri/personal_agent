"""
Admin agent service — the unrestricted admin agent handler.

Used exclusively by admin endpoints and Telegram transport.
Has access to ALL tools, MCP servers, and Google Workspace.

Retrieves granular history, builds context, passes state to LangGraph,
persists new messages, and triggers conversation summarization + memory extraction.

Uses MemoryRepository for all persistent memory operations.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from fastapi import Request

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.core.builder import agent_app
from app.agent.core.nodes import classify_intent
from app.agent.core.state import AgentState
from app.agent.prompts import get_admin_persona
from app.core.logger import agent_logger
from app.core.memory import get_message_history
from app.core.summarizer import (
    build_summarization_prompt,
    parse_summarization_response,
    should_summarize,
    trim_messages_with_summary,
)
from app.rag.context import get_base_portfolio_context
from app.repositories.memory_repo import memory_repo
from app.agent.core.stream import stream_agent_response


@dataclass
class AgentResponse:
    reply: str
    session_id: str


async def _load_user_memories(user_id: str | None) -> str:
    if not user_id:
        return ""

    memories = await memory_repo.get_user_memories(
        user_id=user_id,
        types=["preference", "fact", "interest"],
        min_confidence=0.6,
        limit=10,
    )

    if not memories:
        return ""

    memory_text = "[USER MEMORY]\nKnown facts and preferences about this user:\n"
    for m in memories:
        memory_text += f"- [{m.type}] {m.content}\n"
    memory_text += "[END USER MEMORY]\n"
    return memory_text


async def _load_session_summary(session_id: str, user_id: str | None) -> str:
    if not user_id:
        return ""

    summary = await memory_repo.get_session_summary(user_id, session_id)
    return summary or ""


async def _persist_memories(
    user_id: str | None,
    session_id: str,
    summary: str,
    preferences: list[dict],
) -> None:
    if not user_id:
        return

    if summary:
        await memory_repo.save_summary(user_id, session_id, summary)

    saved_count = await memory_repo.save_preferences(user_id, session_id, preferences)

    agent_logger.info("MEMORY", f"Persisted summary + {saved_count} preferences", {
        "session_id": session_id,
    })


async def _persist_and_summarize(
    final_state: dict,
    history: list,
    human_msg: HumanMessage,
    session_id: str,
    user_id: str | None,
    memory: any,
    request_start: float
):
    new_messages_offset = len(history) + 1
    final_messages = final_state["messages"]
    new_generated_messages = final_messages[new_messages_offset + 1:]
    
    messages_to_save = [human_msg, *new_generated_messages]
    await memory.add_messages(messages_to_save)

    total_message_count = len(history) + len(new_generated_messages) + 1
    if should_summarize(total_message_count) and user_id:
        agent_logger.info("MEMORY", f"Summarization threshold reached ({total_message_count} msgs)", {
            "session_id": session_id,
        })
        try:
            from app.agent.llm import thinker
            providers = thinker.get_providers()
            summarize_llm = providers[-1].llm if providers else None

            if summarize_llm:
                all_msgs = [m for m in final_messages if m.type != "system"]
                prompt_text = build_summarization_prompt(all_msgs)

                sum_response = await summarize_llm.ainvoke(prompt_text)
                parsed = parse_summarization_response(str(sum_response.content))

                await _persist_memories(
                    user_id=user_id,
                    session_id=session_id,
                    summary=parsed["summary"],
                    preferences=parsed["preferences"],
                )
        except Exception as e:
            agent_logger.warn("MEMORY", f"Summarization failed (non-fatal): {e}")

    total_duration = round((time.time() - request_start) * 1000)
    agent_logger.info("SYSTEM", "━━━ Request Complete ━━━", {
        "session_id": session_id,
        "total_duration_ms": total_duration,
        "new_messages_added": len(new_generated_messages) + 1,
        "intent": final_state.get("intent", "unknown"),
    })


async def prepare_agent_state(message: str, session_id: str, current_url: str | None, user_id: str | None, role: str):
    memory = get_message_history(session_id, user_id=user_id, role=role)
    history, user_memories, session_summary = await asyncio.gather(
        memory.get_messages(),
        _load_user_memories(user_id),
        _load_session_summary(session_id, user_id)
    )

    if session_summary and len(history) > 10:
        history = trim_messages_with_summary(history, session_summary, keep_recent=8)

    intent = classify_intent(message.lower())
    if intent in ("greeting", "meta_question", "conversational"):
        portfolio_context = "No portfolio context loaded for simple exchange."
    else:
        portfolio_context = await get_base_portfolio_context(query=message)
        
    location_context = ""
    if current_url:
        location_context = (
            f'\n[SCREEN CONTEXT]\nThe user is currently looking at the page: {current_url}. '
            f'If they use words like "this" or "here", they are referring to this page.\n[END SCREEN CONTEXT]'
        )

    system_prompt = SystemMessage(
        content=(
            f"{get_admin_persona()}\n\n"
            f"{user_memories}"
            f"[PORTFOLIO CONTEXT]\n{portfolio_context}\n[END CONTEXT]"
            f"{location_context}"
        )
    )
    human_msg = HumanMessage(content=message)

    initial_state: AgentState = {
        "messages": [system_prompt, *history, human_msg],
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "current_url": current_url,
        "intent": "tool_use",
        "summary": session_summary,
    }
    
    return initial_state, memory, history, human_msg


async def process_user_message_stream(
    message: str,
    session_id: str,
    request: Request | None = None,
    current_url: str | None = None,
    user_id: str | None = None,
):
    request_start = time.time()
    role = "ADMIN" if user_id else "GUEST"

    agent_logger.info("SYSTEM", "━━━ New Stream Request (LangGraph) ━━━", {
        "session_id": session_id,
        "role": role,
    })

    initial_state, memory, history, human_msg = await prepare_agent_state(
        message, session_id, current_url, user_id, role
    )

    final_state_ref = []
    
    async for chunk in stream_agent_response(request, agent_app, initial_state, final_state_ref):
        yield chunk

    if final_state_ref and final_state_ref[0]:
        await _persist_and_summarize(
            final_state_ref[0], history, human_msg, session_id, user_id, memory, request_start
        )


async def process_user_message(
    message: str,
    session_id: str,
    current_url: str | None = None,
    user_id: str | None = None,
) -> AgentResponse:
    """Non-streaming backward compatibility."""
    request_start = time.time()
    role = "ADMIN" if user_id else "GUEST"

    initial_state, memory, history, human_msg = await prepare_agent_state(
        message, session_id, current_url, user_id, role
    )

    final_state = await agent_app.ainvoke(initial_state)

    await _persist_and_summarize(
        final_state, history, human_msg, session_id, user_id, memory, request_start
    )

    final_messages = final_state["messages"]
    final_reply = ""
    for msg in reversed(final_messages):
        if msg.type == "ai" and msg.content and str(msg.content).strip():
            final_reply = msg.content
            break

    return AgentResponse(
        reply=str(final_reply) if final_reply else "I couldn't process that properly.",
        session_id=session_id,
    )
