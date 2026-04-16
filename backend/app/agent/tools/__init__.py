from app.agent.tools.github import github_tool
from app.agent.tools.github_repo import github_repo_tool
from app.agent.tools.leetcode import leetcode_tool
from app.agent.tools.portfolio import portfolio_tool
from app.agent.tools.contact import contact_tool
from app.agent.tools.weather import weather_tool
from app.agent.tools.wikipedia import wikipedia_tool
from app.agent.tools.hackernews import hackernews_tool
from app.agent.tools.web_search import web_search_tool

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

__all__ = ["agent_tools"]

