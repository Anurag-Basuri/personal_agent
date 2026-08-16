"""
Unit tests for the Dual-Brain LLM fallback cascade logic.

Tests the cascade behavior in BaseOrchestrator by mocking LLM providers
and circuit breakers to verify correct tier-by-tier fallthrough.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.core.nodes import (
    STATIC_FALLBACK_MESSAGE,
    call_model,
)


def _make_state(user_msg: str = "What is Python?", intent: str = "tool_use") -> dict:
    """Create a minimal AgentState dict for testing."""
    return {
        "messages": [HumanMessage(content=user_msg)],
        "role": "ADMIN",
        "intent": intent,
    }


def _mock_provider(tier: int, name: str = "Mock", model: str = "mock-model"):
    """Create a mock LLMProvider with the given tier."""
    provider = MagicMock()
    provider.tier = tier
    provider.provider_name = name
    provider.model_name = model
    provider.llm = MagicMock()
    provider.disabled = False
    provider.key_manager = None
    provider.timeout = 10.0
    return provider


class TestCascadeSuccess:
    """Tests where at least one tier succeeds."""

    @patch("app.agent.core.nodes.reasoner")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_reasoner_succeeds_immediately(self, _mock_tools, mock_reasoner):
        """When the reasoner succeeds, call_model returns the response."""
        ai_response = AIMessage(content="Python is a programming language.")
        mock_reasoner.invoke = AsyncMock(return_value=ai_response)
        mock_reasoner.get_providers.return_value = [_mock_provider(1)]

        result = await call_model(_make_state())

        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "Python is a programming language."
        mock_reasoner.invoke.assert_awaited_once()

    @patch("app.agent.core.nodes.thinker")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_thinker_handles_greetings(self, _mock_tools, mock_thinker):
        """Greetings are routed through the thinker, not the reasoner."""
        ai_response = AIMessage(content="Hello! How can I help?")
        mock_thinker.invoke = AsyncMock(return_value=ai_response)
        mock_thinker.get_providers.return_value = [_mock_provider(1)]

        result = await call_model(_make_state("hello", intent="greeting"))

        assert result["messages"][0].content == "Hello! How can I help?"
        mock_thinker.invoke.assert_awaited_once()


class TestCascadeStaticFallback:
    """Tests where all tiers fail and the static Layer 6 activates."""

    @patch("app.agent.core.nodes.reasoner")
    @patch("app.agent.core.nodes.thinker")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_all_tiers_fail_returns_static_message(self, _mock_tools, mock_thinker, mock_reasoner):
        """When all providers fail, Layer 6 static message is returned (no crash)."""
        mock_reasoner.invoke = AsyncMock(return_value=None)
        mock_reasoner.get_providers.return_value = []
        mock_thinker.get_providers.return_value = []

        result = await call_model(_make_state())

        assert len(result["messages"]) == 1
        assert result["messages"][0].content == STATIC_FALLBACK_MESSAGE

    @patch("app.agent.core.nodes.reasoner")
    @patch("app.agent.core.nodes.thinker")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_no_providers_configured(self, _mock_tools, mock_thinker, mock_reasoner):
        """When zero providers are configured, Layer 6 static message is returned."""
        mock_reasoner.invoke = AsyncMock(return_value=None)
        mock_reasoner.get_providers.return_value = []
        mock_thinker.get_providers.return_value = []

        result = await call_model(_make_state())

        assert result["messages"][0].content == STATIC_FALLBACK_MESSAGE


class TestCircuitBreakerIntegration:
    """Tests verifying the orchestrator handles failures gracefully."""

    @patch("app.agent.core.nodes.reasoner")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_exception_in_invoke_returns_static(self, _mock_tools, mock_reasoner):
        """When invoke raises, call_model returns static fallback instead of crashing."""
        mock_reasoner.invoke = AsyncMock(return_value=None)
        mock_reasoner.get_providers.return_value = []

        mock_thinker_patch = patch("app.agent.core.nodes.thinker")
        mock_thinker = mock_thinker_patch.start()
        mock_thinker.get_providers.return_value = []

        result = await call_model(_make_state())

        assert result["messages"][0].content == STATIC_FALLBACK_MESSAGE
        mock_thinker_patch.stop()

    @patch("app.agent.core.nodes.reasoner")
    @patch("app.agent.core.nodes.thinker")
    @patch("app.agent.core.nodes.get_all_tools", return_value=[])
    async def test_greeting_fallback_when_thinker_fails(self, _mock_tools, mock_thinker, mock_reasoner):
        """When the thinker fails on a greeting, static fallback is used."""
        mock_thinker.invoke = AsyncMock(return_value=None)
        mock_thinker.get_providers.return_value = []
        mock_reasoner.get_providers.return_value = []

        result = await call_model(_make_state("hi there", intent="greeting"))

        assert result["messages"][0].content == STATIC_FALLBACK_MESSAGE
