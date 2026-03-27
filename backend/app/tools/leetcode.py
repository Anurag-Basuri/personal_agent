"""LeetCode stats tool — fetch profile via official GraphQL API."""

import httpx
from langchain_core.tools import tool

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


@tool
async def leetcode_tool(username: str = "Anurag_Basuri") -> str:
    """Fetch Anurag's live LeetCode competitive programming stats (problems solved, ranking, etc)."""
    try:
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

        if response.status_code != 200:
            return (
                f"The LeetCode API returned status {response.status_code}. "
                "Tell the user you can't fetch live LeetCode stats right now."
            )

        data = response.json()
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

        return result

    except httpx.TimeoutException:
        return (
            "LeetCode API timed out. Tell the user the service is slow right now, "
            "but they can check the coding profiles section on the portfolio."
        )
    except Exception as e:
        return f"Error fetching LeetCode data: {e}"
