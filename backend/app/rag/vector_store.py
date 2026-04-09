"""
Neon PostgreSQL Vector Store Implementation.

Replaces ChromaDB. Connects to NeonDB pgvector extension via Langchain.
"""

from langchain_postgres.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import get_settings

settings = get_settings()

def get_embeddings():
    """Fallback embedding model if Gemini is not preferred or configured."""
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_neon_vector_store(collection_name: str = "portfolio_knowledge") -> PGVector:
    """
    Returns an instance of PGVector connected to NeonDB.
    
    Warning: This assumes settings.DATABASE_URL is a PostgreSQL connection string.
    Since async pg urls (postgresql+asyncpg://) don't work cleanly for standard psycopg wrappers,
    we replace `+asyncpg` dynamically just for the Langchain connector which uses sync psycopg beneath.
    """
    db_url = settings.DATABASE_URL.replace("+asyncpg", "")
    
    return PGVector(
        connection=db_url,
        embeddings=get_embeddings(),
        collection_name=collection_name,
        use_jsonb=True,
    )
