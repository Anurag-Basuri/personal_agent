"""Wikipedia tool — knowledge lookup via the free Wikipedia API."""

import httpx
from langchain_core.tools import tool


@tool
async def wikipedia_tool(query: str) -> str:
    """Search Wikipedia for general knowledge on any topic.
    Returns a summary of the most relevant article.
    Use for factual questions about people, places, concepts, technologies, etc."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Search for relevant pages
            search_res = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": 3,
                    "format": "json",
                },
            )
            search_data = search_res.json()
            results = search_data.get("query", {}).get("search", [])

            if not results:
                return f'No Wikipedia articles found for "{query}".'

            # 2. Get the summary extract for the top result
            page_title = results[0]["title"]
            summary_res = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": page_title,
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "exsectionformat": "plain",
                    "format": "json",
                },
            )
            pages = summary_res.json().get("query", {}).get("pages", {})

            for page_id, page in pages.items():
                extract = page.get("extract", "")
                if extract:
                    # Truncate very long extracts
                    if len(extract) > 1500:
                        extract = extract[:1500] + "..."

                    output = f"📚 Wikipedia: {page_title}\n\n{extract}\n"
                    output += f"\nRead more: https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

                    # Also list other related results
                    if len(results) > 1:
                        output += "\n\nRelated articles:\n"
                        for r in results[1:]:
                            output += f"  - {r['title']}\n"

                    return output

            return f'Found "{page_title}" on Wikipedia but could not retrieve its summary.'

    except httpx.TimeoutException:
        return "Wikipedia API timed out. Please try again."
    except Exception as e:
        return f"Error searching Wikipedia: {e}"
