"""
Centralized LLM Orchestrator (Dual-Brain Architecture).

Owns the entire lifecycle of LLM provider management.
Features:
  1. Round-robin API key rotation (Gemini)
  2. Per-tier circuit breakers with fast tripping
  3. Smart error classification
  4. Dual-Brain setup:
     ThinkerOrchestrator: Fast cheap models (Groq, Gemini Flash-Lite, Mistral) for routing and greetings.
     ReasonerOrchestrator: Deep reasoning models (Gemini Flash, Cohere, Mistral) for tools.
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

class RoundRobinKeyManager:
    """Manages a pool of API keys for round-robin rotation upon 429 errors."""
    
    def __init__(self, key_string: str | None):
        self._keys = [k.strip() for k in (key_string or "").split(",") if k.strip()]
        self._current_index = 0

    @property
    def has_keys(self) -> bool:
        return len(self._keys) > 0

    def get_current_key(self) -> str:
        if not self.has_keys:
            return ""
        return self._keys[self._current_index]

    def rotate(self) -> str:
        """Rotate to the next key and return it."""
        if self.has_keys:
            self._current_index = (self._current_index + 1) % len(self._keys)
        return self.get_current_key()

    @property
    def total_keys(self) -> int:
        return len(self._keys)

@dataclass
class LLMProvider:
    """Describes a single LLM in the fallback chain."""

    tier: int
    provider_name: str
    model_name: str
    llm: BaseChatModel
    timeout: float
    disabled: bool = False
    key_manager: RoundRobinKeyManager | None = None
    _init_fn: Any = field(default=None, repr=False)

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
        if self._state == "OPEN":
            if (time.time() - self._last_failure_time) >= self.recovery_timeout:
                self._state = "HALF_OPEN"
        return self._state

    @property
    def is_available(self) -> bool:
        return self.state != "OPEN"

    def record_success(self) -> None:
        self._state = "CLOSED"
        self._failure_count = 0

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"

    def trip_open(self) -> None:
        self._state = "OPEN"
        self._failure_count = self.failure_threshold
        self._last_failure_time = time.time()

_PLACEHOLDER_VALUES = {
    "", "your_gemini_api_key_here",
    "your-api-key-here", "sk-xxx", "your_key_here",
    "your_github_pat_here", "your_groq_api_key_here",
    "your_cohere_api_key_here", "your_mistral_api_key_here",
}

def _is_valid_key(key: str | None) -> bool:
    if not key:
        return False
    # If comma separated, check the first one
    first_key = key.split(",")[0].strip()
    return first_key.lower() not in _PLACEHOLDER_VALUES

def _classify_error(error: Exception) -> str:
    error_str = str(error).lower()
    permanent_signals = [
        "404", "not found", "removed", "deprecated",
        "unauthorized", "invalid api key", "forbidden",
        "invalid_api_key", "401", "403",
    ]
    if any(sig in error_str for sig in permanent_signals):
        return "permanent"

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

    rate_limit_signals = [
        "429", "rate limit", "resource_exhausted",
        "quota", "too many requests", "rate_limit",
    ]
    if any(sig in error_str for sig in rate_limit_signals):
        return "rate_limited"

    # Gemini message ordering issues are transient (history dependent)
    gemini_transient = [
        "function call turn comes immediately after",
        "invalid_argument",
    ]
    if any(sig in error_str for sig in gemini_transient):
        return "transient"

    return "transient"

# Keys that are valid JSON Schema but not supported by LLM providers
_UNSUPPORTED_SCHEMA_KEYS = {
    "$schema", "$id", "$ref", "$comment", "$defs",
    "definitions", "examples", "default", "const",
    "if", "then", "else", "allOf", "not",
    "additionalProperties", "patternProperties",
    "minItems", "maxItems", "minLength", "maxLength",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "pattern", "format", "contentMediaType", "contentEncoding",
    "deprecated", "readOnly", "writeOnly",
}

def sanitize_json_schema(schema: dict) -> dict:
    """Recursively clean JSON schemas for LLM provider compatibility."""
    if not isinstance(schema, dict):
        return schema
    cleaned = {k: v for k, v in schema.items() if k not in _UNSUPPORTED_SCHEMA_KEYS}

    for key in ("anyOf", "oneOf"):
        if key in cleaned and isinstance(cleaned[key], list):
            non_null_schemas = [
                s for s in cleaned[key]
                if isinstance(s, dict) and s.get("type") != "null"
            ]
            if len(non_null_schemas) == 1:
                sub_schema = sanitize_json_schema(non_null_schemas[0])
                cleaned.pop(key)
                cleaned.update(sub_schema)
            elif len(non_null_schemas) > 1:
                cleaned[key] = [sanitize_json_schema(s) for s in non_null_schemas]

    if "type" in cleaned:
        if isinstance(cleaned["type"], list):
            types = [t for t in cleaned["type"] if t != "null"]
            cleaned["type"] = types[0] if types else "string"

    if "properties" in cleaned and isinstance(cleaned["properties"], dict):
        cleaned["properties"] = {
            k: sanitize_json_schema(v) for k, v in cleaned["properties"].items()
        }

    if "items" in cleaned and isinstance(cleaned["items"], dict):
        cleaned["items"] = sanitize_json_schema(cleaned["items"])

    return cleaned

def prepare_sanitized_tools(tools: list) -> list[dict]:
    from langchain_core.utils.function_calling import convert_to_openai_tool
    sanitized_tools = []
    for tool in tools:
        if isinstance(tool, dict):
            formatted = copy.deepcopy(tool)
        else:
            formatted = convert_to_openai_tool(tool)

        if "function" in formatted and "parameters" in formatted["function"]:
            formatted["function"]["parameters"] = sanitize_json_schema(
                formatted["function"]["parameters"]
            )
        sanitized_tools.append(formatted)
    return sanitized_tools

class BaseOrchestrator:
    """Base class for managing an LLM cascade."""
    
    def __init__(self, name: str) -> None:
        self.name = name
        self._providers: list[LLMProvider] = []
        self._breakers: dict[int, _TierBreaker] = {}
        self._initialized: bool = False

    def get_providers(self) -> list[LLMProvider]:
        self._init_providers()
        return self._providers

    def get_provider_info(self) -> list[dict[str, Any]]:
        self._init_providers()
        info = []
        for p in self._providers:
            brk = self._breakers.get(p.tier)
            info.append({
                "tier": p.tier,
                "provider": p.provider_name,
                "model": p.model_name,
                "disabled": p.disabled,
                "breaker_state": brk.state if brk else "N/A",
            })
        return info

    def _init_providers(self) -> None:
        """To be implemented by subclasses."""
        pass

    async def invoke(
        self,
        messages: list[BaseMessage],
        tools: list[BaseTool] | None = None,
    ) -> BaseMessage | None:
        self._init_providers()

        for provider in self._providers:
            tier = provider.tier
            breaker = self._breakers.get(tier)
            tier_label = f"{self.name}_tier_{tier}"

            if provider.disabled:
                continue

            if breaker and not breaker.is_available:
                agent_logger.debug("LLM", f"[SKIP] {self.name} Tier {tier} ({provider.provider_name}) circuit OPEN")
                continue

            if not check_llm_budget(tier_label):
                agent_logger.warn("LLM", f"[SKIP] {self.name} Tier {tier} ({provider.provider_name}) budget exhausted")
                continue

            # Attempt logic handling Key Rotation
            attempts = provider.key_manager.total_keys if provider.key_manager else 1
            
            for attempt in range(attempts):
                if tools:
                    # Try sanitized OpenAI-format dicts first (Gemini/Groq/Mistral)
                    # Fall back to raw BaseTool instances (Cohere requires this)
                    try:
                        sanitized = prepare_sanitized_tools(tools)
                        llm = provider.llm.bind_tools(sanitized)
                    except (ValueError, TypeError):
                        llm = provider.llm.bind_tools(tools)
                else:
                    llm = provider.llm

                result = await self._attempt_tier(provider, llm, messages, breaker, tier_label)
                
                # If we hit a rate limit AND have keys remaining, rotate and try again
                if isinstance(result, Exception) and _classify_error(result) == "rate_limited":
                    if provider.key_manager and provider.key_manager.total_keys > 1 and attempt < attempts - 1:
                        new_key = provider.key_manager.rotate()
                        agent_logger.warn("LLM", f"Rate limited. Rotating API key for {provider.provider_name}.")
                        # Re-initialize the LLM instance with the new key
                        provider.llm = provider._init_fn(new_key)
                        continue # Try again with new key
                    else:
                        break # No more keys, move to next tier
                
                # If it's a permanent or transient error that failed after retry, move to next tier
                if isinstance(result, Exception):
                    break
                    
                # Success
                if result is not None:
                    return result

        return None

    async def _attempt_tier(
        self,
        provider: LLMProvider,
        llm: Any,
        messages: list[BaseMessage],
        breaker: _TierBreaker | None,
        tier_label: str,
    ) -> BaseMessage | Exception | None:
        
        tier = provider.tier
        start = agent_logger.llm_start(f"{self.name}_{provider.provider_name}", provider.model_name)
        
        try:
            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=provider.timeout,
            )

            tool_calls = getattr(response, "tool_calls", [])
            agent_logger.llm_success(start, len(tool_calls) > 0, len(tool_calls))
            agent_logger.info("LLM", f"[OK] {self.name} Tier {tier}: {provider.provider_name}/{provider.model_name}")

            if breaker:
                breaker.record_success()
            system_health.mark_up(tier_label)
            return response

        except asyncio.TimeoutError as e:
            agent_logger.llm_error(start, TimeoutError(f"{self.name} Tier {tier} timed out after {provider.timeout}s"))
            error_class = "transient"
            returned_error = e

        except Exception as e:
            agent_logger.llm_error(start, e)
            error_class = _classify_error(e)
            returned_error = e

            if error_class == "permanent":
                agent_logger.warn("LLM", f"[PERMANENT ERROR] Disabling {self.name} Tier {tier} ({provider.provider_name})")
                provider.disabled = True
                if breaker:
                    breaker.trip_open()

        if breaker and error_class != "permanent":
            breaker.record_failure()
        system_health.mark_down(tier_label)
        
        return returned_error

class ThinkerOrchestrator(BaseOrchestrator):
    """Brain 1: Fast routing, intent classification, greetings."""

    def __init__(self) -> None:
        super().__init__("Thinker")

    def _init_providers(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        settings = get_settings()

        tier_configs = [
            (1, "GROQ_API_KEY", "Groq", self._init_groq, 5.0),
            (2, "GEMINI_API_KEY", "GeminiFlashLite", self._init_gemini_flash_lite, 5.0),
            (3, "MISTRAL_API_KEY", "Mistral", self._init_mistral, 10.0),
        ]

        self._setup_tiers(settings, tier_configs)

    def _setup_tiers(self, settings, tier_configs):
        for tier, key_attr, name, init_fn, timeout in tier_configs:
            key_value = getattr(settings, key_attr, "")
            if _is_valid_key(key_value):
                try:
                    km = RoundRobinKeyManager(key_value)
                    
                    def make_init(km, init_fn):
                        return lambda key: init_fn(key)
                        
                    llm = init_fn(km.get_current_key())
                    provider = LLMProvider(
                        tier=tier, 
                        provider_name=name.split("Flash")[0] if "Gemini" in name else name, 
                        model_name=llm.model_name if hasattr(llm, "model_name") else getattr(llm, "model", "unknown"), 
                        llm=llm, 
                        timeout=timeout,
                        key_manager=km,
                        _init_fn=make_init(km, init_fn)
                    )
                    self._providers.append(provider)
                    self._breakers[tier] = _TierBreaker(f"{self.name}_Tier{tier}_{name}", failure_threshold=2, recovery_timeout=30)
                    agent_logger.info("LLM", f"[OK] {self.name} Tier {tier} ({name}) initialized")
                except Exception as e:
                    agent_logger.error("LLM", f"Failed to init {self.name} Tier {tier} ({name})", e)

    @staticmethod
    def _init_groq(api_key: str):
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama-3.1-8b-instant", api_key=api_key, temperature=0.3, max_tokens=1024)

    @staticmethod
    def _init_gemini_flash_lite(api_key: str):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=api_key, temperature=0.3, max_output_tokens=1024)

    @staticmethod
    def _init_mistral(api_key: str):
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(model="mistral-small-latest", api_key=api_key, temperature=0.3, max_tokens=1024)

class ReasonerOrchestrator(BaseOrchestrator):
    """Brain 2: Deep reasoning, complex tool calling, synthesis."""

    def __init__(self) -> None:
        super().__init__("Reasoner")

    def _init_providers(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        settings = get_settings()

        tier_configs = [
            (1, "GEMINI_API_KEY", "GeminiFlash", self._init_gemini_flash, 45.0),
            (2, "GEMINI_API_KEY", "Gemini3.5Flash", self._init_gemini_3_5_flash, 45.0),
            (3, "COHERE_API_KEY", "Cohere", self._init_cohere, 30.0),
            (4, "MISTRAL_API_KEY", "Mistral", self._init_mistral, 30.0),
        ]

        self._setup_tiers(settings, tier_configs)

    def _setup_tiers(self, settings, tier_configs):
        for tier, key_attr, name, init_fn, timeout in tier_configs:
            key_value = getattr(settings, key_attr, "")
            if _is_valid_key(key_value):
                try:
                    km = RoundRobinKeyManager(key_value)
                    
                    def make_init(km, init_fn):
                        return lambda key: init_fn(key)
                        
                    llm = init_fn(km.get_current_key())
                    provider = LLMProvider(
                        tier=tier, 
                        provider_name="Gemini" if "Gemini" in name else name, 
                        model_name=llm.model_name if hasattr(llm, "model_name") else getattr(llm, "model", "unknown"), 
                        llm=llm, 
                        timeout=timeout,
                        key_manager=km,
                        _init_fn=make_init(km, init_fn)
                    )
                    self._providers.append(provider)
                    self._breakers[tier] = _TierBreaker(f"{self.name}_Tier{tier}_{name}", failure_threshold=2, recovery_timeout=60)
                    agent_logger.info("LLM", f"[OK] {self.name} Tier {tier} ({name}) initialized")
                except Exception as e:
                    agent_logger.error("LLM", f"Failed to init {self.name} Tier {tier} ({name})", e)

    @staticmethod
    def _init_gemini_flash(api_key: str):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-3.7-flash", google_api_key=api_key, temperature=0.3, max_output_tokens=4096)

    @staticmethod
    def _init_gemini_3_5_flash(api_key: str):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=api_key, temperature=0.3, max_output_tokens=4096)

    @staticmethod
    def _init_cohere(api_key: str):
        from langchain_cohere import ChatCohere
        return ChatCohere(model="command-r-plus-08-2024", cohere_api_key=api_key, temperature=0.3, max_tokens=4096)

    @staticmethod
    def _init_mistral(api_key: str):
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(model="mistral-large-latest", api_key=api_key, temperature=0.3, max_tokens=4096)

# Singletons
thinker = ThinkerOrchestrator()
reasoner = ReasonerOrchestrator()

# Deprecated export for backward compatibility during migration
orchestrator = reasoner

def get_providers():
    return reasoner.get_providers()