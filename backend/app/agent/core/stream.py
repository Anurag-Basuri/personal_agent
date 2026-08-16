"""
SSE Streaming generator for LangGraph events.
Maps astream_events(version="v2") to frontend-friendly JSON chunks.
"""

import json
import traceback
from typing import AsyncGenerator
from fastapi import Request
from app.core.logger import agent_logger

async def stream_agent_response(request: Request | None, graph, initial_state: dict, final_state_ref: list) -> AsyncGenerator[str, None]:
    """
    Executes a LangGraph workflow and yields Server-Sent Events (SSE) token-by-token.
    Captures the final graph state in final_state_ref[0].
    """
    try:
        async for event in graph.astream_events(initial_state, version="v2"):
            # Stop generating if the client disconnects
            if request and await request.is_disconnected():
                break

            kind = event["event"]
            name = event.get("name", "")
            
            # Capture final graph state (root level chain)
            if kind == "on_chain_end" and name == "LangGraph":
                final_state_ref.append(event["data"]["output"])

            # 1. Text token streaming from the LLM
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    content = chunk.content
                    # Sometimes content is a list of dicts for multimodal/complex responses
                    if isinstance(content, list):
                        text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
                        content = "".join(text_parts)
                    
                    if content:
                        yield f"data: {json.dumps({'type': 'token', 'content': str(content)})}\n\n"

            # 2. Tool execution starts
            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'name': name})}\n\n"

            # 3. Tool execution finishes
            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end', 'name': name})}\n\n"

        # Final done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        agent_logger.error("STREAM", "SSE stream failed", e)
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
