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

import time
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.core.builder import build_public_agent
from app.agent.core.state import AgentState
from app.agent.prompts import PUBLIC_PORTFOLIO_PERSONA
from app.core.logger import agent_logger
from app.core.memory import get_message_history
from app.rag.context import get_base_portfolio_context


# Constants
PUBLIC_SESSION_MESSAGE_CAP = 20


# Response Dataclass
@dataclass
class PublicChatResponse:
    """Return type for the public chat service."""

    reply: str
    session_id: str
    messages_remaining: int


# Message Counter
class SessionMessageCounter:
    """In memory counter for messages per public session.

    Tracks how many user messages have been sent per session_id.
    Thread-safe via simple dict (single-process async server).
    Stale entries are cleaned up by the session cleanup job.
    """

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def get_count(self, session_id: str) -> int:
        """Get current message count for a session."""
        return self._counts.get(session_id, 0)

    def increment(self, session_id: str) -> int:
        """Increment and return the new count."""
        self._counts[session_id] = self._counts.get(session_id, 0) + 1
        return self._counts[session_id]

    def remove(self, session_id: str) -> None:
        """Remove a session's counter (called during cleanup)."""
        self._counts.pop(session_id, None)

    def get_remaining(self, session_id: str) -> int:
        """Return how many messages the session has left."""
        return max(0, PUBLIC_SESSION_MESSAGE_CAP - self.get_count(session_id))


# Singleton
_message_counter = SessionMessageCounter()


def get_message_counter() -> SessionMessageCounter:
    """Accessor for the session message counter singleton."""
    return _message_counter


# Service Function
async def process_public_message(
    message: str,
    session_id: str,
    current_url: str | None = None,
) -> PublicChatResponse:
    """
    Process a message from the public portfolio chatbot.

    1. Check message cap (20 per session)
    2. Load session history from memory
    3. Build system prompt with portfolio RAG context
    4. Invoke LangGraph with restricted tools
    5. Persist messages for the session's lifetime
    6. Return reply with remaining message count

    Args:
        message: The visitor's message text.
        session_id: Ephemeral session ID from browser sessionStorage.
        current_url: The portfolio page the visitor is currently on.

    Returns:
        PublicChatResponse with the agent's reply and remaining messages.

    Raises:
        ValueError: If the session has exceeded its message cap.
    """
    request_start = time.time()

    # Message Cap Check
    counter = get_message_counter()
    current_count = counter.get_count(session_id)

    if current_count >= PUBLIC_SESSION_MESSAGE_CAP:
        raise ValueError(
            f"Session message limit reached ({PUBLIC_SESSION_MESSAGE_CAP}). "
            "Please start a new session."
        )

    agent_logger.info("PUBLIC", "━━━ Public Chat Request ━━━", {
        "session_id": session_id[:16] + "...",
        "message_number": current_count + 1,
        "remaining": PUBLIC_SESSION_MESSAGE_CAP - current_count - 1,
        "current_url": current_url or "N/A",
        "message_preview": message[:80],
    })

    # Load Session History
    memory = get_message_history(session_id, user_id=None, role="GUEST")
    history = await memory.get_messages()

    # Build System Prompt
    portfolio_context = await get_base_portfolio_context(query=message)

    location_context = ""
    if current_url:
        location_context = (
            f'\n[SCREEN CONTEXT]\nThe visitor is currently on: {current_url}. '
            f'If they use words like "this" or "here", they refer to this page.\n[END SCREEN CONTEXT]'
        )

    system_prompt = SystemMessage(
        content=(
            f"{PUBLIC_PORTFOLIO_PERSONA}\n\n"
            f"[PORTFOLIO CONTEXT]\n{portfolio_context}\n[END CONTEXT]"
            f"{location_context}"
        )
    )

    human_msg = HumanMessage(content=message)

    # Initialize LangGraph State
    initial_state: AgentState = {
        "messages": [system_prompt, *history, human_msg],
        "session_id": session_id,
        "user_id": None,
        "role": "GUEST",
        "current_url": current_url,
        # Default router will override
        "intent": "tool_use",
        "summary": "",
    }

    # Invoke LangGraph (Public Agent)
    public_agent = build_public_agent()

    try:
        final_state = await public_agent.ainvoke(initial_state)
    except Exception as e:
        agent_logger.error("PUBLIC", "Public LangGraph Workflow Failed", e)
        raise

    # Persist Messages
    await memory.add_message(human_msg)

    new_messages_offset = len(history) + 1
    final_messages = final_state["messages"]
    new_generated_messages = final_messages[new_messages_offset + 1:]

    for msg in new_generated_messages:
        await memory.add_message(msg)

    # Extract Final Reply (skip tool-calling intermediates with empty content)
    final_reply = ""
    for msg in reversed(final_messages):
        if msg.type == "ai" and msg.content and str(msg.content).strip():
            final_reply = msg.content
            break

    # Increment Counter
    counter.increment(session_id)
    remaining = counter.get_remaining(session_id)

    total_duration = round((time.time() - request_start) * 1000)
    agent_logger.info("PUBLIC", "━━━ Public Request Complete ━━━", {
        "session_id": session_id[:16] + "...",
        "total_duration_ms": total_duration,
        "messages_remaining": remaining,
    })

    return PublicChatResponse(
        reply=str(final_reply) if final_reply else "I couldn't process that properly.",
        session_id=session_id,
        messages_remaining=remaining,
    )
