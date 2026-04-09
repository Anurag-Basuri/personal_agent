"""
Agent service — the core agent handler.

Refactored to use LangGraph structure defined in `app/graph/builder.py`.
Retrieves granular history, builds context, passes state to LangGraph,
and persists new messages.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.logger import agent_logger
from app.core.memory import get_message_history
from app.core.prompts import SYSTEM_PERSONA
from app.rag.context import get_base_portfolio_context

from app.graph.builder import agent_app
from app.graph.state import AgentState

@dataclass
class AgentResponse:
    reply: str
    session_id: str


async def process_user_message(
    message: str,
    session_id: str,
    current_url: str | None = None,
    user_id: str | None = None,
) -> AgentResponse:
    """
    Process a user message through the LangGraph agent pipeline.

    1. Load granular history from memory
    2. Build system prompt with portfolio context
    3. Construct AgentState
    4. Invoke LangGraph (handles tools + llm loop)
    5. Persist only the newly generated messages and return reply
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

    human_msg = HumanMessage(content=message)
    
    # Initialize LangGraph State
    initial_state: AgentState = {
        "messages": [system_prompt, *history, human_msg],
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "current_url": current_url
    }

    approx_chars = sum(len(str(m.content)) for m in initial_state["messages"])
    agent_logger.debug("LLM", f"Estimated prompt size: {approx_chars} characters", {"session_id": session_id})

    # ─── Invoke LangGraph ───
    # LangGraph will run the model, check tools, run tools, run model again, etc.
    try:
        # We use ainvoke. LangGraph will return the final state.
        # Since it runs a cycle, the final messages array will have new AI msgs and Tool msgs.
        final_state = await agent_app.ainvoke(initial_state)
    except Exception as e:
        agent_logger.error("SYSTEM", "LangGraph Workflow Failed", e)
        raise e

    # ─── Persist New Messages ───
    # We only want to persist new messages (human_msg + whatever graph added)
    # The history list length + 1 (the new human msg) gets us the offset
    new_messages_offset = len(history) + 1 
    
    # Save the human message
    await memory.add_message(human_msg)
    
    # Save everything Graph generated (AI / Tool messages)
    final_messages = final_state["messages"]
    new_generated_messages = final_messages[new_messages_offset + 1:] # +1 because system prompt is at [0]
    
    for msg in new_generated_messages:
        await memory.add_message(msg)

    # The final displayable reply is the last AIMessage content
    final_reply = ""
    for msg in reversed(final_messages):
        if msg.type == "ai":
            final_reply = msg.content
            break

    total_duration = round((time.time() - request_start) * 1000)
    agent_logger.info("SYSTEM", "━━━ Request Complete ━━━", {
        "session_id": session_id,
        "total_duration_ms": total_duration,
        "new_messages_added": len(new_generated_messages) + 1,
    })

    return AgentResponse(
        reply=str(final_reply) if final_reply else "I couldn't process that properly.",
        session_id=session_id,
    )
