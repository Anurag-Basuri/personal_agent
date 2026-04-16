"""Hacker News tool — search and trending stories via the Algolia HN API (free, no key)."""

import httpx
from langchain_core.tools import tool


@tool
async def hackernews_tool(query: str = "") -> str:
    """Search Hacker News for tech stories, discussions, and trending topics.
    Provide a search query (e.g., 'LangChain', 'AI agents', 'React 19').
    Leave query empty or use 'trending' to get the current top stories."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if not query or query.strip().lower() in ("trending", "top", "front page", "latest"):
                # Fetch current top stories from the front page
                top_ids_res = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                top_ids = top_ids_res.json()[:8]

                stories = []
                for sid in top_ids:
                    story_res = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                    story = story_res.json()
                    if story:
                        stories.append(story)

                if not stories:
                    return "Could not fetch top Hacker News stories right now."

                result = "🔥 Trending on Hacker News:\n\n"
                for i, s in enumerate(stories, 1):
                    title = s.get("title", "Untitled")
                    url = s.get("url", f"https://news.ycombinator.com/item?id={s.get('id', '')}")
                    score = s.get("score", 0)
                    comments = s.get("descendants", 0)
                    result += f"{i}. **{title}**\n"
                    result += f"   ⬆️ {score} points | 💬 {comments} comments\n"
                    result += f"   🔗 {url}\n\n"

                return result

            else:
                # Search via Algolia
                res = await client.get(
                    "https://hn.algolia.com/api/v1/search",
                    params={"query": query, "tags": "story", "hitsPerPage": 6},
                )
                data = res.json()
                hits = data.get("hits", [])

                if not hits:
                    return f'No Hacker News stories found for "{query}".'

                result = f'📰 Hacker News results for "{query}":\n\n'
                for i, h in enumerate(hits, 1):
                    title = h.get("title", "Untitled")
                    url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID', '')}"
                    points = h.get("points", 0)
                    comments = h.get("num_comments", 0)
                    result += f"{i}. **{title}**\n"
                    result += f"   ⬆️ {points} points | 💬 {comments} comments\n"
                    result += f"   🔗 {url}\n\n"

                return result

    except httpx.TimeoutException:
        return "Hacker News API timed out. Please try again."
    except Exception as e:
        return f"Error fetching Hacker News data: {e}"
