"""Agent tool registry.

Defines tool lists for different access levels:
  - get_public_tools(): Portfolio-safe tools for the public chatbot
  - get_all_tools(): All tools + MCP for authenticated users
"""

from app.agent.tools.contact import contact_tool
from app.agent.tools.github import github_tool
from app.agent.tools.github_repo import github_repo_tool

from app.agent.tools.leetcode import leetcode_tool
from app.agent.tools.portfolio_api import portfolio_api_tool
from app.agent.tools.weather import weather_tool
from app.agent.tools.web_search import web_search_tool
from app.agent.tools.wikipedia import wikipedia_tool
from app.agent.tools.notify import (
    broadcast_notification,
    send_telegram_notification,
    send_whatsapp_notification,
)

agent_tools = [
    # Portfolio data tools (API driven fetches from portfolio website)
    portfolio_api_tool,
    github_tool,
    github_repo_tool,
    leetcode_tool,
    contact_tool,
    # Public knowledge tools
    weather_tool,
    wikipedia_tool,

    web_search_tool,
    # Admin only notification tools
    send_telegram_notification,
    send_whatsapp_notification,
    broadcast_notification,
]


def get_public_tools() -> list:
    """Return only portfolio safe tools for the public chatbot.

    This is the restricted toolset used by /api/public/* endpoints.
    Intentionally excludes MCP-discovered tools and any admin only
    tools (notifications, email, calendar, tasks).
    """
    return [t for t in agent_tools if not getattr(t, "requires_admin", False)]


def get_all_tools(active_servers: list[str] | None = None) -> list:
    """Merge local tools with dynamically discovered MCP tools."""
    from app.mcp.client import mcp_manager
    mcp_tools = mcp_manager.get_tools(active_servers)
    return agent_tools + mcp_tools

__all__ = ["agent_tools", "get_all_tools", "get_public_tools"]
