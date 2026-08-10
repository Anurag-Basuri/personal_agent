"""
Centralized LLM Orchestrator.

Owns the entire lifecycle of LLM provider management:
  - Provider initialization (Gemini, Cohere, OpenRouter, Groq, HuggingFace)
  - Per-tier circuit breakers with fast tripping
  - Smart error classification (permanent vs rate_limited vs transient)
  - Cascade invocation with hard per-tier timeouts
  - Health status reporting

The cascade order:
  Tier 1: Google Gemini  (gemini-2.0-flash)
  Tier 2: Cohere         (command-r-plus-08-2024)
  Tier 3: OpenRouter     (openrouter/auto)
  Tier 4: Groq           (llama-3.1-8b-instant)
  Tier 5: HuggingFace    (Qwen/Qwen2.5-VL-72B-Instruct)
  Tier 6: Static Python  (handled externally in nodes.py)
"""

from __future__ import annotations

import copy

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.config import get_settings
from app.core.degradation import system_health
from app.core.logger import agent_logger
from app.core.rate_limiter import check_llm_budget


@dataclass
class LLMProvider:
    """Describes a single LLM in the fallback chain."""

    tier: int
    provider_name: str
    model_name: str
    llm: BaseChatModel
    disabled: bool = False


@dataclass
class _TierBreaker:
    """Lightweight per-tier circuit breaker embedded in the orchestrator."""

    name: str
    failure_threshold: int = 2
    recovery_timeout: int = 30
    _state: str = field(default="CLOSED", init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)

    @property
    def state(self) -> str:
        """Current state with automatic OPEN to HALF_OPEN transition."""
        if self._state == "OPEN":
            if (time.time() - self._last_failure_time) >= self.recovery_timeout:
                self._state = "HALF_OPEN"
        return self._state

    @property
    def is_available(self) -> bool:
        """Whether this tier can accept a call."""
        return self.state != "OPEN"

    def record_success(self) -> None:
        """Reset on success."""
        self._state = "CLOSED"
        self._failure_count = 0

    def record_failure(self) -> None:
        """Record failure and trip OPEN if threshold reached."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"

    def trip_open(self) -> None:
        """Force-trip the breaker (for permanent errors)."""
        self._state = "OPEN"
        self._failure_count = self.failure_threshold
        self._last_failure_time = time.time()


# Placeholder API key values to skip during init
_PLACEHOLDER_VALUES = {
    "", "your_huggingface_api_key", "your_gemini_api_key_here",
    "your_huggingface_deployment_token", "your-api-key-here",
    "sk-xxx", "your_key_here", "your_github_pat_here",
    "your_groq_api_key_here", "your_cohere_api_key_here",
    "your_openrouter_api_key_here",
}


def _is_valid_key(key: str | None) -> bool:
    """Check if an API key is set and not a placeholder."""
    if not key:
        return False
    return key.strip().lower() not in _PLACEHOLDER_VALUES


def _classify_error(error: Exception) -> str:
    """
    Classify an LLM error to decide retry strategy.

    Returns:
        "permanent"    : Model removed, invalid key, 404, tool schema. Never retry.
        "rate_limited"  : 429 / quota exhausted. Skip tier instantly.
        "transient"     : Timeout, 503, network. Worth one retry.
    """
    error_str = str(error).lower()

    # Permanent errors: never retry, disable the tier
    permanent_signals = [
        "404", "not found", "removed", "deprecated",
        "unauthorized", "invalid api key", "forbidden",
        "invalid_api_key", "401", "403",
    ]
    if any(sig in error_str for sig in permanent_signals):
        return "permanent"

    # Tool schema incompatibility: provider can't parse tool call history
    # These will never succeed on retry, so treat as permanent for this request
    tool_schema_signals = [
        "tool call id", "tool_call_id",
        "not found in previous tool calls",
        "missing field `function`", "missing field 'function'",
        "not one of the allowed values ['function']",
        "not one of the allowed values [\"function\"]",
        "invalid tool message",
    ]
    if any(sig in error_str for sig in tool_schema_signals):
        return "permanent"

    # Rate limit: skip immediately, don't waste time retrying
    rate_limit_signals = [
        "429", "rate limit", "resource_exhausted",
        "quota", "too many requests", "rate_limit",
    ]
    if any(sig in error_str for sig in rate_limit_signals):
        return "rate_limited"

    return "transient"


class LLMOrchestrator:
    """
    Central brain for the LLM cascade.

    Manages provider init, per-tier breakers, error classification,
    and the full fallback loop with hard timeouts.
    """

    # Hard timeout for a single LLM attempt (seconds)
    PER_ATTEMPT_TIMEOUT: float = 30.0
    # Max retries for transient errors only
    MAX_TRANSIENT_RETRIES: int = 1
    # Delay before transient retry
    TRANSIENT_RETRY_DELAY: float = 0.5

    def __init__(self) -> None:
        self._providers: list[LLMProvider] = []
        self._breakers: dict[int, _TierBreaker] = {}
        self._initialized: bool = False

    def _init_providers(self) -> None:
        """Initialize all available LLM providers in tier order."""
        if self._initialized:
            return
        self._initialized = True

        settings = get_settings()

        tier_configs = [
            (1, "GROQ_API_KEY", "Groq", self._init_groq),
            (2, "OPENROUTER_API_KEY", "OpenRouter", self._init_openrouter),
            (3, "COHERE_API_KEY", "Cohere", self._init_cohere),
            (4, "MISTRAL_API_KEY", "Mistral", self._init_mistral),
            (5, "HF_TOKEN", "HuggingFace", self._init_huggingface),
        ]

        for tier, key_attr, name, init_fn in tier_configs:
            key_value = getattr(settings, key_attr, "")
            if _is_valid_key(key_value):
                try:
                    provider = init_fn(tier, key_value)
                    self._providers.append(provider)
                    self._breakers[tier] = _TierBreaker(
                        name=f"LLM_Tier{tier}_{name}",
                        failure_threshold=2,
                        recovery_timeout=30 if tier <= 3 else 60,
                    )
                    agent_logger.info("LLM", f"[OK] Tier {tier} ({name}/{provider.model_name}) initialized")
                except Exception as e:
                    agent_logger.error("LLM", f"Failed to init Tier {tier} ({name})", e)
            else:
                agent_logger.warn("LLM", f"[SKIP] {key_attr} not set -- Tier {tier} ({name}) skipped")

        if not self._providers:
            agent_logger.error(
                "SYSTEM", "FATAL: No AI providers configured", None,
                {"hint": "Set GEMINI_API_KEY, COHERE_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, or HF_TOKEN in .env"},
            )

    @staticmethod
    def _init_mistral(tier: int, api_key: str) -> LLMProvider:
        """Initialize Mistral AI provider."""
        from langchain_mistralai import ChatMistralAI
        llm = ChatMistralAI(
            model="mistral-large-latest",
            api_key=api_key,
            temperature=0.3,
            max_tokens=1000,
        )
        return LLMProvider(tier, "Mistral", "mistral-large-latest", llm)

    @staticmethod
    def _init_cohere(tier: int, api_key: str) -> LLMProvider:
        """Initialize Cohere provider."""
        from langchain_cohere import ChatCohere
        llm = ChatCohere(
            model="command-r-plus-08-2024",
            cohere_api_key=api_key,
            temperature=0.3,
            max_tokens=1000,
        )
        return LLMProvider(tier, "Cohere", "command-r-plus-08-2024", llm)

    @staticmethod
    def _init_openrouter(tier: int, api_key: str) -> LLMProvider:
        """Initialize OpenRouter provider (OpenAI-compatible)."""
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="openrouter/auto",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.3,
            timeout=30,
            max_tokens=1000,
        )
        return LLMProvider(tier, "OpenRouter", "auto", llm)

    @staticmethod
    def _init_groq(tier: int, api_key: str) -> LLMProvider:
        """Initialize Groq provider."""
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.3,
            max_tokens=1000,
        )
        return LLMProvider(tier, "Groq", "llama-3.1-8b-instant", llm)

    @staticmethod
    def _init_huggingface(tier: int, api_key: str) -> LLMProvider:
        """Initialize HuggingFace provider (OpenAI-compatible)."""
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="Qwen/Qwen2.5-VL-72B-Instruct",
            api_key=api_key,
            base_url="https://router.huggingface.co/v1",
            temperature=0.3,
            timeout=10,
            max_tokens=1000,
        )
        return LLMProvider(tier, "HuggingFace", "Qwen2.5-VL-72B-Instruct", llm)

    async def invoke(
        self,
        messages: list[BaseMessage],
        tools: list[BaseTool] | None = None,
    ) -> BaseMessage | None:
        """
        Run the full LLM cascade with smart error handling.

        For each tier:
          1. Skip if provider is permanently disabled
          2. Skip if circuit breaker is OPEN
          3. Skip if LLM budget is exhausted
          4. Skip if tool history is present and provider is schema-incompatible
          5. Attempt invocation with a hard per-attempt timeout
          6. On permanent error -> disable tier, skip instantly
          7. On rate limit -> skip to next tier instantly (no retry)
          8. On transient error -> retry once, then skip

        Returns None if all tiers exhausted (caller handles static fallback).
        """
        self._init_providers()

        # Check if messages contain tool call history
        # Langchain outputs OpenAI-formatted tool history which crashes some native APIs
        has_tool_history = False
        for m in messages:
            if isinstance(m, ToolMessage):
                has_tool_history = True
                break
            if isinstance(m, AIMessage):
                if getattr(m, "tool_calls", []) or m.additional_kwargs.get("tool_calls"):
                    has_tool_history = True
                    break

        incompatible_tool_providers = {"Cohere", "Groq", "HuggingFace"}

        for provider in self._providers:
            tier = provider.tier
            breaker = self._breakers.get(tier)
            tier_label = f"llm_tier_{tier}"

            # Skip permanently disabled providers
            if provider.disabled:
                continue

            # Skip if circuit breaker is OPEN
            if breaker and not breaker.is_available:
                agent_logger.debug(
                    "LLM",
                    f"[SKIP] Tier {tier} ({provider.provider_name}) circuit OPEN",
                )
                continue

            # Skip if budget exhausted
            if not check_llm_budget(tier_label):
                agent_logger.warn(
                    "LLM",
                    f"[SKIP] Tier {tier} ({provider.provider_name}) budget exhausted",
                )
                continue

            # Skip incompatible providers if we have tool history
            if has_tool_history and provider.provider_name in incompatible_tool_providers:
                agent_logger.debug(
                    "LLM",
                    f"[SKIP] Tier {tier} ({provider.provider_name}) incompatible with tool history",
                )
                continue

            # Bind tools if needed
            llm = provider.llm.bind_tools(tools) if tools else provider.llm

            # Attempt invocation (with optional transient retry)
            result = await self._attempt_tier(
                provider, llm, messages, breaker, tier_label,
            )
            if result is not None:
                return result

        # All tiers exhausted
        return None

    async def _attempt_tier(
        self,
        provider: LLMProvider,
        llm: Any,
        messages: list[BaseMessage],
        breaker: _TierBreaker | None,
        tier_label: str,
    ) -> BaseMessage | None:
        """
        Attempt a single tier with smart error handling.

        Returns the LLM response on success, None on failure (caller continues cascade).
        """
        tier = provider.tier
        max_attempts = self.MAX_TRANSIENT_RETRIES + 1

        for attempt in range(max_attempts):
            start = agent_logger.llm_start(provider.provider_name, provider.model_name)
            try:
                response = await asyncio.wait_for(
                    llm.ainvoke(messages),
                    timeout=self.PER_ATTEMPT_TIMEOUT,
                )

                # Success
                tool_calls = getattr(response, "tool_calls", [])
                agent_logger.llm_success(start, len(tool_calls) > 0, len(tool_calls))
                agent_logger.info(
                    "LLM",
                    f"[OK] Tier {tier}: {provider.provider_name}/{provider.model_name}",
                )

                if breaker:
                    breaker.record_success()
                system_health.mark_up(tier_label)
                return response

            except asyncio.TimeoutError:
                agent_logger.llm_error(start, TimeoutError(f"Tier {tier} timed out after {self.PER_ATTEMPT_TIMEOUT}s"))
                error_class = "transient"

            except Exception as e:
                agent_logger.llm_error(start, e)
                error_class = _classify_error(e)

                # PERMANENT: Disable the tier entirely until restart
                if error_class == "permanent":
                    agent_logger.warn(
                        "LLM",
                        f"[DEAD] Tier {tier} ({provider.provider_name}) permanently failed -- disabling",
                        {"error": str(e)[:120]},
                    )
                    provider.disabled = True
                    if breaker:
                        breaker.trip_open()
                    system_health.mark_down(tier_label)
                    return None

                # RATE LIMITED: Skip immediately (no retry)
                if error_class == "rate_limited":
                    agent_logger.warn(
                        "LLM",
                        f"[RATE] Tier {tier} ({provider.provider_name}) rate limited -- skipping",
                        {"error": str(e)[:80]},
                    )
                    if breaker:
                        breaker.record_failure()
                    system_health.mark_down(tier_label)
                    return None

            # TRANSIENT: Retry once
            if attempt < max_attempts - 1:
                agent_logger.debug(
                    "LLM",
                    f"[RETRY] Tier {tier} ({provider.provider_name}) transient failure -- retrying in {self.TRANSIENT_RETRY_DELAY}s",
                )
                await asyncio.sleep(self.TRANSIENT_RETRY_DELAY)
            else:
                agent_logger.warn(
                    "LLM",
                    f"[FAIL] Tier {tier} ({provider.provider_name}) exhausted after {max_attempts} attempts",
                )
                if breaker:
                    breaker.record_failure()
                system_health.mark_down(tier_label)

        return None

    def get_providers(self) -> list[LLMProvider]:
        """Return the initialized provider list."""
        self._init_providers()
        return list(self._providers)

    def get_bound_providers(self, tools: list[BaseTool]) -> list[LLMProvider]:
        """Return providers with tools pre-bound (for backward compat)."""
        self._init_providers()
        if not self._providers:
            raise RuntimeError(
                "No AI providers configured. Set GEMINI_API_KEY, COHERE_API_KEY, "
                "OPENROUTER_API_KEY, GROQ_API_KEY, or HF_TOKEN in .env."
            )
        bound: list[LLMProvider] = []
        for p in self._providers:
            if p.disabled:
                continue
            bound_llm = p.llm.bind_tools(tools) if tools else p.llm
            bound.append(LLMProvider(
                tier=p.tier,
                provider_name=p.provider_name,
                model_name=p.model_name,
                llm=bound_llm,
            ))
        return bound

    def get_provider_info(self) -> list[dict[str, Any]]:
        """Return a serializable summary for health endpoints."""
        self._init_providers()
        return [
            {
                "tier": p.tier,
                "provider": p.provider_name,
                "model": p.model_name,
                "disabled": p.disabled,
                "breaker_state": self._breakers[p.tier].state if p.tier in self._breakers else "N/A",
            }
            for p in self._providers
        ]

    def init_eagerly(self) -> None:
        """Call during startup to populate logs with the LLM cascade status."""
        self._init_providers()


# Module-level singleton
orchestrator = LLMOrchestrator()


# Backward-compatible public API (used by nodes.py and other modules)
def get_providers() -> list[LLMProvider]:
    """Return the ordered list of available LLM providers."""
    return orchestrator.get_providers()


def get_bound_providers(tools: list[BaseTool]) -> list[LLMProvider]:
    """Return providers with tools pre-bound to their LLMs."""
    return orchestrator.get_bound_providers(tools)


def get_provider_info() -> list[dict[str, Any]]:
    """Return a serializable summary of configured providers for health endpoints."""
    return orchestrator.get_provider_info()


def init_llms_eagerly() -> None:
    """Call during startup to populate logs with the LLM cascade status."""
    orchestrator.init_eagerly()
