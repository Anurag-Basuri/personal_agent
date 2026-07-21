"""
Agent service — the core agent handler.

Refactored to use LangGraph structure defined in `app/agent/core/builder.py`.
Retrieves granular history, builds context, passes state to LangGraph,
persists new messages, and triggers conversation summarization + memory extraction.

Uses MemoryRepository for all persistent memory operations.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.core.builder import agent_app
from app.agent.core.state import AgentState
from app.agent.prompts import SYSTEM_PERSONA
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


@dataclass
class AgentResponse:
    reply: str
    session_id: str


async def _load_user_memories(user_id: str | None) -> str:
    """Load persistent memories (preferences, facts) for the user from AgentMemory."""
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
    """Load the most recent conversation summary for this session."""
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
    """Save extracted summary and preferences to AgentMemory."""
    if not user_id:
        return

    if summary:
        await memory_repo.save_summary(user_id, session_id, summary)

    saved_count = await memory_repo.save_preferences(user_id, session_id, preferences)

    agent_logger.info("MEMORY", f"Persisted summary + {saved_count} preferences", {
        "session_id": session_id,
    })


async def process_user_message(
    message: str,
    session_id: str,
    current_url: str | None = None,
    user_id: str | None = None,
) -> AgentResponse:
    """
    Process a user message through the LangGraph agent pipeline.

    1. Load granular history from memory
    2. Load persistent user memories and session summary
    3. Build system prompt with portfolio context + memories
    4. Construct AgentState with intent field
    5. Invoke LangGraph (router → agent → tools loop)
    6. Persist only the newly generated messages
    7. Trigger summarization if message threshold is reached
    """
    request_start = time.time()

    # We define a default role; ideally this should be passed down from the route (get_current_user)
    # For now, if we have a user_id, they are at least authenticated.
    role = "ADMIN" if user_id else "GUEST"

    agent_logger.info("SYSTEM", "━━━ New Request (LangGraph) ━━━", {
        "session_id": session_id,
        "role": role,
        "current_url": current_url or "N/A",
        "message_preview": message[:80],
    })

    # Load session history
    memory = get_message_history(session_id, user_id=user_id, role=role)
    history = await memory.get_messages()

    agent_logger.debug("MEMORY", f"Loaded {len(history)} messages from session history", {
        "session_id": session_id,
    })

    # Load persistent memories and session summary
    user_memories = await _load_user_memories(user_id)
    session_summary = await _load_session_summary(session_id, user_id)

    # If we have a summary and history is long, trim old messages
    if session_summary and len(history) > 10:
        history = trim_messages_with_summary(history, session_summary, keep_recent=8)

    # Build context by searching the Vector Database with the user's prompt
    portfolio_context = await get_base_portfolio_context(query=message)
    location_context = ""
    if current_url:
        location_context = (
            f'\n[SCREEN CONTEXT]\nThe user is currently looking at the page: {current_url}. '
            f'If they use words like "this" or "here", they are referring to this page.\n[END SCREEN CONTEXT]'
        )

    system_prompt = SystemMessage(
        content=(
            f"{SYSTEM_PERSONA}\n\n"
            f"{user_memories}"
            f"[PORTFOLIO CONTEXT]\n{portfolio_context}\n[END CONTEXT]"
            f"{location_context}"
        )
    )

    human_msg = HumanMessage(content=message)

    # Initialize LangGraph State
    initial_state: AgentState = {
        "messages": [system_prompt, *history, human_msg],
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "current_url": current_url,
        "intent": "tool_use",  # Default — router will override
        "summary": session_summary,
    }

    approx_chars = sum(len(str(m.content)) for m in initial_state["messages"])
    agent_logger.debug("LLM", f"Estimated prompt size: {approx_chars} characters", {"session_id": session_id})

    # ─── Invoke LangGraph ───
    try:
        final_state = await agent_app.ainvoke(initial_state)
    except Exception as e:
        agent_logger.error("SYSTEM", "LangGraph Workflow Failed", e)
        raise e

    # ─── Persist New Messages ───
    new_messages_offset = len(history) + 1

    # Save the human message
    await memory.add_message(human_msg)

    # Save everything Graph generated (AI / Tool messages)
    final_messages = final_state["messages"]
    new_generated_messages = final_messages[new_messages_offset + 1:]  # +1 because system prompt is at [0]

    for msg in new_generated_messages:
        await memory.add_message(msg)

    # The final displayable reply is the last AIMessage content
    final_reply = ""
    for msg in reversed(final_messages):
        if msg.type == "ai":
            final_reply = msg.content
            break

    # ─── Trigger Summarization (Background) ───
    total_message_count = len(history) + len(new_generated_messages) + 1
    if should_summarize(total_message_count) and user_id:
        agent_logger.info("MEMORY", f"Summarization threshold reached ({total_message_count} msgs)", {
            "session_id": session_id,
        })
        try:
            # Use the cheapest available LLM (last tier) for summarization
            from app.agent.llm import get_providers
            providers = get_providers()
            summarize_llm = providers[-1].llm if providers else None

            if summarize_llm:
                # Build summarization prompt from all messages (excluding system)
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

    return AgentResponse(
        reply=str(final_reply) if final_reply else "I couldn't process that properly.",
        session_id=session_id,
    )
