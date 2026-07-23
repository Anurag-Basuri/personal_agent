from app.agent.tools.contact import contact_tool
from app.agent.tools.github import github_tool
from app.agent.tools.github_repo import github_repo_tool
from app.agent.tools.hackernews import hackernews_tool
from app.agent.tools.leetcode import leetcode_tool
from app.agent.tools.portfolio import portfolio_tool
from app.agent.tools.weather import weather_tool
from app.agent.tools.web_search import web_search_tool
from app.agent.tools.wikipedia import wikipedia_tool

agent_tools = [
    # Portfolio-specific tools
    github_tool,
    github_repo_tool,
    leetcode_tool,
    portfolio_tool,
    contact_tool,
    # Public API tools
    weather_tool,
    wikipedia_tool,
    hackernews_tool,
    web_search_tool,
]


def get_public_tools() -> list:
    """Return only portfolio-safe tools for the public chatbot.

    This is the restricted toolset used by /api/public/* endpoints.
    Intentionally excludes MCP-discovered tools and any future
    admin-only tools (email, calendar, tasks).
    """
    return list(agent_tools)


def get_all_tools() -> list:
    """Merge local tools with dynamically discovered MCP tools."""
    from app.mcp.client import mcp_manager
    mcp_tools = mcp_manager.get_tools()
    return agent_tools + mcp_tools

__all__ = ["agent_tools", "get_all_tools", "get_public_tools"]
