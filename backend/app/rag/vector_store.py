"""
Vector store factory.

Returns a PGVector instance when connected to PostgreSQL,
or None when using SQLite (RAG is disabled gracefully).
"""

from __future__ import annotations

from app.config import get_settings
from app.core.logger import agent_logger

settings = get_settings()

# Flag for other modules to check
RAG_AVAILABLE = settings.is_postgres


def get_embeddings():
    """HuggingFace embedding model for vector operations."""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def get_neon_vector_store(collection_name: str = "portfolio_knowledge"):
    """
    Returns an instance of PGVector connected to NeonDB, or None if not on PostgreSQL.

    Warning: This assumes settings.DATABASE_URL is a PostgreSQL connection string.
    Since async pg urls (postgresql+asyncpg://) don't work cleanly for standard psycopg wrappers,
    we replace `+asyncpg` dynamically just for the Langchain connector which uses sync psycopg beneath.
    """
    if not RAG_AVAILABLE:
        agent_logger.debug("RAG", "⚠️ RAG disabled — DATABASE_URL is not PostgreSQL. Vector search unavailable.")
        return None

    try:
        from langchain_postgres.vectorstores import PGVector

        db_url = settings.DATABASE_URL.replace("+asyncpg", "")

        return PGVector(
            connection=db_url,
            embeddings=get_embeddings(),
            collection_name=collection_name,
            use_jsonb=True,
        )
    except Exception as e:
        agent_logger.error("RAG", f"Failed to initialize PGVector store: {e}")
        return None
