<div align="center">

# 🧠 Autonomous Personal Agent

**An industry-grade, autonomous AI assistant embedded directly into a modern developer portfolio.** Built with strict Domain-Driven Design, LangGraph State Machines, a 6-Layer LLM Cascade, 17 MCP servers, and Deep-Privacy encryption.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20LangGraph-black?style=flat&logo=react)](https://github.com/)
[![Database](https://img.shields.io/badge/Database-Neon%20(PGVector)-blue?style=flat&logo=postgresql)](https://neon.tech/)

[Project Vision](#-project-vision--what-it-is) • [Core Systems Explained](#-core-systems-explained--how-it-works) • [Architecture](#-architecture-stack) • [Quick Start](#-quick-start-local-development) • [Environment Variables](#-environment-variables-dictionary)

</div>

---

## 🌎 Project Vision & What It Is

The **Autonomous Personal Agent** is not a standard RAG chatbot or a glorified FAQ bot. It is a highly capable **digital proxy** engineered to represent you to the public, assist your authenticated users, and act as your personal Jarvis in private.

Rather than just answering questions, this agent **decides, acts, remembers, and orchestrates**. It runs on a LangGraph state machine, allowing it to evaluate intents and route workflows autonomously. 

It operates across a strict **Tri-Tier Architecture**:

1. **🌐 Public Tier (The Advocate)**: Embedded in your public portfolio. It talks to recruiters and visitors, answers questions about your background (via RAG), dynamically scrapes your live GitHub metrics, and captures contact requests. It is entirely sandboxed and ephemeral.
2. **👤 Agent Tier (The Assistant)**: For users who log in (via Google OAuth). They get access to a persistent, omni-memory session where the agent remembers their preferences across days or weeks, but it remains restricted to portfolio-safe tools.
3. **🔐 Admin Tier (The Brain)**: Exclusive to you. Accessed via a custom admin login or through your personal Telegram/WhatsApp. Here, the agent has no restrictions. It can read your Gmail, draft emails, query raw databases, manage your calendar, check your server deployments, and control the entire system's Model Context Protocol (MCP) servers.

---

## ⚙️ Core Systems Explained & How It Works

### 1. The LangGraph State Machine
We rejected standard LangChain `create_react_agent` while-loops. They are prone to infinite loops, expensive, and impossible to pause for human-in-the-loop approvals.
Instead, this agent runs on a strict **LangGraph Directed Acyclic Graph (DAG)**. 
* **The Router Node**: Evaluates user inputs and classifies intent (e.g., greeting vs. meta_question vs. tool_use). If you just say "Hi", it skips the expensive tool-binding process entirely, saving time and money.
* **RBAC Layer**: Role-Based Access Control is injected dynamically at the node level. The LLM is literally never shown admin tools if a GUEST is talking to it, making prompt-injection hacking impossible.
* **6-Layer LLM Cascade**: For extreme reliability and cost optimization, requests flow through a cascading circuit breaker: GitHub Models (GPT-4o → Llama-3.3-70B → GPT-4o-mini) → Groq (Llama-3.1-8B) → HuggingFace (Qwen2.5-72B) → Static Python fallback. 

### 2. Omni-Memory & Deep Privacy 🔒
Most AI platforms log transcripts in plaintext. This project enforces an **Omni-Memory** architecture.
* Every single chat message is secured locally via **256-bit AES-GCM Encryption** prior to database insertion.
* Conversation Summarization: Every 15 messages, a background LLM process distills the chat into a short summary and extracts user preferences with confidence scores, storing them in long-term memory.
* Only the exact runtime environment holds the decryption key. Even if the entire PostgreSQL database is compromised, the attacker sees nothing but unreadable byte-salts.

### 3. Native RAG & Neon.tech Vectors 🗄️
Rather than fracturing data across multiple databases, everything converges into **Neon PostgreSQL**.
* **Vector Pipeline**: The AI leverages the `pgvector` extension to transform incoming messages and portfolio metadata (projects, profile, timeline) into mathematics using `langchain-huggingface` embeddings. 
* **Semantic Recovery**: When a visitor asks "What do you know about React?", the system performs an asynchronous semantic cosine similarity search directly against Postgres, loading exact technical specifications into the AI's short-term memory dynamically.

---

## 🛠️ The Agentic Toolbelt (MCP + Native Tools)

The AI is completely autonomous and capable of deciding when to call external logic functions. It uses a mix of 10 native Python tools and **17 dynamically loaded Model Context Protocol (MCP) servers**.

| Category | Capabilities & Tools |
|---|---|
| **Public Sandbox** | `github` (live commits/PRs), `github_repos` (read READMEs), `leetcode` (algorithmic ranks), `portfolio` (RAG search), `contact` (write secure DB inquiries), `weather` (Open-Meteo), `wikipedia`, `web_search` (DuckDuckGo), `hackernews` |
| **DevOps & Infra (Admin)** | Vercel, Netlify, Render (deployment monitoring, logs), Postgres (direct DB access), Puppeteer (headless browser automation) |
| **Productivity (Admin)** | Google Workspace (Gmail, Calendar, Drive), Linear (issue management), Todoist (tasks), Notion (knowledge base) |
| **Commerce (Admin)** | Zomato, Swiggy (Food/Instamart/Dineout), QuickCommerce (Blinkit/Zepto price comparison) |
| **System Control (Admin)**| `notify_admin` (push to Telegram/WhatsApp), `Sequential Thinking` (complex reasoning) |

---

## 🧩 Architecture Stack

The platform is completely decoupled to ensure standard MVC / Domain-Driven constraints.

#### API & Backend (FastAPI / `Python 3.11`)
*   **`/api`**: External HTTP REST boundaries (Strict 3-Way Split: `/api/public`, `/api/agent`, `/api/admin`).
*   **`/agent`**: The Neural Layer (LangGraph logic, Nodes, 6-Layer LLM Cascade).
*   **`/core`**: Auth, Encryption, Error Handlers, Circuit Breakers, Rate Limiting, Caching, Degradation tracking.
*   **`/rag`**: The Vector Embedding and PGVector contextual mechanisms.
*   **`/mcp`**: MCP client for dynamic tool discovery and runtime management.
*   **`/transports`**: Telegram Bot + WhatsApp notifications.
*   **`/repositories`**: Strict Repository Pattern for all database CRUD operations.

#### Client & Interface (`Next.js 15+`)
*   Fully server-side rendered App Router architecture.
*   Radix UI and Tailwind CSS for sophisticated, cinema-grade transitions.

*(For a highly technical breakdown of the architectural philosophy and implemented design patterns, see [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)).*

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
| `AUTH_SECRET` | Next.js Auth.js cryptographic signing string. Must match exactly in both frontend and backend directories. | **Critical** |
| `OMNI_MEMORY_KEY` | 32-Byte Secret Key powering the AES-GCM deep privacy algorithm. | **Critical** |
| `HF_TOKEN` | HuggingFace API key for LLM Tier 5 (Qwen2.5-72B). | **Critical** |
| `GROQ_API_KEY` | Groq API key for LLM Tier 4 (Llama-3.1-8B). | Recommended |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token from BotFather. | Optional |
| `CALLMEBOT_PHONE` | WhatsApp number for CallMeBot notifications. | Optional |

---

## 📄 License
This architecture is proudly opened to the community.
Licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
