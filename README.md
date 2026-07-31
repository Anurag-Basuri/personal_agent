<div align="center">

# 🧠 Autonomous Personal Agent

**An industry-grade, autonomous AI assistant embedded directly into a modern developer portfolio.** Built with strict Domain-Driven Design, LangGraph State Machines, a 6-Layer LLM Cascade, 17 MCP servers, and Deep-Privacy encryption.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20LangGraph-black?style=flat&logo=react)](https://github.com/)
[![Database](https://img.shields.io/badge/Database-Neon%20(PGVector)-blue?style=flat&logo=postgresql)](https://neon.tech/)

[About the Application](#-about-the-application) • [How It Works](#-how-it-works-under-the-hood) • [Technology Stack](#-technology-stack) • [Agentic Toolbelt](#-the-agentic-toolbelt-mcp--native-tools) • [Engineering Patterns](#-resilience--engineering-patterns) • [Quick Start](#-quick-start-local-development)

</div>

---

> 📖 **Deep Dive**: For a highly technical breakdown of the architectural philosophy, RBAC boundaries, and implemented design patterns, please see the **[System Design Documentation (SYSTEM_DESIGN.md)](SYSTEM_DESIGN.md)**.

---

## 🌎 About the Application

The **Autonomous Personal Agent** is a highly capable **digital proxy** engineered to represent you to the public, assist your authenticated users, and act as your personal Jarvis in private.

Most AI portfolio integrations are simple "chatbots" that pattern-match keywords or use basic LangChain chains to answer predefined questions. This application is fundamentally different:

1. **It Decides and Acts**: It does not just return text. It autonomously decides which tools to call, queries databases, scrapes live GitHub metrics, formats responses, and can even send emails or manage your calendar.
2. **It Operates Across Multiple Platforms**: The agent shares a single "brain" (FastAPI backend) but communicates through multiple bodies: your Web Portfolio, Telegram, and (soon) WhatsApp.
3. **It Has Long-Term Memory**: It summarizes conversations in the background, extracts user preferences (e.g., "User prefers Python over Java"), and retains this context securely across sessions lasting weeks or months.
4. **It Understands Context**: When embedded on your website, it knows exactly which page the user is currently looking at and can navigate their browser dynamically.

---

## ⚙️ How It Works (Under the Hood)

The agent operates across a strict **Tri-Tier Architecture**, ensuring absolute segregation of capabilities:

1. **🌐 Public Tier (The Advocate)**: Embedded in your public portfolio. It talks to recruiters and visitors, answers questions about your background (via RAG), dynamically scrapes your live GitHub metrics, and captures contact requests. It is entirely sandboxed and ephemeral (no long term tracking).
2. **👤 Agent Tier (The Assistant)**: For users who log in (via Google OAuth). They get access to a persistent, omni-memory session where the agent remembers their preferences across days or weeks, but it remains restricted to portfolio-safe tools.
3. **🔐 Admin Tier (The Brain)**: Exclusive to you. Accessed via a custom admin login or through your personal Telegram/WhatsApp. Here, the agent has no restrictions. It can read your Gmail, draft emails, query raw databases, manage your calendar, check your server deployments, and control the entire system's Model Context Protocol (MCP) servers.

### The LangGraph State Machine
We rejected standard `while-loop` based AI agents. They are prone to infinite loops, highly expensive, and impossible to pause for human-in-the-loop approvals.
Instead, this agent runs on a strict **LangGraph Directed Acyclic Graph (DAG)**. 
* **The Router Node**: Evaluates user inputs and classifies intent (e.g., greeting vs. meta_question vs. tool_use). If you just say "Hi", it skips the expensive tool-binding process entirely, saving execution time and LLM token costs.
* **RBAC Layer**: Role-Based Access Control is injected dynamically at the graph node level. The LLM is literally never shown admin tools if a GUEST is talking to it, making prompt-injection hacking structurally impossible.

### Omni-Memory & Deep Privacy 🔒
Most AI platforms log transcripts in plaintext. This project enforces an **Omni-Memory** architecture.
* Every single chat message is secured locally via **256-bit AES-GCM Encryption** prior to database insertion. A unique 12-byte random nonce is generated per message.
* Conversation Summarization: Every 15 messages, a background LLM process distills the chat into a short summary and extracts user preferences with confidence scores, storing them in long-term memory.
* Only the exact runtime environment holds the decryption key. Even if the entire PostgreSQL database is compromised, the attacker sees nothing but unreadable byte-salts.

### Native RAG & Neon.tech Vectors 🗄️
Rather than fracturing data across multiple databases (like MongoDB for users and Chroma for vectors), everything converges into **Neon PostgreSQL**.
* **Vector Pipeline**: The AI leverages the `pgvector` extension to transform incoming messages and portfolio metadata (projects, profile, timeline) into mathematics using `langchain-huggingface` embeddings (`all-MiniLM-L6-v2`). 
* **Semantic Recovery**: When a visitor asks "What do you know about React?", the system performs an asynchronous semantic cosine similarity search directly against Postgres, loading exact technical specifications into the AI's short-term memory dynamically.

---

## 💻 Technology Stack

This platform is completely decoupled to ensure standard MVC / Domain-Driven constraints. 

### Backend (The Brain)
| Technology | Role |
|---|---|
| **Python 3.11+** | Core runtime environment. |
| **FastAPI** | High-performance asynchronous REST API framework. |
| **LangGraph** | DAG-based agent orchestration, state management, and multi-step reasoning. |
| **Model Context Protocol (MCP)** | Standardized protocol allowing the agent to dynamically discover and consume tools from independent local or remote servers. |
| **SQLAlchemy (Async)** | Object Relational Mapper for database interactions using the Repository Pattern. |
| **Cryptography** | `cryptography` library for AES-256-GCM encryption of all chat data. |
| **SlowAPI** | Multi-tier identity-aware rate limiting. |

### Frontend (The Interface)
| Technology | Role |
|---|---|
| **Next.js 15+** | Fully server-side rendered App Router architecture. |
| **React 19** | Component framework. |
| **NextAuth (Auth.js)** | Google OAuth2 identity provider integration. |
| **Tailwind CSS 4 & Radix UI** | Styling and headless accessible components for cinema-grade transitions. |
| **Zustand** | Lightweight global state management. |

### Database & Infrastructure
| Technology | Role |
|---|---|
| **Neon.tech PostgreSQL** | Primary relational database. |
| **PGVector** | Postgres extension for storing and querying 768-dimensional mathematical vector embeddings. |
| **HuggingFace** | Providing the embedding models for Semantic RAG pipelines. |
| **Vercel / Render** | Hosting targets for frontend and backend deployment. |

### The 6-Layer LLM Cascade
For extreme reliability and cost optimization, requests flow through a cascading circuit breaker. If one AI provider goes down, the system instantly fails over to the next:
1. **GitHub Models**: GPT-4o
2. **GitHub Models**: Llama-3.3-70B
3. **GitHub Models**: GPT-4o-mini
4. **Groq**: Llama-3.1-8B (Instant fallback)
5. **HuggingFace**: Qwen2.5-72B
6. **Static Fallback**: Hardcoded Python safe responses (zero API dependency)

---

## 🛠️ The Agentic Toolbelt (MCP + Native Tools)

The AI uses a mix of 10 native Python tools and **17 dynamically loaded Model Context Protocol (MCP) servers**, granting it massive real-world capabilities.

| Category | Capabilities & Tools |
|---|---|
| **Public Sandbox** | `github` (live commits/PRs), `github_repos` (read READMEs), `leetcode` (algorithmic ranks), `portfolio` (RAG search), `contact` (write secure DB inquiries), `weather` (Open-Meteo), `wikipedia`, `web_search` (DuckDuckGo), `hackernews` |
| **DevOps & Infra (Admin)** | **Vercel, Netlify, Render**: Check deployment status, read build logs, manage environments. **Postgres**: Direct database inspection. **Puppeteer**: Headless browser automation. |
| **Productivity (Admin)** | **Google Workspace**: Read/send Gmail, read/schedule Calendar events, Google Drive access. **Linear**: Issue management. **Todoist**: Tasks. **Notion**: Knowledge base CRUD. |
| **Commerce (Admin)** | **Zomato, Swiggy (Food/Instamart/Dineout), QuickCommerce**: Read menus, track orders, and compare grocery prices across Blinkit/Zepto dynamically. |
| **System Control (Admin)**| `notify_admin` (push notifications to admin via Telegram/WhatsApp), `Sequential Thinking` (complex reasoning algorithm execution). |

---

## 🛡️ Resilience & Engineering Patterns

To build an "Industry Grade" system, we rejected easy defaults in favor of enterprise patterns:

* **Strict Repository Pattern**: All raw SQL/SQLAlchemy queries are centralized in `SessionRepository`, `MessageRepository`, and `MemoryRepository`. Business logic never touches the database directly.
* **Circuit Breakers**: We employ 5 independent circuit breakers around our API-based LLM calls. If GitHub Models experiences an outage, the breaker trips to `OPEN`, immediately routing traffic to Groq without waiting for timeouts. It recovers via a `HALF_OPEN` probe automatically.
* **Graceful Degradation**: The `SystemHealth` singleton continuously tracks all subsystems (Database, RAG, MCP Servers, LLMs). If PGVector goes offline, the agent gracefully degrades to text-only mode and continues operating without crashing.
* **TTLCache & Auto-Invalidation**: Heavy read operations (like session history) use a thread-safe, in-memory `TTLCache`. Database writes automatically invalidate specific cache patterns (e.g., `app_cache.delete("history:*")`).
* **Multi-Tier Rate Limiting**: Expensive LLM calls are protected by a global LLM Budget per user, per hour.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
*   Node.js v18+ & Python 3.11+
*   A created [Neon.tech](https://neon.tech/) PostgreSQL Database String (`postgresql+asyncpg://...`)

### 1. Database & Backend Configuration
The backend server runs in an isolated Python wrapper.
```bash
# Clone and enter the backend directory
git clone https://github.com/Anurag-Basuri/personal_agent.git
cd personal_agent/backend

# Initialize Virtual Python Environment
python -m venv venv

# Windows Prompt: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Sync entire backend stack
pip install -r requirements.txt
cp .env.example .env
```

### 2. Booting the Neural API
Start the FastAPI auto-reloading server:
```bash
python -m uvicorn app.main:app --reload --port 4000
```
> *(Live Swagger / OpenAPI Documentation is dynamically generated at: `http://localhost:4000/docs`)*

### 3. Booting the Client Interface
```bash
cd ../frontend
npm install
npm run dev
```

---

## 🗝️ Environment Variables Dictionary

This system allows you to completely reskin the AI's personality and authentication layers strictly through `.env` arguments without writing a single line of python.

| Variable | Description | Requirement |
| :--- | :--- | :--- |
| `ADMIN_ID` & `ADMIN_PASSWORD_HASH` | Credentials for the exclusive Admin Web Dashboard. | **Critical** |
| `ADMIN_EMAIL` | Maps your Telegram transport to your real Admin database row. | **Critical** |
| `DATABASE_URL` | The Neon Postgres Database targeting your environment. Must prefix with `postgresql+asyncpg://` | **Critical** |
| `AUTH_SECRET` | Next.js Auth.js cryptographic signing string. Must match exactly in frontend and backend. | **Critical** |
| `OMNI_MEMORY_KEY` | 32-Byte Secret Key powering the AES-GCM deep privacy algorithm. | **Critical** |
| `HF_TOKEN` | HuggingFace API key for LLM Tier 5 (Qwen2.5-72B). | **Critical** |
| `GROQ_API_KEY` | Groq API key for LLM Tier 4 (Llama-3.1-8B). | Recommended |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token from BotFather. | Optional |
| `CALLMEBOT_PHONE` | WhatsApp number for CallMeBot notifications. | Optional |

---

## 📄 License
This architecture is proudly opened to the community.
Licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
