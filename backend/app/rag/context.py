"""
RAG context builder.

Retrieves relevant portfolio chunks from the vector store for grounded generation.
Falls back gracefully when RAG is unavailable (non-PostgreSQL database).
"""

from __future__ import annotations

from app.rag.vector_store import get_neon_vector_store, RAG_AVAILABLE
from app.core.logger import agent_logger


# Static fallback context when RAG is not available
_FALLBACK_CONTEXT = (
    "RAG vector search is not available in this environment. "
    "The agent can still use its tools (GitHub, LeetCode, portfolio DB search) to answer questions. "
    "For portfolio-specific queries, use the search_projects tool."
)


async def get_base_portfolio_context(query: str = "") -> str:
    """Build a contextual block by retrieving the most relevant chunks from the RAG store."""

    if not query:
        return "No specific query provided to search the portfolio."

    if not RAG_AVAILABLE:
        return _FALLBACK_CONTEXT

    try:
        # Initialize the Langchain PGVector store
        vector_store = get_neon_vector_store()

        if vector_store is None:
            return _FALLBACK_CONTEXT

        # Perform similarity search
        agent_logger.debug("RAG", f"Semantic search triggered for: '{query[:50]}'")

        docs = await vector_store.asimilarity_search(query, k=4)

        if not docs:
            return "No highly relevant portfolio data found in vector limits."

        context = "[Found Portfolio Context via RAG]\n\n"
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            context += f"[SOURCE: {source}]\n{doc.page_content}\n\n"
        context += "[End Portfolio Data]\n"

        return context

    except Exception as e:
        agent_logger.error("RAG", f"Error during vector retrieval: {e}")
        return _FALLBACK_CONTEXT
