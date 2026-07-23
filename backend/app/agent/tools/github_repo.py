"""GitHub Repo README tool — fetch raw README markdown from any repo."""

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.core.cache import TTLCache
from app.core.retry import retry_with_backoff

# Cache READMEs for 1 hour to prevent hitting GitHub rate limits on popular projects
_readme_cache = TTLCache(default_ttl=3600)


async def _fetch_readme(url: str, headers: dict) -> httpx.Response:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        return response


@tool
async def github_repo_tool(owner: str, repo: str) -> str:
    """Reads the raw technical README and architecture documentation from any public GitHub repository.
    Crucial for answering deep technical questions like 'How did you build X?' or 'What features does project Y have?'.
    ALWAYS use search_projects FIRST to find the githubUrl. 
    Then extract the owner and repo from the URL (e.g., https://github.com/Anurag-Basuri/BuyIt -> owner='Anurag-Basuri', repo='BuyIt')."""
    
    cache_key = f"readme:{owner}/{repo}"
    cached = _readme_cache.get(cache_key)
    if cached:
        return cached

    settings = get_settings()
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Anurag-Dev-AI-Agent",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    url = f"https://api.github.com/repos/{owner}/{repo}/readme"

    try:
        response = await retry_with_backoff(
            _fetch_readme,
            url,
            headers,
            max_retries=2,
            base_delay=1.0,
            retryable_exceptions=(httpx.TimeoutException, httpx.RequestError),
            operation_name="GitHub_Readme_Fetch",
        )

        if response.status_code == 404:
            result = (
                f"No README found for repository {owner}/{repo}. "
                "The repository might be private or empty."
            )
            _readme_cache.set(cache_key, result)
            return result

        response.raise_for_status()

        markdown = response.text

        # Token safety limit (~3k tokens)
        if len(markdown) > 15000:
            markdown = markdown[:15000] + "\n\n...[README TRUNCATED DUE TO EXTREME LENGTH]"

        result = f"TECHNICAL ARCHITECTURE DOCUMENTATION FOR {owner}/{repo}:\n\n{markdown}"
        _readme_cache.set(cache_key, result)
        return result

    except Exception as e:
        return f"Network error resolving GitHub repository: {e}"
