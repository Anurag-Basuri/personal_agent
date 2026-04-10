"""
RAG Ingester Script.

Fetches career and profile data from the Portfolio Database (Prisma Postgres),
chunks the text, embeds it, and loads it into the Agent's NeonDB PGVector store.

Usage: 
    Ensure PORTFOLIO_DB_URL and DATABASE_URL are set in .env
    Run via `python -m app.rag.ingester`
"""

import sys
import asyncio
import os
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Optional: Add dotenv load if run as script
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.rag.vector_store import get_neon_vector_store
from sqlalchemy.ext.asyncio import create_async_engine

async def fetch_portfolio_data() -> List[Document]:
    """Connects to the portfolio DB directly using asyncpg and extracts core knowledge."""
    # Often, the portfolio and agent DB are the same natively. If not, use PORTFOLIO_DB_URL.
    db_url = os.environ.get("PORTFOLIO_DB_URL", os.environ.get("DATABASE_URL", ""))
    
    if not db_url:
        print("❌ Error: PORTFOLIO_DB_URL or DATABASE_URL not set.")
        sys.exit(1)
        
    engine = create_async_engine(db_url)
    docs = []
    
    try:
        async with engine.begin() as conn:
            # 1. Fetch Profile
            try:
                res = await conn.execute("SELECT name, Tagline, header, bio, skills FROM \"Profile\" LIMIT 1")
                profile = res.fetchone()
                if profile:
                    content = f"# Anurag's Profile\n\nName: {profile[0]}\nTagline: {profile[1]}\nHeadline: {profile[2]}\nBio: {profile[3]}\nSkills: {profile[4]}"
                    docs.append(Document(page_content=content, metadata={"source": "Profile Core Data"}))
            except Exception as e:
                print(f"Failed to fetch Profile: {e}")
                
            # 2. Fetch Projects
            try:
                res = await conn.execute("SELECT title, description, \"techStack\", \"githubUrl\", \"liveUrl\" FROM \"Project\" WHERE status='published'")
                projects = res.fetchall()
                for p in projects:
                    content = f"# Project: {p[0]}\n\nDescription: {p[1]}\nTech Stack: {p[2]}\nGitHub: {p[3]}\nLive URL: {p[4]}"
                    docs.append(Document(page_content=content, metadata={"source": f"Project: {p[0]}"}))
            except Exception as e:
                print(f"Failed to fetch Projects: {e}")

            # 3. Fetch Journey (Work/Education)
            try:
                res = await conn.execute("SELECT type, title, organization, date, description FROM \"JourneyEntry\"")
                journeys = res.fetchall()
                for j in journeys:
                    content = f"# Career Journey: {j[1]} at {j[2]}\n\nType: {j[0]}\nDate: {j[3]}\nDescription: {j[4]}"
                    docs.append(Document(page_content=content, metadata={"source": f"Journey: {j[2]}"}))
            except Exception as e:
                print(f"Failed to fetch Journeys: {e}")
                
    finally:
        await engine.dispose()
        
    return docs

async def main():
    print("🚀 Starting RAG Ingestion Pipeline...")
    
    print("1. Fetching raw knowledge chunks from database...")
    docs = await fetch_portfolio_data()
    
    if not docs:
        print("⚠️ No documents were fetched. Check your database connection and schema.")
        return
        
    print(f"   Done. Fetched {len(docs)} highly structured documents.")
    
    print("2. Splitting text for optimal embedding resolution...")
    # Split text into manageable chunks so the vector math is highly specific
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )
    splits = text_splitter.split_documents(docs)
    print(f"   Done. Generated {len(splits)} chunks.")

    print("3. Connecting to Neon PGVector Store and embedding...")
    vector_store = get_neon_vector_store()
    
    # Store documents asynchronously
    await vector_store.aadd_documents(splits)
    
    print("✅ Successfully ingested all portfolio data into Omni-Memory vector store!")

if __name__ == "__main__":
    asyncio.run(main())
