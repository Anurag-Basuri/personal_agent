"""GitHub Repo README tool — fetch raw README markdown from any repo."""

import httpx
from langchain_core.tools import tool

from app.config import get_settings


@tool
async def github_repo_tool(owner: str, repo: str) -> str:
    """Reads the raw technical README and architecture documentation from any public GitHub repository.
    Crucial for answering deep technical questions like 'How did you build X?' or 'What features does project Y have?'.
    Combine with search_projects to find the githubUrl first."""
    settings = get_settings()
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Anurag-Dev-AI-Agent",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            response = await client.get(url, headers=headers)

        if response.status_code == 404:
            return (
                f"No README found for repository {owner}/{repo}. "
                "The repository might be private or empty."
            )

        if response.status_code != 200:
            return f"Failed to fetch repo data. GitHub returned status: {response.status_code}"

        markdown = response.text

        # Token safety limit (~3k tokens)
        if len(markdown) > 15000:
            markdown = markdown[:15000] + "\n\n...[README TRUNCATED DUE TO EXTREME LENGTH]"

        return f"TECHNICAL ARCHITECTURE DOCUMENTATION FOR {owner}/{repo}:\n\n{markdown}"

    except httpx.TimeoutException:
        return "GitHub API timed out. Tell the user the service is slow right now."
    except Exception as e:
        return f"Network error resolving GitHub repository: {e}"
