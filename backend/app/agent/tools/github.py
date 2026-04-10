"""GitHub Activity tool — fetch user profile stats and recent events."""

import httpx
from langchain_core.tools import tool

from app.config import get_settings


@tool
async def github_tool(username: str = "anurag-basuri") -> str:
    """Fetch Anurag's live GitHub profile stats and recent open-source activity."""
    settings = get_settings()
    headers = {"User-Agent": "Portfolio-App"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch recent events
            events_res = await client.get(
                f"https://api.github.com/users/{username}/events/public",
                params={"per_page": 5},
                headers=headers,
            )
            if events_res.status_code != 200:
                return f"Failed to fetch GitHub events for {username}. Status: {events_res.status_code}"

            events = events_res.json()

            # Fetch user info
            user_res = await client.get(
                f"https://api.github.com/users/{username}",
                headers=headers,
            )
            user = user_res.json() if user_res.status_code == 200 else None

        # Format output
        result = f"GitHub Profile: {username}\n"
        if user:
            result += f"Followers: {user.get('followers', 0)} | Following: {user.get('following', 0)} | Public Repos: {user.get('public_repos', 0)}\n"
            if user.get("bio"):
                result += f"Bio: {user['bio']}\n"

        if not events:
            result += "\nNo recent public activity."
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

        return result

    except httpx.TimeoutException:
        return "GitHub API timed out. Tell the user the service is slow right now."
    except Exception as e:
        return f"Error fetching GitHub data: {e}"
