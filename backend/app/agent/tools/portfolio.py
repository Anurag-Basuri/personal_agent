"""Portfolio project search tool — queries the DB for matching projects."""

from langchain_core.tools import tool
from sqlalchemy import or_, select

from app.database import async_session
from app.models.project import Project
from app.core.cache import TTLCache
from app.core.retry import retry_with_backoff

# Cache database searches to avoid repeated hits (2 min TTL)
_portfolio_cache = TTLCache(default_ttl=120)

async def _fetch_projects(query: str) -> list[Project]:
    """Internal function to query projects."""
    async with async_session() as db:
        stmt = (
            select(Project)
            .where(
                Project.status == "published",
                or_(
                    Project.title.contains(query),
                    Project.description.contains(query),
                    Project.techStack.contains(query),
                ),
            )
            .limit(3)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

@tool
async def portfolio_tool(query: str) -> str:
    """Search the developer's DB for portfolio projects by keyword or tech stack (e.g. React, Python, E-commerce).
    Returns project title, tech stack, description, liveUrl, and githubUrl.
    IMPORTANT CHAINING RULE: If the user wants deep architecture details or asks "how did you build X", 
    you must use the returned 'githubUrl' with the read_github_readme tool next."""
    
    cache_key = f"search_projects:{query.strip().lower()}"
    cached = _portfolio_cache.get(cache_key)
    if cached:
        return cached

    try:
        projects = await retry_with_backoff(
            _fetch_projects,
            query,
            max_retries=2,
            base_delay=1.0,
            retryable_exceptions=(Exception,),
            operation_name="DB_Project_Search",
        )

        if not projects:
            result = (
                f'No specific projects found for "{query}". I might have experience with it, '
                "but there are no dedicated published projects matching this query."
            )
            _portfolio_cache.set(cache_key, result)
            return result

        output = f'Found {len(projects)} relevant projects for "{query}":\n\n'
        for p in projects:
            output += f"### {p.title}\n"
            output += f"Tech Stack: {p.techStack or 'N/A'}\n"
            output += f"Description: {p.description}\n"
            if p.liveUrl:
                output += f"Live Demo: {p.liveUrl}\n"
            if p.githubUrl:
                output += f"GitHub Repo: {p.githubUrl}\n"
            output += "\n"

        _portfolio_cache.set(cache_key, output)
        return output

    except Exception as e:
        return f"Database search failed: {e}"
