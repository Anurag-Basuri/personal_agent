# Personal Agent Customizations

## Rules & Workflow

- **Repository Pattern Enforcement**: Do NOT use raw SQLAlchemy queries in API endpoints or services. Use the dedicated Repositories located in `backend/app/repositories/`.
- **Resilience**: Any external HTTP requests or third-party API calls must use `retry_with_backoff` (and potentially a `CircuitBreaker`) from `backend/app/core`.
- **Caching**: Wrap read-heavy database calls with the `TTLCache` to prevent performance degradation. Ensure cache is invalidated upon writes.
- **Rate Limiting**: Protect new FastAPI endpoints with the `rate_limit` dependency from `app.core.rate_limiter`.
- **Python Conventions**: Use type hints, adhere to PEP 8, and format docstrings for all new methods.
- **Comment Conventions (Server Backend Only)**:
  - **No Inline Comments**: Do NOT place comments on the same line as code (e.g., `y = x + y # qwerty`). All comments must reside on their own dedicated line immediately preceding the code block or statement they describe.
  - **No Hyphens or Dashes**: Do NOT use hyphens, dashes, em-dashes, or box-drawing horizontal lines (e.g., `-`, `–`, `—`, `─`) in any comments or comment headers of any type.
  - **No Gaps Before Functions/Blocks**: There must NOT be any blank lines or vertical gaps between a comment and the immediate function, method, class, or code block it belongs to. The comment must be directly adjacent to its target line.
  - **Hierarchical Structure**: Avoid large monolithic block comments inside method or function bodies. Break down extensive explanations and place them as high-level docstrings before the particular methods or functions.
  - **Specific Single-Line Comments**: Within function or method bodies, write very specific, concise single-line comments immediately before the code block describing the step or logic.
- **Workflow**: Create detailed implementation plans in an artifact before execution for major structural changes. Write code incrementally and atomically.
- **Documentation Context**: Always read and maintain the context of the four primary project documentation files (`README.md`, `PROGRESS.md`, `ROADMAP.md`, and `SYSTEM_DESIGN.md`). Whenever you implement new features or architectural patterns, you must proactively update these files accordingly, or at the very least, explicitly inform the user that these files need updates to reflect the changes.

## Architecture Decisions (Finalized)

### System Architecture (3-Way Split)
This backend serves distinct frontends on separate domains with strict physical route segregation:

1.  **Portfolio Chatbot** (`/api/public/*`)
    - **No authentication**. Open to the public via embedded widget.
    - **Ephemeral sessions**: Session ID lives in browser `sessionStorage` (survives refresh, destroyed on tab close). Backend deletes sessions after **1 hour of inactivity**.
    - **Message cap**: 20 messages per session. Rate limiting handles the rest.
    - **Tools**: Portfolio-safe only (search_projects, github, leetcode, weather, wikipedia, hackernews, web_search, contact_form). No admin or personal tools.
    - **System prompt**: Speaks as Anurag in first person, scoped to portfolio/professional topics.

2.  **Agent Website** (`/api/agent/*`)
    - **Authentication required**: Standard login/signup for normal users.
    - **One continuous conversation per account**: No "new chat" concept. Every message is part of a single thread. Context managed via recent messages + summarization + VectorDB RAG.
    - **Delete & restart**: Users can delete ALL their chat history and start fresh. No partial archive.
    - **Tools**: Standard agent tools, strictly sandboxed to prevent access to admin's personal data.
    - **Memory**: Conversation summarization + preference extraction + VectorDB for long-term RAG retrieval.

3.  **Admin Exclusive** (`/api/admin/*`)
    - **Authentication required**: Exclusive to Anurag.
    - **Complete access**: Unrestricted access to ALL tools (Email, Calendar, Tasks, MCP system management).
    - **Absolute segregation**: Guarantees that normal users can never collide with or access admin-only capabilities.

### LLM Cascade (6-Layer Fallback)
Both products share the same cascade: GitHub Models (gpt-4o → Llama-3.3-70B → gpt-4o-mini) → Groq (llama-3.1-8b) → HuggingFace (Qwen2.5-VL-72B) → Static Python fallback. Each tier has an independent circuit breaker.

### Frontend Strategy
Frontend will be built AFTER the backend is complete. No frontend work until all backend endpoints are stable and tested.
