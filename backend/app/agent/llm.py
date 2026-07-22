"""
6-Layer LLM Fallback Factory.

Initializes an ordered chain of LLM providers for the cascade:
  Tier 1: GitHub Models — openai/gpt-4o
  Tier 2: GitHub Models — meta/llama-3.3-70b-instruct
  Tier 3: GitHub Models — openai/gpt-4o-mini
  Tier 4: Groq          — llama-3.1-8b-instant
  Tier 5: HuggingFace   — Qwen/Qwen2.5-72B-Instruct
  Tier 6: Static Python  (handled in nodes.py, not here)

Each provider is independently initialized — a failed Groq init
doesn't affect GitHub Models. The nodes.py cascade loop iterates
through these providers in order, wrapped with per-tier circuit breakers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.config import get_settings
from app.core.logger import agent_logger


# ─── Provider Dataclass ──────────────────────────────────────────

@dataclass
class LLMProvider:
    """Describes a single LLM in the fallback chain."""

    tier: int               # 1 through 5
    provider_name: str      # "GitHub", "Groq", "HuggingFace"
    model_name: str         # e.g., "openai/gpt-4o"
    llm: BaseChatModel      # The LangChain LLM instance (unbound)


# ─── Placeholder values that should be skipped ───────────────────

_PLACEHOLDER_VALUES = {
    "", "your_huggingface_api_key", "your_gemini_api_key_here",
    "your_huggingface_deployment_token", "your-api-key-here",
    "sk-xxx", "your_key_here", "your_github_pat_here",
    "your_groq_api_key_here",
}


# ─── Module state ────────────────────────────────────────────────

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

    # ─── Tier 1, 2, 3: GitHub Models ─────────────────────────────
    if _is_valid_key(settings.GITHUB_TOKEN):
        from langchain_openai import ChatOpenAI

        github_models = [
            (1, "gpt-4o"),
            (2, "Meta-Llama-3.1-405B-Instruct"),
            (3, "gpt-4o-mini"),
        ]

        for tier, model_id in github_models:
            try:
                llm = ChatOpenAI(
                    model=model_id,
                    api_key=settings.GITHUB_TOKEN,
                    base_url="https://models.inference.ai.azure.com",
                    temperature=0.3,
                    timeout=30,
                    max_tokens=1000,
                )
                _providers.append(LLMProvider(tier, "GitHub", model_id, llm))
                agent_logger.info("LLM", f"✅ Tier {tier} configured", {
                    "provider": "GitHub Models", "model": model_id,
                })
            except Exception as e:
                agent_logger.error(
                    "LLM", f"Failed to init Tier {tier} ({model_id})", e,
                )
    else:
        agent_logger.warn(
            "LLM", "⚠️ GITHUB_TOKEN not set — Tiers 1-3 (GitHub Models) skipped",
        )

    # ─── Tier 4: Groq ────────────────────────────────────────────
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
            agent_logger.info("LLM", "✅ Tier 4 configured", {
                "provider": "Groq", "model": "llama-3.1-8b-instant",
            })
        except Exception as e:
            agent_logger.error("LLM", "Failed to init Tier 4 (Groq)", e)
    else:
        agent_logger.warn(
            "LLM", "⚠️ GROQ_API_KEY not set — Tier 4 (Groq) skipped",
        )

    # ─── Tier 5: HuggingFace ─────────────────────────────────────
    if _is_valid_key(settings.HF_TOKEN):
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="Qwen/Qwen2.5-72B-Instruct",
                api_key=settings.HF_TOKEN,
                base_url="https://router.huggingface.co/v1",
                temperature=0.3,
                timeout=30,
                max_tokens=1000,
            )
            _providers.append(LLMProvider(5, "HuggingFace", "Qwen2.5-72B-Instruct", llm))
            agent_logger.info("LLM", "✅ Tier 5 configured", {
                "provider": "HuggingFace", "model": "Qwen2.5-72B-Instruct",
            })
        except Exception as e:
            agent_logger.error("LLM", "Failed to init Tier 5 (HuggingFace)", e)
    else:
        agent_logger.warn(
            "LLM", "⚠️ HF_TOKEN not set — Tier 5 (HuggingFace) skipped",
        )

    # ─── Summary ─────────────────────────────────────────────────
    if _providers:
        tier_summary = ", ".join(
            f"T{p.tier}:{p.provider_name}/{p.model_name}" for p in _providers
        )
        agent_logger.info(
            "LLM", f"🚀 {len(_providers)}-layer cascade ready: {tier_summary}",
        )
    else:
        agent_logger.error(
            "SYSTEM", "FATAL: No AI providers configured", None,
            {"hint": "Set GITHUB_TOKEN, GROQ_API_KEY, or HF_TOKEN in .env"},
        )


# ─── Public API ──────────────────────────────────────────────────

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
            "No AI providers configured. Set GITHUB_TOKEN, GROQ_API_KEY, or HF_TOKEN in .env."
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
