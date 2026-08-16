"""
Public portfolio chatbot service.

A lightweight agent handler for the public-facing portfolio chatbot.
Uses the restricted PUBLIC_PORTFOLIO_PERSONA prompt and only the
portfolio-safe toolset (no admin, email, calendar, or MCP tools).

Key differences from the authenticated agent service:
  - No user authentication or user_id tracking
  - No persistent memory or preference extraction
  - No summarization (sessions are ephemeral)
  - Hardcoded role = "GUEST"
  - Strict 20-message-per-session cap
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
from app.rag.context import get_base_portfolio_context
from app.agent.core.stream import stream_agent_response

PUBLIC_SESSION_MESSAGE_CAP = 20


@dataclass
class PublicChatResponse:
    reply: str
    session_id: str
    messages_remaining: int


class SessionMessageCounter:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def get_count(self, session_id: str) -> int:
        return self._counts.get(session_id, 0)

    def increment(self, session_id: str) -> int:
        self._counts[session_id] = self._counts.get(session_id, 0) + 1
        return self._counts[session_id]

    def remove(self, session_id: str) -> None:
        self._counts.pop(session_id, None)

    def get_remaining(self, session_id: str) -> int:
        return max(0, PUBLIC_SESSION_MESSAGE_CAP - self.get_count(session_id))


_message_counter = SessionMessageCounter()

def get_message_counter() -> SessionMessageCounter:
    return _message_counter


async def prepare_public_state(message: str, session_id: str, current_url: str | None):
    memory = get_message_history(session_id, user_id=None, role="GUEST")
    history = await memory.get_messages()

    intent = classify_intent(message.lower())
    if intent in ("greeting", "meta_question"):
        portfolio_context = "No portfolio context loaded for simple greeting."
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
            f"[PORTFOLIO CONTEXT]\n{portfolio_context}\n[END CONTEXT]"
            f"{location_context}"
        )
    )

    human_msg = HumanMessage(content=message)

    initial_state: AgentState = {
        "messages": [system_prompt, *history, human_msg],
        "session_id": session_id,
        "user_id": None,
        "role": "GUEST",
        "current_url": current_url,
        "intent": intent,
        "summary": "",
    }
    
    return initial_state, memory, history, human_msg


async def _persist_public_messages(final_state, history, human_msg, session_id, memory, request_start):
    new_messages_offset = len(history) + 1
    final_messages = final_state["messages"]
    new_generated_messages = final_messages[new_messages_offset + 1:]

    messages_to_save = [human_msg, *new_generated_messages]
    await memory.add_messages(messages_to_save)

    counter = get_message_counter()
    counter.increment(session_id)
    remaining = counter.get_remaining(session_id)

    total_duration = round((time.time() - request_start) * 1000)
    agent_logger.info("PUBLIC", "Public Chat Request Complete", {
        "session_id": session_id[:16] + "...",
        "total_duration_ms": total_duration,
        "messages_remaining": remaining,
    })


async def process_public_message_stream(
    message: str, session_id: str, request: Request | None = None, current_url: str | None = None
):
    request_start = time.time()
    counter = get_message_counter()
    if counter.get_count(session_id) >= PUBLIC_SESSION_MESSAGE_CAP:
        import json
        yield f"data: {json.dumps({'type': 'error', 'message': 'Session message limit reached.'})}\n\n"
        return

    agent_logger.info("PUBLIC", "━━━ Public Stream Request ━━━", {
        "session_id": session_id[:16] + "...",
        "message_number": counter.get_count(session_id) + 1,
    })

    initial_state, memory, history, human_msg = await prepare_public_state(message, session_id, current_url)
    
    public_agent = build_public_agent()
    final_state_ref = []
    
    async for chunk in stream_agent_response(request, public_agent, initial_state, final_state_ref):
        yield chunk

    if final_state_ref and final_state_ref[0]:
        await _persist_public_messages(final_state_ref[0], history, human_msg, session_id, memory, request_start)


async def process_public_message(
    message: str, session_id: str, current_url: str | None = None
) -> PublicChatResponse:
    request_start = time.time()
    counter = get_message_counter()
    
    if counter.get_count(session_id) >= PUBLIC_SESSION_MESSAGE_CAP:
        raise ValueError(f"Session message limit reached ({PUBLIC_SESSION_MESSAGE_CAP}). Please start a new session.")

    initial_state, memory, history, human_msg = await prepare_public_state(message, session_id, current_url)
    public_agent = build_public_agent()
    final_state = await public_agent.ainvoke(initial_state)

    await _persist_public_messages(final_state, history, human_msg, session_id, memory, request_start)

    final_reply = ""
    for msg in reversed(final_state["messages"]):
        if msg.type == "ai" and msg.content and str(msg.content).strip():
            final_reply = msg.content
            break

    return PublicChatResponse(
        reply=str(final_reply) if final_reply else "I couldn't process that properly.",
        session_id=session_id,
        messages_remaining=counter.get_remaining(session_id),
    )
