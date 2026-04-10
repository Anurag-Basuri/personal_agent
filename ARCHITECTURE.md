# 🏛️ Architecture Design & Philosophy

This document explains the overarching architectural patterns of the Personal Agent backend. It serves as a guide to understand **where** things live, **how** they interact, and **why** specific technology choices were made over popular alternatives.

---

## 1. Domain-Driven Directory Structure
We strictly adhere to a decoupled, Domain-Driven Design (DDD) model. This ensures that the HTTP routing layer knows absolutely nothing about how the AI generates text, and the AI knows absolutely nothing about how HTTP requests work.

```text
app/
├── api/          # The Controller Layer (FastAPI Routers)
├── agent/        # The Neural Layer (LangGraph State Machine)
├── core/         # The System Infrastructure (Security, Logging, DB Config)
├── middlewares/  # HTTP Middlewares (CORS, Request IDs, Limits)
├── models/       # Relational Database Mappings (SQLAlchemy)
├── rag/          # Vector Embeddings and Knowledge Retrieval
└── schemas/      # Input/Output shape validation (Pydantic)
```

### The Request Lifecycle
1.  **Middleware**: An incoming request passes through `/middlewares/request_id.py` and rate limiting.
2.  **Controller**: It hits `/api/agent.py` which validates the JSON payload via `/schemas`.
3.  **Authentication**: Handled by `/core/auth.py` to decode NextAuth JWTs.
4.  **Service Invocation**: The controller passes the clean data to `/agent/service.py`.
5.  **Agent Orchestration**: The LangGraph state machine inside `/agent/core/builder.py` takes over, managing the cyclic loop between the LLM (`agent/llm.py`) and external systems (`agent/tools/`).
6.  **Persistence**: The resulting conversation is encrypted and persisted back to the database (`core/memory.py`).

---

## 2. Why We Use *This* and Not *That*

To build an "Industry Grade" system, we rejected several standard tutorials and easy defaults in favor of highly resilient enterprise patterns.

### 🧠 LangGraph vs. LangChain ReAct Agent
In basic AI projects, developers use `create_react_agent` with a simple while loop.
*   **The Problem**: A standard `while` loop forces the AI to be a black box. If it gets stuck endlessly calling tools, it crashes. If you want a human to approve an email before it's sent, you can't easily interrupt a `while` loop midway.
*   **Our Solution (LangGraph)**: We built a node-based State Machine (`app/agent/core/builder.py`). This allows us to define strict, exact pathways. The agent moves from Node A (`Model`) to Node B (`Tools`). This allows us to inject granular Role-Based Access Control (RBAC) dynamically and physically halt the graph if a tool requires user permission.

### 💾 NeonDB (PGVector) vs. ChromaDB (Local Vectors) vs. MongoDB
Many AI projects spin up a local ChromaDB instance to handle vector search and a MongoDB to handle chat logs.
*   **The Problem**: Storing vectors in ChromaDB, profile data in MongoDB, and users in SQLite completely fragments your data. If you delete a user in Mongo, their vectors remain orphaned in Chroma. You lose ACID compliance and backups become a nightmare.
*   **Our Solution (NeonDB with PGVector)**: NeonDB is a serverless PostgreSQL database. It natively handles standard relational data (Users/Messages), JSON documents (Tools schemas), AND mathematical vectors (PGVector) simultaneously. We have a single source of truth. When a chat message is logged, its vector embedding is saved in the exact same database row magically.

### 🔐 Auth.js (JWT) vs. Stateful Database Sessions
*   **The Problem**: Validating API calls via standard backend session cookies forces the API backend to hold memory of who is logged in. This breaks if you host the backend on a serverless Edge function (like Vercel) or scale horizontally across multiple instances.
*   **Our Solution**: The Next.js frontend handles OAuth (Google) via NextAuth, which generates cryptographically signed JWTs. The FastAPI backend never has to query the database to know who is talking. It just validates the cryptographic signature using `AUTH_SECRET`, resulting in hyper-fast, stateless authentication.

### 🛡️ AES-GCM Encryption vs. Plain Text Memory
*   **The Problem**: Standard agent frameworks serialize AI conversations directly into `history.txt` or JSON databases. If the database is compromised, all raw transcripts of the user's life are exposed.
*   **Our Solution**: We execute deep-privacy encryption at rest. Every single message inserted into the `AgentMessage` table is encrypted via 256-bit AES-GCM before it hits the disk. Only the application holds the decryption key (`OMNI_MEMORY_KEY`), making database leaks useless to attackers.
