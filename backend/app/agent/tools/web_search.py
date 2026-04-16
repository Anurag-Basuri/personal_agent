"""Web search tool — general web search via DuckDuckGo HTML (free, no API key needed)."""

import httpx
from langchain_core.tools import tool


@tool
async def web_search_tool(query: str) -> str:
    """Search the web for any general question, current events, or information
    not covered by the portfolio tools. Provide a clear search query.
    Use this as a last resort when other tools don't have the answer."""
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            follow_redirects=True,
        ) as client:
            # Use DuckDuckGo's instant answer API
            res = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )
            data = res.json()

            # Build result from available fields
            parts = []

            # Abstract / instant answer
            abstract = data.get("AbstractText", "")
            abstract_source = data.get("AbstractSource", "")
            abstract_url = data.get("AbstractURL", "")
            if abstract:
                parts.append(f"**{abstract_source}**: {abstract}")
                if abstract_url:
                    parts.append(f"🔗 {abstract_url}")

            # Answer box (for calculations, etc.)
            answer = data.get("Answer", "")
            if answer:
                parts.append(f"**Answer**: {answer}")

            # Related topics
            related = data.get("RelatedTopics", [])
            if related:
                topics = []
                for rt in related[:5]:
                    text = rt.get("Text", "")
                    url = rt.get("FirstURL", "")
                    if text:
                        topics.append(f"- {text[:200]}" + (f"\n  🔗 {url}" if url else ""))
                if topics:
                    parts.append("\n**Related:**\n" + "\n".join(topics))

            # Definition
            definition = data.get("Definition", "")
            if definition:
                parts.append(f"**Definition**: {definition}")

            if parts:
                result = f'🔍 Web Search: "{query}"\n\n' + "\n\n".join(parts)
                return result

            # If DDG instant answer returned nothing useful, provide a helpful fallback
            return (
                f'Web search for "{query}" did not return a direct answer. '
                f"The user may want to visit: https://duckduckgo.com/?q={query.replace(' ', '+')} "
                f"for more detailed web results."
            )

    except httpx.TimeoutException:
        return "Web search timed out. Please try a more specific query."
    except Exception as e:
        return f"Error performing web search: {e}"
