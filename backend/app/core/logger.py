"""
Structured agent logger.

Provides categorized, timestamped logging for the entire agent pipeline.
Categories: LLM, TOOL, MEMORY, CTRL, SYSTEM, MCP, STARTUP
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any


logger = logging.getLogger("agent")


# ANSI color codes
class _Colors:
    """ANSI escape sequences for terminal coloring."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"

    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_MAGENTA = "\033[95m"


_LEVEL_STYLES = {
    "DEBUG": f"{_Colors.DIM}DBG{_Colors.RESET}",
    "INFO": f"{_Colors.BRIGHT_GREEN}INF{_Colors.RESET}",
    "WARNING": f"{_Colors.BRIGHT_YELLOW}WRN{_Colors.RESET}",
    "ERROR": f"{_Colors.BRIGHT_RED}ERR{_Colors.RESET}",
    "CRITICAL": f"{_Colors.BG_RED}{_Colors.WHITE}CRT{_Colors.RESET}",
}

_CATEGORY_STYLES = {
    "LLM": f"{_Colors.MAGENTA}LLM{_Colors.RESET}",
    "MCP": f"{_Colors.CYAN}MCP{_Colors.RESET}",
    "TOOL": f"{_Colors.BLUE}TOOL{_Colors.RESET}",
    "MEMORY": f"{_Colors.GREEN}MEM{_Colors.RESET}",
    "CTRL": f"{_Colors.YELLOW}CTRL{_Colors.RESET}",
    "SYSTEM": f"{_Colors.WHITE}SYS{_Colors.RESET}",
    "STARTUP": f"{_Colors.BRIGHT_CYAN}BOOT{_Colors.RESET}",
    "CLEANUP": f"{_Colors.DIM}CLN{_Colors.RESET}",
    "RAG": f"{_Colors.GREEN}RAG{_Colors.RESET}",
    "AUTH": f"{_Colors.YELLOW}AUTH{_Colors.RESET}",
    "API": f"{_Colors.BLUE}API{_Colors.RESET}",
}


class _StructuredFormatter(logging.Formatter):
    """Compact structured formatter with ANSI colors and aligned columns."""

    def format(self, record: logging.LogRecord) -> str:
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))
        ts_dim = f"{_Colors.DIM}{ts}{_Colors.RESET}"

        level = _LEVEL_STYLES.get(record.levelname, record.levelname)

        category = getattr(record, "category", "SYSTEM")
        cat_styled = _CATEGORY_STYLES.get(category, f"{_Colors.DIM}{category}{_Colors.RESET}")

        meta = getattr(record, "meta", None)
        meta_str = ""
        if meta:
            meta_str = f" {_Colors.DIM}{json.dumps(meta, default=str)}{_Colors.RESET}"

        return f" {ts_dim} {level} [{cat_styled}] {record.getMessage()}{meta_str}"


def _setup_logger() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False


_setup_logger()


# One of: LLM, TOOL, MEMORY, CTRL, SYSTEM, MCP, STARTUP, CLEANUP, RAG, AUTH, API
LogCategory = str


def _log(level: int, category: LogCategory, message: str, meta: dict[str, Any] | None = None) -> None:
    logger.log(level, message, extra={"category": category, "meta": meta})


class AgentLogger:
    """Structured logger with categorized, colored output."""

    # Standard Levels
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

    # Tool Execution
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
            f"✅ {tool_name} completed ({duration_ms}ms)",
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
            f"❌ {tool_name} FAILED ({duration_ms}ms)",
            {
                "duration_ms": duration_ms,
                "error_name": type(error).__name__,
                "error_message": str(error),
            },
        )

    # LLM Invocation
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

    # Startup helpers
    @staticmethod
    def section(title: str) -> None:
        """Print a visual section divider during startup."""
        C = _Colors
        line = f"\n {C.DIM}{'─' * 52}{C.RESET}"
        header = f" {C.BOLD}{C.BRIGHT_CYAN}▸ {title}{C.RESET}"
        print(line)
        print(header)

    @staticmethod
    def status_line(label: str, value: str, ok: bool = True) -> None:
        """Print a key/value status line with color indicator."""
        C = _Colors
        dot = f"{C.BRIGHT_GREEN}●{C.RESET}" if ok else f"{C.BRIGHT_RED}●{C.RESET}"
        print(f"   {dot} {C.DIM}{label:<20}{C.RESET} {value}")

    @staticmethod
    def banner() -> None:
        """Print a compact startup banner."""
        C = _Colors
        print()
        print(f"  {C.BOLD}{C.BRIGHT_CYAN}╔══════════════════════════════════════════════════╗{C.RESET}")
        print(f"  {C.BOLD}{C.BRIGHT_CYAN}║{C.RESET}   {C.BOLD}🤖 Personal Agent API{C.RESET}                            {C.BOLD}{C.BRIGHT_CYAN}║{C.RESET}")
        print(f"  {C.BOLD}{C.BRIGHT_CYAN}║{C.RESET}   {C.DIM}AI powered assistant with tool calling & RAG{C.RESET}     {C.BOLD}{C.BRIGHT_CYAN}║{C.RESET}")
        print(f"  {C.BOLD}{C.BRIGHT_CYAN}╚══════════════════════════════════════════════════╝{C.RESET}")
        print()


agent_logger = AgentLogger()
