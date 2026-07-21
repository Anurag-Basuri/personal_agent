"""
Unit tests for the 6-layer LLM fallback cascade logic.

Tests the cascade behavior in nodes.py by mocking LLM providers
and circuit breakers to verify correct tier-by-tier fallthrough.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.core.nodes import (
    STATIC_FALLBACK_MESSAGE,
    _llm_breakers,
    call_model,
)
from app.core.circuit_breaker import CircuitOpenError


def _make_state(user_msg: str = "What is Python?") -> dict:
    """Create a minimal AgentState dict for testing."""
    return {
        "messages": [HumanMessage(content=user_msg)],
        "role": "ADMIN",
        "intent": "tool_use",
    }


def _mock_provider(tier: int, name: str = "Mock", model: str = "mock-model"):
    """Create a mock LLMProvider with the given tier."""
    provider = MagicMock()
    provider.tier = tier
    provider.provider_name = name
    provider.model_name = model
    provider.llm = MagicMock()
    return provider


# ─── Cascade Tests ───────────────────────────────────────────────

class TestCascadeSuccess:
    """Tests where at least one tier succeeds."""

    @patch("app.agent.core.nodes.get_bound_providers")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_tier1_succeeds_immediately(self, _mock_tools, mock_providers):
        """When Tier 1 succeeds, the cascade returns immediately without touching other tiers."""
        p1 = _mock_provider(1, "GitHub", "gpt-4o")
        ai_response = AIMessage(content="Python is a programming language.")
        p1.llm.ainvoke = AsyncMock(return_value=ai_response)

        p2 = _mock_provider(2, "GitHub", "llama-3.3")
        p2.llm.ainvoke = AsyncMock()

        mock_providers.return_value = [p1, p2]

        # Reset breakers to CLOSED
        for b in _llm_breakers.values():
            b._state = "CLOSED"
            b._failure_count = 0

        result = await call_model(_make_state())

        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "Python is a programming language."
        # Tier 2 should never have been called
        p2.llm.ainvoke.assert_not_called()

    @patch("app.agent.core.nodes.get_bound_providers")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_tier1_fails_falls_to_tier2(self, _mock_tools, mock_providers):
        """When Tier 1 fails, the cascade falls to Tier 2."""
        p1 = _mock_provider(1, "GitHub", "gpt-4o")
        p1.llm.ainvoke = AsyncMock(side_effect=ConnectionError("rate limited"))

        p2 = _mock_provider(2, "GitHub", "llama-3.3")
        ai_response = AIMessage(content="Answer from Tier 2.")
        p2.llm.ainvoke = AsyncMock(return_value=ai_response)

        mock_providers.return_value = [p1, p2]

        for b in _llm_breakers.values():
            b._state = "CLOSED"
            b._failure_count = 0

        result = await call_model(_make_state())

        assert result["messages"][0].content == "Answer from Tier 2."


class TestCascadeStaticFallback:
    """Tests where all tiers fail and the static Layer 6 activates."""

    @patch("app.agent.core.nodes.get_bound_providers")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_all_tiers_fail_returns_static_message(self, _mock_tools, mock_providers):
        """When all providers fail, Layer 6 static message is returned (no crash)."""
        providers = []
        for tier in range(1, 6):
            p = _mock_provider(tier, f"Provider{tier}", f"model-{tier}")
            p.llm.ainvoke = AsyncMock(side_effect=RuntimeError("down"))
            providers.append(p)

        mock_providers.return_value = providers

        for b in _llm_breakers.values():
            b._state = "CLOSED"
            b._failure_count = 0

        result = await call_model(_make_state())

        assert len(result["messages"]) == 1
        assert result["messages"][0].content == STATIC_FALLBACK_MESSAGE

    @patch("app.agent.core.nodes.get_bound_providers")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_no_providers_configured(self, _mock_tools, mock_providers):
        """When zero providers are configured, Layer 6 static message is returned."""
        mock_providers.return_value = []

        result = await call_model(_make_state())

        assert result["messages"][0].content == STATIC_FALLBACK_MESSAGE


class TestCircuitBreakerIntegration:
    """Tests verifying circuit breakers skip tiers instantly."""

    @patch("app.agent.core.nodes.get_bound_providers")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_cb_open_skips_to_next_tier(self, _mock_tools, mock_providers):
        """When Tier 1's circuit breaker is OPEN, it skips instantly to Tier 2."""
        p1 = _mock_provider(1, "GitHub", "gpt-4o")
        p1.llm.ainvoke = AsyncMock()  # Should never be called

        p2 = _mock_provider(2, "GitHub", "llama-3.3")
        ai_response = AIMessage(content="From Tier 2.")
        p2.llm.ainvoke = AsyncMock(return_value=ai_response)

        mock_providers.return_value = [p1, p2]

        # Force Tier 1 breaker to OPEN, Tier 2 to CLOSED
        _llm_breakers[1]._state = "OPEN"
        _llm_breakers[1]._last_failure_time = 9999999999.0
        _llm_breakers[2]._state = "CLOSED"
        _llm_breakers[2]._failure_count = 0

        result = await call_model(_make_state())

        assert result["messages"][0].content == "From Tier 2."
        # Tier 1's LLM should never have been invoked (CB skipped it)
        p1.llm.ainvoke.assert_not_called()

    @patch("app.agent.core.nodes.get_bound_providers")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_all_cbs_open_returns_static(self, _mock_tools, mock_providers):
        """When all circuit breakers are OPEN, Layer 6 activates instantly."""
        providers = []
        for tier in range(1, 6):
            p = _mock_provider(tier, f"P{tier}", f"m{tier}")
            p.llm.ainvoke = AsyncMock()  # Should never be called
            providers.append(p)

            _llm_breakers[tier]._state = "OPEN"
            _llm_breakers[tier]._last_failure_time = 9999999999.0

        mock_providers.return_value = providers

        result = await call_model(_make_state())

        assert result["messages"][0].content == STATIC_FALLBACK_MESSAGE
        # None of the LLMs should have been invoked
        for p in providers:
            p.llm.ainvoke.assert_not_called()
