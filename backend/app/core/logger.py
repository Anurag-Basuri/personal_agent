"""
Structured agent logger.

Provides categorized, timestamped logging for the entire agent pipeline.
Categories: LLM, TOOL, MEMORY, CTRL, SYSTEM
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

# ─── Setup Python Logger ─────────────────────────────────────────

logger = logging.getLogger("agent")


class _StructuredFormatter(logging.Formatter):
    """Compact structured formatter: [timestamp] [LEVEL] [Agent:CATEGORY] message | meta"""

    def format(self, record: logging.LogRecord) -> str:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        category = getattr(record, "category", "SYSTEM")
        meta = getattr(record, "meta", None)
        meta_str = f" | {json.dumps(meta, default=str)}" if meta else ""
        return f"[{ts}] [{record.levelname}] [Agent:{category}] {record.getMessage()}{meta_str}"


def _setup_logger() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False


_setup_logger()


# ─── Public API ──────────────────────────────────────────────────

LogCategory = str  # One of: LLM, TOOL, MEMORY, CTRL, SYSTEM


def _log(level: int, category: LogCategory, message: str, meta: dict[str, Any] | None = None) -> None:
    logger.log(level, message, extra={"category": category, "meta": meta})


class AgentLogger:
    """Structured logger matching the original Node.js agentLogger interface."""

    # ─── Standard Levels ──────────────────────────────────────

    @staticmethod
    def info(category: LogCategory, message: str, meta: dict[str, Any] | None = None) -> None:
        _log(logging.INFO, category, message, meta)

    @staticmethod
    def warn(category: LogCategory, message: str, meta: dict[str, Any] | None = None) -> None:
        _log(logging.WARNING, category, message, meta)

    @staticmethod
    def error(
        category: LogCategory,
        message: str,
        error: Exception | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        err_meta = {
            **(meta or {}),
            "error_name": type(error).__name__ if error else "Unknown",
            "error_message": str(error) if error else "",
        }
        _log(logging.ERROR, category, message, err_meta)

    @staticmethod
    def debug(category: LogCategory, message: str, meta: dict[str, Any] | None = None) -> None:
        _log(logging.DEBUG, category, message, meta)

    # ─── Tool Execution ───────────────────────────────────────

    @staticmethod
    def tool_start(tool_name: str, args: dict[str, Any]) -> float:
        _log(logging.INFO, "TOOL", f"⚡ Executing: {tool_name}", {"args": args})
        return time.time()

    @staticmethod
    def tool_success(tool_name: str, start_time: float, output_preview: str = "") -> None:
        duration_ms = round((time.time() - start_time) * 1000)
        _log(
            logging.INFO,
            "TOOL",
            f"✅ {tool_name} completed",
            {
                "duration_ms": duration_ms,
                "output_length": len(output_preview),
                "preview": output_preview[:120],
            },
        )

    @staticmethod
    def tool_error(tool_name: str, start_time: float, error: Exception) -> None:
        duration_ms = round((time.time() - start_time) * 1000)
        _log(
            logging.ERROR,
            "TOOL",
            f"❌ {tool_name} FAILED",
            {
                "duration_ms": duration_ms,
                "error_name": type(error).__name__,
                "error_message": str(error),
            },
        )

    # ─── LLM Invocation ───────────────────────────────────────

    @staticmethod
    def llm_start(provider: str, model: str) -> float:
        _log(logging.INFO, "LLM", f"🧠 Invoking {provider} ({model})")
        return time.time()

    @staticmethod
    def llm_success(start_time: float, has_tool_calls: bool, tool_count: int) -> None:
        duration_ms = round((time.time() - start_time) * 1000)
        _log(
            logging.INFO,
            "LLM",
            "✅ LLM responded",
            {
                "duration_ms": duration_ms,
                "has_tool_calls": has_tool_calls,
                "tool_call_count": tool_count,
            },
        )

    @staticmethod
    def llm_error(start_time: float, error: Exception) -> None:
        duration_ms = round((time.time() - start_time) * 1000)
        _log(
            logging.ERROR,
            "LLM",
            "❌ LLM invocation FAILED",
            {
                "duration_ms": duration_ms,
                "error_name": type(error).__name__,
                "error_message": str(error),
                "is_rate_limit": "429" in str(error) or "Quota" in str(error),
            },
        )


agent_logger = AgentLogger()
