"""
Graceful Degradation — System Health Tracker.

Tracks the operational status of all subsystems and computes
a formal degradation level. Circuit breakers feed into this
tracker when they trip open, and subsystems self-report when
they recover.
"""

from __future__ import annotations

from enum import Enum

from app.core.logger import agent_logger


class DegradationLevel(str, Enum):
    """Ordered severity levels for system degradation."""
    FULL = "full"               # Everything operational
    NO_RAG = "no_rag"           # Vector store down — fallback context
    NO_MCP = "no_mcp"           # MCP servers down — local tools only
    NO_TOOLS = "no_tools"       # All external tools failing — LLM knowledge only
    FALLBACK_LLM = "fallback"   # Primary LLM down — Gemini handles everything
    DEGRADED = "degraded"       # Multiple subsystems down
    UNAVAILABLE = "unavailable" # No LLM available — static error only


class SystemHealth:
    """
    Singleton that tracks the operational status of all subsystems
    and computes the current degradation level.
    """

    def __init__(self):
        self.subsystems: dict[str, bool] = {
            "primary_llm": True,
            "fallback_llm": True,
            "rag": True,
            "mcp": True,
            "database": True,
        }

    def mark_down(self, subsystem: str) -> None:
        """Mark a subsystem as down and log the degradation."""
        if subsystem in self.subsystems and self.subsystems[subsystem]:
            self.subsystems[subsystem] = False
            agent_logger.warn(
                "HEALTH",
                f"⬇️ Subsystem '{subsystem}' marked DOWN — level: {self.level.value}",
            )

    def mark_up(self, subsystem: str) -> None:
        """Mark a subsystem as recovered."""
        if subsystem in self.subsystems and not self.subsystems[subsystem]:
            self.subsystems[subsystem] = True
            agent_logger.info(
                "HEALTH",
                f"⬆️ Subsystem '{subsystem}' recovered — level: {self.level.value}",
            )

    @property
    def level(self) -> DegradationLevel:
        """Compute the current degradation level from subsystem states."""
        up = self.subsystems

        # Total failure — no LLMs at all
        if not up["primary_llm"] and not up["fallback_llm"]:
            return DegradationLevel.UNAVAILABLE

        # Count how many subsystems are down
        down_count = sum(1 for v in up.values() if not v)

        if down_count == 0:
            return DegradationLevel.FULL

        # Multiple subsystems down
        if down_count >= 2:
            return DegradationLevel.DEGRADED

        # Single subsystem failures
        if not up["primary_llm"]:
            return DegradationLevel.FALLBACK_LLM
        if not up["rag"]:
            return DegradationLevel.NO_RAG
        if not up["mcp"]:
            return DegradationLevel.NO_MCP
        if not up["database"]:
            return DegradationLevel.UNAVAILABLE

        return DegradationLevel.DEGRADED

    @property
    def available_capabilities(self) -> list[str]:
        """Return a human-readable list of what's currently working."""
        up = self.subsystems
        caps = []

        if up["primary_llm"] or up["fallback_llm"]:
            provider = "primary" if up["primary_llm"] else "fallback"
            caps.append(f"chat ({provider})")
        if up["mcp"]:
            caps.append("mcp_tools")
        if up["rag"]:
            caps.append("rag_search")
        if up["database"]:
            caps.append("memory")

        # Local tools always work if LLM is available
        if up["primary_llm"] or up["fallback_llm"]:
            caps.append("local_tools")

        return caps

    def get_status(self) -> dict:
        """Return a complete health status dict for API responses."""
        return {
            "level": self.level.value,
            "subsystems": dict(self.subsystems),
            "capabilities": self.available_capabilities,
        }


# Singleton
system_health = SystemHealth()
