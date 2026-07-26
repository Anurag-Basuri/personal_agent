"""GitHub Activity tool   fetch user profile stats and recent events."""

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.core.cache import TTLCache
from app.core.retry import retry_with_backoff

# Cache GitHub API responses for 5 minutes to avoid rate limits on popular portfolios
_github_cache = TTLCache(default_ttl=300)


async def _fetch_github_data(username: str, headers: dict) -> dict:
    """Internal function to fetch and combine GitHub data."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Fetch user info
        user_res = await client.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
        )
        user_res.raise_for_status()
        user = user_res.json()

        # Fetch recent events
        events_res = await client.get(
            f"https://api.github.com/users/{username}/events/public",
            params={"per_page": 5},
            headers=headers,
        )
        events_res.raise_for_status()
        events = events_res.json()

        return {"user": user, "events": events}


@tool
async def github_tool() -> str:
    """Fetch the developer's live GitHub profile stats (followers, repos) and recent open source activity.
    Use this when the user asks about my GitHub activity, commits, or overall coding presence."""
    settings = get_settings()
    username = settings.GITHUB_USERNAME

    if not username:
        return "GitHub username is not configured in the system settings."

    cache_key = f"github_profile:{username}"
    cached = _github_cache.get(cache_key)
    if cached:
        return cached

    headers = {"User-Agent": "Portfolio-App"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    try:
        data = await retry_with_backoff(
            _fetch_github_data,
            username,
            headers,
            max_retries=2,
            base_delay=1.0,
            retryable_exceptions=(httpx.TimeoutException, httpx.RequestError),
            operation_name="GitHub_API",
        )
        
        user = data["user"]
        events = data["events"]

        # Format output
        result = f"GitHub Profile: {username}\n"
        result += f"Followers: {user.get('followers', 0)} | Following: {user.get('following', 0)} | Public Repos: {user.get('public_repos', 0)}\n"
        if user.get("bio"):
            result += f"Bio: {user['bio']}\n"

        if not events:
            result += "\nNo recent public activity."
            _github_cache.set(cache_key, result)
            return result

        result += "\nRecent Activity (Last 5 events):\n"
        for event in events:
            repo_name = event.get("repo", {}).get("name", "unknown repo")
            date = event.get("created_at", "")[:10]
            event_type = event.get("type", "")

            if event_type == "PushEvent":
                commits = len(event.get("payload", {}).get("commits", []))
                result += f"- [{date}] Pushed {commits} commits to {repo_name}\n"
            elif event_type == "PullRequestEvent":
                action = event.get("payload", {}).get("action", "")
                result += f"- [{date}] {action} a pull request in {repo_name}\n"
            elif event_type == "CreateEvent":
                ref_type = event.get("payload", {}).get("ref_type", "resource")
                result += f"- [{date}] Created a new {ref_type} in {repo_name}\n"
            elif event_type == "WatchEvent":
                result += f"- [{date}] Starred {repo_name}\n"
            elif event_type == "IssuesEvent":
                action = event.get("payload", {}).get("action", "")
                result += f"- [{date}] {action} an issue in {repo_name}\n"
            else:
                result += f"- [{date}] Performed {event_type} in {repo_name}\n"

        _github_cache.set(cache_key, result)
        return result

    except Exception as e:
        return f"Error fetching GitHub data: {e}"
