"""LeetCode stats tool   fetch profile via official GraphQL API."""

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.core.cache import TTLCache
from app.core.retry import retry_with_backoff

# Cache LeetCode API responses for 5 minutes
_leetcode_cache = TTLCache(default_ttl=300)

LEETCODE_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
  userContestRanking(username: $username) {
    rating
    globalRanking
  }
}"""


async def _fetch_leetcode_data(username: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://leetcode.com/graphql/",
            json={"query": LEETCODE_QUERY, "variables": {"username": username}},
            headers={
                "Content-Type": "application/json",
                "Referer": "https://leetcode.com/",
                "Origin": "https://leetcode.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        )
        response.raise_for_status()
        return response.json()


@tool
async def leetcode_tool() -> str:
    """Fetch the developer's live LeetCode competitive programming stats (problems solved, ranking, etc).
    Use this when the user asks about coding stats, LeetCode performance, or algorithms."""
    settings = get_settings()
    username = settings.LEETCODE_USERNAME

    if not username:
        return "LeetCode username is not configured in the system settings."

    cache_key = f"leetcode_profile:{username}"
    cached = _leetcode_cache.get(cache_key)
    if cached:
        return cached

    try:
        data = await retry_with_backoff(
            _fetch_leetcode_data,
            username,
            max_retries=2,
            base_delay=1.0,
            retryable_exceptions=(httpx.TimeoutException, httpx.RequestError),
            operation_name="LeetCode_API",
        )

        user = data.get("data", {}).get("matchedUser")
        if not user:
            return f'LeetCode account "{username}" not found or the API returned no data.'

        # Parse submission stats
        submissions = user.get("submitStatsGlobal", {}).get("acSubmissionNum", [])

        def find_count(difficulty: str) -> int:
            for s in submissions:
                if s.get("difficulty") == difficulty:
                    return s.get("count", 0)
            return 0

        contest = data.get("data", {}).get("userContestRanking") or {}

        result = f"LeetCode Profile: {username}\n"
        result += f"Total Solved: {find_count('All')}"
        ranking = user.get("profile", {}).get("ranking")
        if ranking:
            result += f" (Global Ranking: #{ranking})"
        result += "\n"
        result += "Difficulty Breakdown:\n"
        result += f"- Easy: {find_count('Easy')}\n"
        result += f"- Medium: {find_count('Medium')}\n"
        result += f"- Hard: {find_count('Hard')}\n"

        if contest.get("rating"):
            result += f"Contest Rating: {round(contest['rating'])}\n"
        if contest.get("globalRanking"):
            result += f"Contest Global Rank: #{contest['globalRanking']}\n"

        _leetcode_cache.set(cache_key, result)
        return result

    except Exception as e:
        return f"Error fetching LeetCode data: {e}"
