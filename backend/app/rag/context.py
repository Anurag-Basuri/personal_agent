"""RAG context builder — fetches base portfolio profile from PGVector in NeonDB."""

from __future__ import annotations

from app.rag.vector_store import get_neon_vector_store
from app.core.logger import agent_logger

async def get_base_portfolio_context(query: str = "") -> str:
    """Build a contextual block by retrieving the most relevant chunks from the RAG store."""
    try:
        if not query:
            return "No specific query provided to search the portfolio."

        # Initialize the Langchain PGVector store
        vector_store = get_neon_vector_store()
        
        # Perform similarity search
        agent_logger.debug("RAG", f"Semantic search triggered for: '{query[:50]}'")
        
        # Async retriever isn't natively supported on all sync pgvector implementations 
        # so we use ainvoke if available, else a wrapper or direct invoke
        docs = await vector_store.asimilarity_search(query, k=4)
        
        if not docs:
            return "No highly relevant portfolio data found in vector limits."

        context = "[Found Portfolio Context via RAG]\n"
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            context += f"--- Result {i+1} (Source: {source}) ---\n{doc.page_content}\n\n"
        context += "[End Portfolio Data]\n"

        return context

    except Exception as e:
        agent_logger.error("RAG", f"Error during vector retrieval: {e}")
        return ""
