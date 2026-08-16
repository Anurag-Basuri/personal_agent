"""
Agent service for normal logged-in users.

Uses the same PUBLIC_PORTFOLIO_PERSONA as the public chatbot, but with:
  - Persistent memory (preferences, facts, summaries)
  - Summarization at message thresholds
  - 50-message-per-session cap
  - One continuous session per user account

Key differences from admin service (service.py):
  - Restricted to portfolio-safe tools only (no MCP, no admin tools)
  - Same persona as public chatbot (speaks as Anurag, portfolio-scoped)
  - Message cap enforcement
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from fastapi import Request

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.core.builder import build_public_agent
from app.agent.core.nodes import classify_intent
from app.agent.core.state import AgentState
from app.agent.prompts import get_public_persona
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

USER_SESSION_MESSAGE_CAP = 50


@dataclass
class UserAgentResponse:
    """Return type for the user agent service."""
    reply: str
    session_id: str
    messages_remaining: int


class UserSessionCounter:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def get_count(self, session_id: str) -> int:
        return self._counts.get(session_id, 0)

    def increment(self, session_id: str) -> int:
        self._counts[session_id] = self._counts.get(session_id, 0) + 1
        return self._counts[session_id]

    def reset(self, session_id: str) -> None:
        self._counts.pop(session_id, None)

    def get_remaining(self, session_id: str) -> int:
        return max(0, USER_SESSION_MESSAGE_CAP - self.get_count(session_id))


_user_message_counter = UserSessionCounter()

def get_user_message_counter() -> UserSessionCounter:
    return _user_message_counter


async def _load_user_memories(user_id: str) -> str:
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


async def _load_session_summary(session_id: str, user_id: str) -> str:
    summary = await memory_repo.get_session_summary(user_id, session_id)
    return summary or ""


async def _persist_memories(user_id: str, session_id: str, summary: str, preferences: list[dict]) -> None:
    if summary:
        await memory_repo.save_summary(user_id, session_id, summary)
    saved_count = await memory_repo.save_preferences(user_id, session_id, preferences)
    agent_logger.info("MEMORY", f"Persisted summary + {saved_count} preferences", {"session_id": session_id})


async def prepare_user_agent_state(message: str, session_id: str, user_id: str, current_url: str | None):
    memory = get_message_history(session_id, user_id=user_id, role="GUEST")
    history = await memory.get_messages()

    user_memories = await _load_user_memories(user_id)
    session_summary = await _load_session_summary(session_id, user_id)

    if session_summary and len(history) > 10:
        history = trim_messages_with_summary(history, session_summary, keep_recent=8)

    intent = classify_intent(message)
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
            f"{get_public_persona()}\n\n"
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
        "role": "GUEST",
        "current_url": current_url,
        "intent": intent,
        "summary": session_summary,
    }
    return initial_state, memory, history, human_msg


async def _persist_and_summarize(final_state, history, human_msg, session_id, user_id, memory, request_start):
    new_messages_offset = len(history) + 1
    final_messages = final_state["messages"]
    new_generated_messages = final_messages[new_messages_offset + 1:]

    messages_to_save = [human_msg, *new_generated_messages]
    await memory.add_messages(messages_to_save)

    counter = get_user_message_counter()
    counter.increment(session_id)
    remaining = counter.get_remaining(session_id)

    total_message_count = len(history) + len(new_generated_messages) + 1
    if should_summarize(total_message_count):
        agent_logger.info("MEMORY", f"Summarization threshold reached ({total_message_count} msgs)", {"session_id": session_id})
        try:
            from app.agent.llm import thinker
            providers = thinker.get_providers()
            summarize_llm = providers[-1].llm if providers else None
            if summarize_llm:
                all_msgs = [m for m in final_messages if m.type != "system"]
                prompt_text = build_summarization_prompt(all_msgs)
                sum_response = await summarize_llm.ainvoke(prompt_text)
                parsed = parse_summarization_response(str(sum_response.content))
                await _persist_memories(user_id, session_id, parsed["summary"], parsed["preferences"])
        except Exception as e:
            agent_logger.warn("MEMORY", f"Summarization failed (non-fatal): {e}")

    total_duration = round((time.time() - request_start) * 1000)
    agent_logger.info("AGENT", "User request complete", {
        "session_id": session_id[:20] + "...",
        "total_duration_ms": total_duration,
        "messages_remaining": remaining,
    })


async def process_user_agent_message_stream(
    message: str, session_id: str, user_id: str, request: Request | None = None, current_url: str | None = None
):
    request_start = time.time()
    counter = get_user_message_counter()
    if counter.get_count(session_id) >= USER_SESSION_MESSAGE_CAP:
        import json
        yield f"data: {json.dumps({'type': 'error', 'message': 'Session message limit reached.'})}\n\n"
        return

    initial_state, memory, history, human_msg = await prepare_user_agent_state(message, session_id, user_id, current_url)
    
    public_agent = build_public_agent()
    final_state_ref = []
    
    async for chunk in stream_agent_response(request, public_agent, initial_state, final_state_ref):
        yield chunk

    if final_state_ref and final_state_ref[0]:
        await _persist_and_summarize(final_state_ref[0], history, human_msg, session_id, user_id, memory, request_start)


async def process_user_agent_message(
    message: str, session_id: str, user_id: str, current_url: str | None = None
) -> UserAgentResponse:
    request_start = time.time()
    counter = get_user_message_counter()
    if counter.get_count(session_id) >= USER_SESSION_MESSAGE_CAP:
        return UserAgentResponse(
            reply="You've reached the message limit for this session. Please reset your conversation to continue chatting!",
            session_id=session_id,
            messages_remaining=0,
        )

    initial_state, memory, history, human_msg = await prepare_user_agent_state(message, session_id, user_id, current_url)
    public_agent = build_public_agent()
    final_state = await public_agent.ainvoke(initial_state)

    await _persist_and_summarize(final_state, history, human_msg, session_id, user_id, memory, request_start)

    final_reply = ""
    for msg in reversed(final_state["messages"]):
        if msg.type == "ai" and msg.content and str(msg.content).strip():
            final_reply = msg.content
            break

    return UserAgentResponse(
        reply=str(final_reply) if final_reply else "I couldn't process that properly.",
        session_id=session_id,
        messages_remaining=counter.get_remaining(session_id),
    )
