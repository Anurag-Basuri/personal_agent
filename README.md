<div align="center">

# 🧠 Autonomous Personal Agent

**An industry-grade, autonomous AI assistant embedded directly into a modern developer portfolio.** Built with strict Domain-Driven Design, LangGraph State Machines, a 6-Layer LLM Cascade, 17 MCP servers, and Deep-Privacy encryption.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20LangGraph-black?style=flat&logo=react)](https://github.com/)
[![Database](https://img.shields.io/badge/Database-Neon%20(PGVector)-blue?style=flat&logo=postgresql)](https://neon.tech/)

[Project Vision](#-project-vision) • [Core Systems Explained](#-core-systems-explained) • [Architecture](#-architecture-stack) • [Quick Start](#-quick-start-local-development) • [Environment Variables](#-environment-variables-dictionary)

</div>

---

## 🌎 Project Vision
The **Autonomous Personal Agent** is not a standard RAG chatbot. It is a dual-interface agent engineered to act as an uncompromised proxy for the repository owner. 

When embedded into a portfolio site (**Public Mode**), it acts as an intelligent advocate—pitching your skills to recruiters, analyzing your GitHub metrics dynamically, and reading your Leetcode ranks. When accessed by you via an authenticated dashboard (**Private Mode**), it unlocks administrative powers (RBAC), bypassing restrictions to help manage tasks, view raw database data, and orchestrate personal operations.

---

## ⚙️ Core Systems Explained

### 1. The LangGraph State Machine
We rejected standard LangChain `create_react_agent` `while-loops`. They are prone to infinite loops and impossible to pause for human-in-the-loop approvals.
Instead, this agent runs on a strict **LangGraph Directed Acyclic Graph (DAG)**. 
*   **The Router Node**: Evaluates user inputs and classifies intent (greeting / meta_question / tool_use) to skip tools when unnecessary.
*   **RBAC Layer**: Injected dynamically at the node level. If the user invokes a tool tagged with `requires_admin` (but isn't authenticated), the State Machine physically routes the packet into an exception wrapper, making prompt-injection hacking impossible.
*   **6-Layer LLM Cascade**: GitHub Models (GPT-4o → Llama-3.3-70B → GPT-4o-mini) → Groq (Llama-3.1-8B) → HuggingFace (Qwen2.5-72B) → Static Python fallback. Each tier has an independent circuit breaker.

### 2. Omni-Memory & Deep Privacy 🔒
Most AI platforms log transcripts in plaintext. This project enforces an **Omni-Memory** architecture.
*   Every single chat message is secured locally via **256-bit AES-GCM Encryption** (via the cryptography library) prior to database insertion.
*   Only the exact runtime environment holds the `OMNI_MEMORY_KEY`. Even if the entire PostgreSQL database is stolen, the attacker receives nothing but unreadable byte-salts.

### 3. Native RAG & Neon.tech Vectors 🗄️
Rather than fracturing data by using MongoDB for users and ChromaDB for vectors, everything converges into **Neon PostgreSQL**.
*   **Vector Pipeline**: The AI leverages the `pgvector` extension to transform incoming messages and portfolio metadata into mathematics using `langchain-huggingface` embeddings. 
*   **Semantic Recovery**: When a user asks "What do you know about React?", the system performs an asynchronous semantic cosine similarity search directly against Postgres, loading exact technical specifications into the AI's short-term memory dynamically.

---

## 🛠️ The Agentic Toolbelt
The AI is completely autonomous and capable of deciding when to call external logic functions.

### 10 Built-in Tools
1.  `github` — Uses the GitHub API to dynamically scan your open source commits, PRs, and metrics.
2.  `github_repos` — Fetches repository READMEs and project details.
3.  `leetcode` — Scrapes competitive programming statistics and algorithmic competencies dynamically.
4.  `portfolio` — Executes semantic vector searches against your cached database resume.
5.  `contact` — Writes secure inquiries directly into the admin database for user feedback.
6.  `weather` — Current weather and forecasts via Open-Meteo.
7.  `wikipedia` — Knowledge lookup from Wikipedia.
8.  `web_search` — DuckDuckGo web search for general queries.
9.  `notify_admin` — Push notifications to admin via Telegram + WhatsApp.
10. `portfolio_api` — Live data from the Vercel portfolio backend.

### 17 MCP Servers
| Server | Purpose |
|---|---|
| Vercel, Netlify, Render | DevOps: deployment monitoring, logs, environment management |
| GitHub | Repository management, PRs, issues |
| Google | Gmail, Calendar, Drive access |
| Zomato | Restaurant search and ordering |
| Swiggy (x3) | Food, Instamart, Dineout |
| QuickCommerce | Blinkit, Zepto, BigBasket price comparison |
| HackerNews | Tech news and trending stories |
| DuckDuckGo | Web search |
| Sequential Thinking | Complex reasoning chains |
| Puppeteer | Headless browser automation |
| Postgres | Direct database access for admin |
| Linear | Issue and project management |
| Todoist | Task management |
| Notion | Notes, databases, knowledge base |

---

## 🧩 Architecture Stack

The platform is completely decoupled to ensure standard MVC / Domain-Driven constraints.

#### API & Backend (FastAPI / `Python 3.11`)
*   **`/api`**: External HTTP REST boundaries (public, agent, admin 3-way split).
*   **`/agent`**: The Neural Layer (LangGraph logic, Nodes, 6-Layer LLM Cascade).
*   **`/core`**: Auth, Encryption, Error Handlers, Circuit Breakers, Rate Limiting, Caching.
*   **`/rag`**: The Vector Embedding and PGVector contextual mechanisms.
*   **`/mcp`**: MCP client for dynamic tool discovery from 17 servers.
*   **`/transports`**: Telegram Bot + WhatsApp notifications.
*   **`/middlewares`**: Request ID, Request Logging, CORS.

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
| `AGENT_NAME` | The dynamic fallback name injected into the System Prompts. | Optional |
| `GITHUB_USERNAME` | The identifier the `github` tool uses to calculate open source metrics. | Optional |
| `GITHUB_TOKEN` | GitHub personal access token for API + MCP. | Optional |
| `LEETCODE_USERNAME` | The string the `leetcode` tool scrapes for algorithmic power. | Optional |
| `DATABASE_URL` | The Neon Postgres Database targeting your environment. Must prefix with `postgresql+asyncpg://` | **Critical** |
| `AUTH_SECRET` | Next.js Auth.js cryptographic signing string. Must match exactly in both frontend and backend directories. | **Critical** |
| `OMNI_MEMORY_KEY` | 32-Byte Secret Key powering the AES-GCM deep privacy algorithm. | **Critical** |
| `HF_TOKEN` | HuggingFace API key for LLM Tier 5 (Qwen2.5-72B). | **Critical** |
| `GROQ_API_KEY` | Groq API key for LLM Tier 4 (Llama-3.1-8B). | Recommended |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token from BotFather. | Optional |
| `TELEGRAM_ALLOWED_USER_IDS` | Comma-separated list of allowed Telegram user IDs. | Optional |
| `CALLMEBOT_PHONE` | WhatsApp number for CallMeBot notifications. | Optional |
| `CALLMEBOT_API_KEY` | CallMeBot API key. | Optional |
| `AUTOMATION_SECRET` | Shared secret for cron-triggered automation endpoints. | Optional |
| `REINDEX_SECRET` | Shared secret for the RAG reindex webhook. | Optional |

---

## 📄 License
This architecture is proudly opened to the community.
Licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
