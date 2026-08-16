"""
SSE Streaming generator for LangGraph events.

Maps astream_events(version="v2") to frontend-friendly JSON chunks.
Event types emitted:
  status     : Phase changes (routing, thinking, executing, generating)
  token      : Individual text tokens from the LLM
  tool_start : A tool invocation has begun
  tool_end   : A tool invocation has completed
  done       : Stream finished successfully
  error      : An unrecoverable error occurred
"""

import json
import traceback
from typing import AsyncGenerator
from fastapi import Request
from app.core.logger import agent_logger

# LangGraph node names mapped to human-readable phase labels
_NODE_PHASE_MAP = {
    "router": "routing",
    "agent": "thinking",
    "tools": "executing",
}


def _sse(data: dict) -> str:
    """Format a dict as a single SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


async def stream_agent_response(
    request: Request | None,
    graph,
    initial_state: dict,
    final_state_ref: list,
) -> AsyncGenerator[str, None]:
    """
    Execute a LangGraph workflow and yield Server-Sent Events token-by-token.

    Captures the final graph state in final_state_ref for post-stream
    persistence (memory, summarization, etc.).
    """
    first_token_sent = False

    try:
        async for event in graph.astream_events(initial_state, version="v2"):
            if request and await request.is_disconnected():
                break

            kind = event["event"]
            name = event.get("name", "")

            # Capture final graph state (root level chain)
            if kind == "on_chain_end" and name == "LangGraph":
                final_state_ref.append(event["data"]["output"])

            # Phase status events from node lifecycle
            if kind == "on_chain_start" and name in _NODE_PHASE_MAP:
                yield _sse({"type": "status", "phase": _NODE_PHASE_MAP[name]})

            # Text token streaming from the LLM
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    content = chunk.content
                    if isinstance(content, list):
                        text_parts = [
                            c.get("text", "")
                            for c in content
                            if isinstance(c, dict) and "text" in c
                        ]
                        content = "".join(text_parts)

                    if content:
                        if not first_token_sent:
                            yield _sse({"type": "status", "phase": "generating"})
                            first_token_sent = True
                        yield _sse({"type": "token", "content": str(content)})

            # Tool execution starts
            elif kind == "on_tool_start":
                yield _sse({"type": "tool_start", "name": name})

            # Tool execution finishes
            elif kind == "on_tool_end":
                yield _sse({"type": "tool_end", "name": name})

        yield _sse({"type": "done"})

    except Exception as e:
        agent_logger.error("STREAM", "SSE stream failed", e)
        traceback.print_exc()
        yield _sse({"type": "error", "message": str(e)})
