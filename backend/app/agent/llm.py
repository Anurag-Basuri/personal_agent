"""
6-Layer LLM Fallback Factory.

Initializes an ordered chain of LLM providers for the cascade:
  Tier 1: Google Gemini  — gemini-2.0-flash
  Tier 2: Cohere         — command-r-plus
  Tier 3: OpenRouter     — meta-llama/llama-3.3-70b-instruct:free
  Tier 4: Groq           — llama-3.1-8b-instant
  Tier 5: HuggingFace    — Qwen/Qwen2.5-72B-Instruct
  Tier 6: Static Python   (handled in nodes.py, not here)

Each provider is independently initialized — a failed Cohere init
doesn't affect Gemini. The nodes.py cascade loop iterates
through these providers in order, wrapped with per-tier circuit breakers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.config import get_settings
from app.core.logger import agent_logger


@dataclass
class LLMProvider:
    """Describes a single LLM in the fallback chain."""

    # 1 through 5
    tier: int
    # "Gemini", "Cohere", "OpenRouter", "Groq", "HuggingFace"
    provider_name: str
    # e.g., "gemini-2.0-flash"
    model_name: str
    # The LangChain LLM instance (unbound)
    llm: BaseChatModel


# Placeholder values that should be skipped
_PLACEHOLDER_VALUES = {
    "", "your_huggingface_api_key", "your_gemini_api_key_here",
    "your_huggingface_deployment_token", "your-api-key-here",
    "sk-xxx", "your_key_here", "your_github_pat_here",
    "your_groq_api_key_here", "your_cohere_api_key_here",
    "your_openrouter_api_key_here",
}


# Module state
_providers: list[LLMProvider] = []
_initialized: bool = False


def _is_valid_key(key: str | None) -> bool:
    """Check if an API key is actually set (not a placeholder or empty)."""
    if not key:
        return False
    return key.strip().lower() not in _PLACEHOLDER_VALUES


def _init_providers() -> None:
    """Initialize all available LLM providers in tier order."""
    global _providers, _initialized

    if _initialized:
        return
    _initialized = True

    settings = get_settings()

    # Tier 1: Google Gemini
    if _is_valid_key(settings.GEMINI_API_KEY):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
                max_output_tokens=1000,
            )
            _providers.append(LLMProvider(1, "Gemini", "gemini-2.0-flash", llm))
            agent_logger.info("LLM", "[OK] Tier 1 (Gemini gemini-2.0-flash) initialized")
        except Exception as e:
            agent_logger.error("LLM", "Failed to init Tier 1 (Gemini)", e)
    else:
        agent_logger.warn(
            "LLM", "⚠️ GEMINI_API_KEY not set — Tier 1 (Gemini) skipped",
        )

    # Tier 2: Cohere
    if _is_valid_key(settings.COHERE_API_KEY):
        try:
            from langchain_cohere import ChatCohere

            llm = ChatCohere(
                model="command-r-plus",
                cohere_api_key=settings.COHERE_API_KEY,
                temperature=0.3,
                max_tokens=1000,
            )
            _providers.append(LLMProvider(2, "Cohere", "command-r-plus", llm))
            agent_logger.info("LLM", "[OK] Tier 2 (Cohere command-r-plus) initialized")
        except Exception as e:
            agent_logger.error("LLM", "Failed to init Tier 2 (Cohere)", e)
    else:
        agent_logger.warn(
            "LLM", "⚠️ COHERE_API_KEY not set — Tier 2 (Cohere) skipped",
        )

    # Tier 3: OpenRouter (uses the OpenAI-compatible API)
    if _is_valid_key(settings.OPENROUTER_API_KEY):
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="meta-llama/llama-3.3-70b-instruct:free",
                api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.3,
                timeout=30,
                max_tokens=1000,
            )
            _providers.append(LLMProvider(3, "OpenRouter", "llama-3.3-70b:free", llm))
            agent_logger.info("LLM", "[OK] Tier 3 (OpenRouter llama-3.3-70b:free) initialized")
        except Exception as e:
            agent_logger.error("LLM", "Failed to init Tier 3 (OpenRouter)", e)
    else:
        agent_logger.warn(
            "LLM", "⚠️ OPENROUTER_API_KEY not set — Tier 3 (OpenRouter) skipped",
        )

    # Tier 4: Groq
    if _is_valid_key(settings.GROQ_API_KEY):
        try:
            from langchain_groq import ChatGroq

            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=settings.GROQ_API_KEY,
                temperature=0.3,
                max_tokens=1000,
            )
            _providers.append(LLMProvider(4, "Groq", "llama-3.1-8b-instant", llm))
            agent_logger.info("LLM", "[OK] Tier 4 (Groq llama-3.1-8b-instant) initialized")
        except Exception as e:
            agent_logger.error("LLM", "Failed to init Tier 4 (Groq)", e)
    else:
        agent_logger.warn(
            "LLM", "⚠️ GROQ_API_KEY not set — Tier 4 (Groq) skipped",
        )

    # Tier 5: HuggingFace
    if _is_valid_key(settings.HF_TOKEN):
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="Qwen/Qwen2.5-VL-72B-Instruct",
                api_key=settings.HF_TOKEN,
                base_url="https://router.huggingface.co/v1",
                temperature=0.3,
                timeout=30,
                max_tokens=1000,
            )
            _providers.append(LLMProvider(5, "HuggingFace", "Qwen2.5-VL-72B-Instruct", llm))
            agent_logger.info("LLM", "[OK] Tier 5 (HuggingFace Qwen2.5-VL-72B) initialized")
        except Exception as e:
            agent_logger.error("LLM", "Failed to init Tier 5 (HuggingFace)", e)
    else:
        agent_logger.warn(
            "LLM", "⚠️ HF_TOKEN not set — Tier 5 (HuggingFace) skipped",
        )

    if not _providers:
        agent_logger.error(
            "SYSTEM", "FATAL: No AI providers configured", None,
            {"hint": "Set GEMINI_API_KEY, COHERE_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, or HF_TOKEN in .env"},
        )


# Public API
def get_providers() -> list[LLMProvider]:
    """
    Return the ordered list of available LLM providers.

    Each provider's `.llm` is the raw (unbound) model.
    Call `.llm.bind_tools(tools)` before invocation if tools are needed.
    """
    _init_providers()
    return list(_providers)


def get_bound_providers(tools: list[BaseTool]) -> list[LLMProvider]:
    """
    Return providers with tools pre-bound to their LLMs.

    Creates new LLMProvider instances with bound LLMs — does not
    mutate the originals, so this is safe to call repeatedly.
    """
    _init_providers()

    if not _providers:
        raise RuntimeError(
            "No AI providers configured. Set GEMINI_API_KEY, COHERE_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, or HF_TOKEN in .env."
        )

    bound: list[LLMProvider] = []
    for p in _providers:
        if tools:
            bound_llm = p.llm.bind_tools(tools)
        else:
            bound_llm = p.llm
        bound.append(LLMProvider(
            tier=p.tier,
            provider_name=p.provider_name,
            model_name=p.model_name,
            llm=bound_llm,
        ))
    return bound


def get_provider_info() -> list[dict[str, Any]]:
    """Return a serializable summary of configured providers for health endpoints."""
    _init_providers()
    return [
        {
            "tier": p.tier,
            "provider": p.provider_name,
            "model": p.model_name,
        }
        for p in _providers
    ]


def init_llms_eagerly() -> None:
    """Call during startup to populate logs with the LLM cascade status."""
    _init_providers()
