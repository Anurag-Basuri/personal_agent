"""RAG Ingester   fetches portfolio data via API, embeds it, and loads into PGVector.

Two modes of operation:
  1. CLI: `python -m app.rag.ingester` (manual one-off)
  2. Programmatic: `await run_ingestion()` (called by webhook or background task)

Data Source: Portfolio website's public API (not direct DB access).
This ensures the agent's vector store mirrors exactly what the frontend shows.
"""

import asyncio

import httpx
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Optional: Add dotenv load if run as script
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.config import get_settings
from app.core.logger import agent_logger
from app.rag.vector_store import RAG_AVAILABLE, get_neon_vector_store


async def _fetch_api_data(portfolio_url: str, endpoint: str) -> dict | list | None:
    """Fetch data from a portfolio API endpoint."""
    url = f"{portfolio_url.rstrip('/')}/api/v1{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "PersonalAgent-RAG-Ingester/2.0",
                    "Accept": "application/json",
                },
            )
            if response.status_code != 200:
                agent_logger.warn("RAG", f"[INGEST] {endpoint} returned status {response.status_code}")
                return None
            json_data = response.json()
            # Portfolio API wraps responses: { success: true, data: ... }
            return json_data.get("data", json_data)
    except Exception as e:
        agent_logger.error("RAG", f"[INGEST] Failed to fetch {endpoint}: {e}")
        return None


async def fetch_portfolio_data_via_api() -> list[Document]:
    """Fetch all portfolio data via the public API and convert to LangChain Documents."""
    settings = get_settings()
    portfolio_url = settings.PORTFOLIO_URL

    if not portfolio_url:
        agent_logger.warn("RAG", "[INGEST] PORTFOLIO_URL not set. Cannot fetch portfolio data.")
        return []

    docs = []

    # 1. Profile
    profile = await _fetch_api_data(portfolio_url, "/profile")
    if profile and isinstance(profile, dict):
        parts = [f"# Anurag's Profile\n"]
        for key in ["name", "Tagline", "header", "bio", "pronouns", "Currentlocation",
                     "Originallocation", "email"]:
            if profile.get(key):
                parts.append(f"{key}: {profile[key]}")

        if profile.get("openToWork"):
            parts.append("Open to Work: Yes")
        if profile.get("availableFrom"):
            parts.append(f"Available From: {profile['availableFrom']}")

        skills = profile.get("skills")
        if skills:
            if isinstance(skills, dict):
                for cat, skill_list in skills.items():
                    if isinstance(skill_list, list):
                        parts.append(f"Skills ({cat}): {', '.join(skill_list)}")
            elif isinstance(skills, str):
                parts.append(f"Skills: {skills}")

        languages = profile.get("languages")
        if languages and isinstance(languages, list):
            parts.append(f"Languages: {', '.join(languages)}")

        docs.append(Document(
            page_content="\n".join(parts),
            metadata={"source": "Profile Core Data"},
        ))

        # Social links as a separate document
        social_links = profile.get("socialLinks", [])
        if social_links:
            link_lines = ["# Social Links & Coding Profiles\n"]
            for link in social_links:
                platform = link.get("platform", link.get("customLabel", "Link"))
                url = link.get("url", "")
                link_lines.append(f"- {platform}: {url}")
            for platform in ["github", "leetcode", "codeforces", "codechef", "gfg",
                             "kaggle", "hackerrank", "stackoverflow"]:
                url = profile.get(platform)
                if url:
                    link_lines.append(f"- {platform.capitalize()}: {url}")
            docs.append(Document(
                page_content="\n".join(link_lines),
                metadata={"source": "Social Links"},
            ))

    # 2. Projects
    projects = await _fetch_api_data(portfolio_url, "/projects")
    if projects and isinstance(projects, list):
        for p in projects:
            tech = p.get("techStack", "")
            if isinstance(tech, list):
                tech = ", ".join(tech)
            content = (
                f"# Project: {p.get('title', 'Untitled')}\n\n"
                f"Description: {p.get('description', '')}\n"
                f"Tech Stack: {tech}\n"
                f"GitHub: {p.get('githubUrl', 'N/A')}\n"
                f"Live URL: {p.get('liveUrl', 'N/A')}"
            )
            docs.append(Document(
                page_content=content,
                metadata={"source": f"Project: {p.get('title', 'Untitled')}"},
            ))

    # 3. Journey (Work + Education)
    journey = await _fetch_api_data(portfolio_url, "/journey")
    if journey and isinstance(journey, list):
        for j in journey:
            parts = [
                f"# Career Journey: {j.get('title', '')} at {j.get('organization', '')}",
                f"\nType: {j.get('type', 'OTHER')}",
                f"Date: {j.get('date', '')}",
                f"Description: {j.get('description', '')}",
            ]
            if j.get("degree"):
                parts.append(f"Degree: {j['degree']}")
            if j.get("fieldOfStudy"):
                parts.append(f"Field: {j['fieldOfStudy']}")
            if j.get("skills") and isinstance(j["skills"], list):
                parts.append(f"Skills: {', '.join(j['skills'])}")
            docs.append(Document(
                page_content="\n".join(parts),
                metadata={"source": f"Journey: {j.get('organization', j.get('title', ''))}"},
            ))

    # 4. Achievements
    achievements = await _fetch_api_data(portfolio_url, "/achievements")
    if achievements and isinstance(achievements, list):
        for a in achievements:
            parts = [
                f"# Achievement: {a.get('title', '')}",
                f"\nCategory: {a.get('category', '')}",
            ]
            if a.get("issuer"):
                parts.append(f"Issuer: {a['issuer']}")
            if a.get("event"):
                parts.append(f"Event: {a['event']}")
            if a.get("rank"):
                parts.append(f"Rank: {a['rank']}")
            if a.get("description"):
                parts.append(f"Description: {a['description']}")
            if a.get("tags") and isinstance(a["tags"], list):
                parts.append(f"Tags: {', '.join(a['tags'])}")
            docs.append(Document(
                page_content="\n".join(parts),
                metadata={"source": f"Achievement: {a.get('title', '')}"},
            ))

    # 5. Certifications
    certifications = await _fetch_api_data(portfolio_url, "/certifications")
    if certifications and isinstance(certifications, list):
        for c in certifications:
            parts = [
                f"# Certification: {c.get('title', '')}",
                f"\nIssuer: {c.get('issuer', '')}",
            ]
            if c.get("description"):
                parts.append(f"Description: {c['description']}")
            if c.get("skills") and isinstance(c["skills"], list):
                parts.append(f"Skills: {', '.join(c['skills'])}")
            docs.append(Document(
                page_content="\n".join(parts),
                metadata={"source": f"Certification: {c.get('title', '')}"},
            ))

    # 6. Blog posts
    blog = await _fetch_api_data(portfolio_url, "/blog")
    if blog and isinstance(blog, list):
        for b in blog:
            content = b.get("content", "")
            if len(content) > 2000:
                content = content[:2000] + "..."
            parts = [
                f"# Blog Post: {b.get('title', '')}",
                f"\nContent: {content}",
            ]
            if b.get("tags") and isinstance(b["tags"], list):
                parts.append(f"Tags: {', '.join(b['tags'])}")
            docs.append(Document(
                page_content="\n".join(parts),
                metadata={"source": f"Blog: {b.get('title', '')}"},
            ))

    return docs


async def run_ingestion():
    """Reusable ingestion function   callable from CLI, webhook, or background task.

    Fetches all portfolio data via the public API, chunks it, embeds it,
    and stores it in the PGVector store. Clears old documents first to prevent duplicates.
    """
    agent_logger.info("RAG", "[START] Starting RAG ingestion pipeline...")

    if not RAG_AVAILABLE:
        agent_logger.warn("RAG", "[WARN] RAG not available (requires PostgreSQL with pgvector)")
        return

    # 1. Fetch data via API
    docs = await fetch_portfolio_data_via_api()
    if not docs:
        agent_logger.warn("RAG", "[WARN] No documents fetched. Check PORTFOLIO_URL and portfolio server.")
        return

    agent_logger.info("RAG", f"  Fetched {len(docs)} documents from portfolio API")

    # 2. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
    )
    splits = text_splitter.split_documents(docs)
    agent_logger.info("RAG", f"  Generated {len(splits)} chunks")

    # 3. Store in vector DB
    vector_store = get_neon_vector_store()
    if vector_store is None:
        agent_logger.error("RAG", "[ERROR] Could not initialize vector store")
        return

    # Clear existing documents before re-ingesting to prevent duplicates and dimension mismatches
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        settings = get_settings()
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            # Delete embeddings associated with the portfolio_knowledge collection
            await conn.execute(text("""
                DELETE FROM langchain_pg_embedding 
                WHERE collection_id IN (
                    SELECT uuid FROM langchain_pg_collection WHERE name = 'portfolio_knowledge'
                );
            """))
        agent_logger.info("RAG", "  Cleared old vector store documents from database")
    except Exception as e:
        agent_logger.warn("RAG", f"  Could not clear old documents: {e}")

    await vector_store.aadd_documents(splits)
    agent_logger.info("RAG", f"[OK] Successfully ingested {len(splits)} chunks into vector store")


async def main():
    """CLI entry point for manual ingestion."""
    await run_ingestion()


if __name__ == "__main__":
    asyncio.run(main())
