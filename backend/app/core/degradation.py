"""
Graceful Degradation — System Health Tracker.

Tracks the operational status of all subsystems and computes
a formal degradation level. Circuit breakers feed into this
tracker when they trip open, and subsystems self-report when
they recover.

Updated for the 6-layer LLM cascade (5 API tiers + 1 static).
"""

from __future__ import annotations

from enum import StrEnum

from app.core.logger import agent_logger


class DegradationLevel(StrEnum):
    """Ordered severity levels for system degradation."""
    
    FULL = "full"
    NO_RAG = "no_rag"
    NO_MCP = "no_mcp"
    NO_TOOLS = "no_tools"
    FALLBACK_LLM = "fallback"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class SystemHealth:
    """
    Singleton that tracks the operational status of all subsystems
    and computes the current degradation level.
    """

    def __init__(self):
        self.subsystems: dict[str, bool] = {
            "Thinker_Tier1_Groq": True,
            "Thinker_Tier2_GeminiFlashLite": True,
            "Thinker_Tier3_Mistral": True,
            "Reasoner_Tier1_GeminiFlash": True,
            "Reasoner_Tier2_Gemini3.5Flash": True,
            "Reasoner_Tier3_Cohere": True,
            "Reasoner_Tier4_Mistral": True,
            "rag": True,
            "mcp": True,
            "database": True,
        }

    def mark_down(self, subsystem: str) -> None:
        """Mark a subsystem as down and log the degradation."""
        if subsystem not in self.subsystems:
            self.subsystems[subsystem] = True
        if self.subsystems[subsystem]:
            self.subsystems[subsystem] = False
            agent_logger.warn(
                "HEALTH",
                f"⬇️ Subsystem '{subsystem}' marked DOWN — level: {self.level.value}",
            )

    def mark_up(self, subsystem: str) -> None:
        """Mark a subsystem as recovered."""
        if subsystem not in self.subsystems:
            self.subsystems[subsystem] = True
            return
        if not self.subsystems[subsystem]:
            self.subsystems[subsystem] = True
            agent_logger.info(
                "HEALTH",
                f"⬆️ Subsystem '{subsystem}' recovered — level: {self.level.value}",
            )

    @property
    def _llm_tiers_up(self) -> int:
        """Count how many LLM tiers are currently operational."""
        return sum(
            1 for k, v in self.subsystems.items()
            if k.startswith("llm_tier_") and v
        )

    @property
    def _llm_tiers_total(self) -> int:
        """Total number of tracked LLM tiers."""
        return sum(1 for k in self.subsystems if k.startswith("llm_tier_"))

    @property
    def level(self) -> DegradationLevel:
        """Compute the current degradation level from subsystem states."""
        up = self.subsystems
        llm_up = self._llm_tiers_up

        # Total LLM failure all tiers down, running on static Layer 6
        if llm_up == 0:
            return DegradationLevel.UNAVAILABLE

        # Count non LLM subsystems that are down
        non_llm_down = sum(
            1 for k, v in up.items()
            if not k.startswith("llm_tier_") and not v
        )

        # Everything working
        if llm_up == self._llm_tiers_total and non_llm_down == 0:
            return DegradationLevel.FULL

        # Multiple subsystems down (LLM tiers + other services)
        llm_down = self._llm_tiers_total - llm_up
        total_down = llm_down + non_llm_down

        if total_down >= 3:
            return DegradationLevel.DEGRADED

        # Single category failures
        if llm_down > 0 and non_llm_down == 0:
            return DegradationLevel.FALLBACK_LLM

        if not up.get("rag", True):
            return DegradationLevel.NO_RAG

        if not up.get("mcp", True):
            return DegradationLevel.NO_MCP

        if not up.get("database", True):
            return DegradationLevel.UNAVAILABLE

        return DegradationLevel.DEGRADED

    @property
    def available_capabilities(self) -> list[str]:
        """Return a human readable list of what's currently working."""
        up = self.subsystems
        caps = []

        llm_up = self._llm_tiers_up
        if llm_up > 0:
            # Find the lowest (best) active tier
            for i in range(1, 6):
                if up.get(f"llm_tier_{i}", False):
                    caps.append(f"chat (tier {i}, {llm_up} tiers available)")
                    break
        if up.get("mcp", True):
            caps.append("mcp_tools")
        if up.get("rag", True):
            caps.append("rag_search")
        if up.get("database", True):
            caps.append("memory")

        # Local tools always work if any LLM is available
        if llm_up > 0:
            caps.append("local_tools")

        return caps

    def get_status(self) -> dict:
        """Return a complete health status dict for API responses."""
        return {
            "level": self.level.value,
            "llm_tiers_up": self._llm_tiers_up,
            "llm_tiers_total": self._llm_tiers_total,
            "subsystems": dict(self.subsystems),
            "capabilities": self.available_capabilities,
        }


# Singleton
system_health = SystemHealth()
