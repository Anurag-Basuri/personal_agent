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

from functools import lru_cache

@lru_cache(maxsize=1)
def get_embeddings():
    """Cohere embeddings for vector operations."""
    from langchain_cohere import CohereEmbeddings
    return CohereEmbeddings(
        model="embed-english-v3.0",
        cohere_api_key=settings.COHERE_API_KEY
    )

def init_embeddings_eagerly() -> None:
    """Initialize the embeddings client early."""
    if RAG_AVAILABLE:
        agent_logger.info("RAG", "Initializing Google GenAI embeddings client...")
        get_embeddings()
        agent_logger.info("RAG", "[OK] Embeddings client ready")


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

        return PGVector(
            connection=settings.DATABASE_URL,
            embeddings=get_embeddings(),
            collection_name=collection_name,
            use_jsonb=True,
            async_mode=True,
            create_extension=False,
        )
    except Exception as e:
        agent_logger.error("RAG", f"Failed to initialize PGVector store: {e}")
        return None
