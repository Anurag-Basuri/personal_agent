"""
Conversation Summarizer — Phase 5: Memory & Summarization.

Summarizes long conversations to reduce context window usage
and extracts user preferences as persistent memory entries.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from app.core.logger import agent_logger


# ─── Constants ────────────────────────────────────────────────────

SUMMARIZATION_THRESHOLD = 15  # Trigger summarization after this many messages
MAX_CONTEXT_MESSAGES = 20     # Maximum messages to send to LLM (keep recent + summary)

_SUMMARIZE_PROMPT = """You are a conversation summarizer. Analyze the following conversation between a user and an AI agent. Produce two outputs in valid JSON:

1. "summary": A concise 2-4 sentence summary of the conversation covering the main topics discussed and any conclusions reached.
2. "preferences": A list of user preferences or facts extracted from the conversation. Each item should have:
   - "content": The preference/fact as a clear statement (e.g., "User prefers Python over Java")
   - "type": One of "preference", "fact", or "interest"
   - "confidence": A float from 0.0 to 1.0 indicating how confident you are

Only include preferences that are clearly stated or strongly implied. If no preferences are detected, return an empty list.

Respond with ONLY valid JSON, no markdown formatting:
{"summary": "...", "preferences": [{"content": "...", "type": "...", "confidence": 0.0}]}

CONVERSATION:
"""


def build_summarization_prompt(messages: list[BaseMessage]) -> str:
    """Build a prompt for summarizing a list of messages."""
    conversation_text = ""
    for msg in messages:
        if isinstance(msg, SystemMessage):
            continue  # Skip system prompts — not relevant for summarization
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        content = str(msg.content)[:500]  # Truncate very long messages
        conversation_text += f"{role}: {content}\n"

    return _SUMMARIZE_PROMPT + conversation_text


def parse_summarization_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM's summarization JSON response."""
    try:
        # Try to extract JSON from the response (handle markdown code blocks)
        text = response_text.strip()
        if text.startswith("```"):
            # Remove code fences
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        result = json.loads(text)
        return {
            "summary": result.get("summary", ""),
            "preferences": result.get("preferences", []),
        }
    except (json.JSONDecodeError, KeyError) as e:
        agent_logger.warn("MEMORY", f"Failed to parse summarization response: {e}")
        return {"summary": response_text[:500], "preferences": []}


def should_summarize(message_count: int) -> bool:
    """Check if the conversation has reached the summarization threshold."""
    return message_count >= SUMMARIZATION_THRESHOLD


def trim_messages_with_summary(
    messages: list[BaseMessage],
    summary: str,
    keep_recent: int = 8,
) -> list[BaseMessage]:
    """
    Replace old messages with a summary, keeping only the most recent ones.
    
    This reduces context window usage while preserving conversational continuity.
    """
    if not summary or len(messages) <= keep_recent:
        return messages

    summary_msg = SystemMessage(
        content=f"[CONVERSATION SUMMARY]\nPrevious conversation summary: {summary}\n[END SUMMARY]"
    )

    # Keep the most recent messages for immediate context
    recent_messages = messages[-keep_recent:]

    return [summary_msg] + recent_messages
