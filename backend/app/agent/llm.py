"""
Dual-LLM factory: HuggingFace Qwen2.5 (primary) + Gemini (fallback).

Same pattern as the Node.js llm.factory.ts — singleton init, tool binding,
and sticky fallback logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import BaseTool

from app.config import get_settings
from app.core.logger import agent_logger

# Placeholder values that should be skipped
_PLACEHOLDER_VALUES = {
    "", "your_huggingface_api_key", "your_gemini_api_key_here",
    "your_huggingface_deployment_token", "your-api-key-here",
    "sk-xxx", "your_key_here",
}


@dataclass
class LLMInfo:
    primary_provider: str = ""
    primary_model: str = ""
    fallback_provider: str = ""
    fallback_model: str = ""
    mode: str = "NONE"  # dual | primary-only | fallback-only | NONE


_primary_llm = None
_fallback_llm = None
_initialized: bool = False
llm_info = LLMInfo()


def _is_valid_key(key: str | None) -> bool:
    """Check if an API key is actually set (not a placeholder or empty)."""
    if not key:
        return False
    return key.strip().lower() not in _PLACEHOLDER_VALUES


def _init_llms() -> None:
    global _primary_llm, _fallback_llm, _initialized

    if _initialized:
        return
    _initialized = True

    settings = get_settings()

    # 1. Primary — HuggingFace (OpenAI-compatible endpoint)
    if _is_valid_key(settings.HF_TOKEN):
        try:
            from langchain_openai import ChatOpenAI
            _primary_llm = ChatOpenAI(
                model="Qwen/Qwen2.5-72B-Instruct",
                api_key=settings.HF_TOKEN,
                base_url="https://router.huggingface.co/v1",
                temperature=0.3,
                timeout=30,
                max_tokens=1000,
            )
            llm_info.primary_provider = "HuggingFace"
            llm_info.primary_model = "Qwen2.5-72B-Instruct"
            agent_logger.info("LLM", "🟢 Primary LLM configured", {
                "provider": "HuggingFace", "model": "Qwen2.5-72B-Instruct"
            })
        except Exception as e:
            agent_logger.error("LLM", "Failed to initialize HuggingFace LLM", e)
    else:
        agent_logger.warn("LLM", "⚠️ HF_TOKEN not set or is placeholder — HuggingFace primary skipped")

    # 2. Fallback — Gemini
    if _is_valid_key(settings.GEMINI_API_KEY):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _fallback_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
                max_output_tokens=1000,
            )
            llm_info.fallback_provider = "Gemini"
            llm_info.fallback_model = "gemini-2.5-flash"
            agent_logger.info("LLM", "🟡 Fallback LLM configured", {
                "provider": "Google Gemini", "model": "gemini-2.5-flash"
            })
        except Exception as e:
            agent_logger.error("LLM", "Failed to initialize Gemini LLM", e)
    else:
        agent_logger.warn("LLM", "⚠️ GEMINI_API_KEY not set or is placeholder — Gemini fallback skipped")

    # Determine mode
    if _primary_llm and _fallback_llm:
        llm_info.mode = "dual"
        agent_logger.info("LLM", "🚀 Dual-LLM ready: HuggingFace (primary) → Gemini (fallback)")
    elif _primary_llm:
        llm_info.mode = "primary-only"
        agent_logger.info("LLM", "🚀 Single-LLM ready: HuggingFace (no fallback)")
    elif _fallback_llm:
        llm_info.mode = "fallback-only"
        agent_logger.warn("LLM", "⚠️ Running on Gemini only (no primary HuggingFace)")
    else:
        llm_info.mode = "NONE"
        agent_logger.error("SYSTEM", "FATAL: No AI Providers configured", None, {
            "hint": "Set valid HF_TOKEN or GEMINI_API_KEY in .env"
        })


def get_bound_llms(tools: list[BaseTool]) -> dict[str, Any]:
    """
    Returns the primary + fallback LLMs with tools bound.

    Returns:
        {"primary": bound_llm | None, "fallback": bound_llm | None, "info": LLMInfo}
    """
    _init_llms()

    if llm_info.mode == "NONE":
        raise RuntimeError("No AI Providers configured. Please set HF_TOKEN or GEMINI_API_KEY.")

    return {
        "primary": _primary_llm.bind_tools(tools) if _primary_llm else None,
        "fallback": _fallback_llm.bind_tools(tools) if _fallback_llm else None,
        "info": llm_info,
    }


def init_llms_eagerly() -> None:
    """Call during startup to get accurate LLM mode in logs."""
    _init_llms()
