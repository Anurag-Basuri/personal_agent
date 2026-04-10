"""Portfolio project search tool — queries the DB for matching projects."""

from langchain_core.tools import tool
from sqlalchemy import or_, select

from app.database import async_session
from app.models.project import Project


@tool
async def portfolio_tool(query: str) -> str:
    """Search Anurag's DB for portfolio projects by keyword or tech stack (e.g. React, Python, E-commerce)."""
    try:
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
            projects = result.scalars().all()

        if not projects:
            return (
                f'No specific projects found for "{query}". Anurag might have experience with it, '
                "but there are no dedicated published projects matching this query."
            )

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

        return output

    except Exception as e:
        return f"Database search failed: {e}"
