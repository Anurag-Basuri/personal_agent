<div align="center">

# 🧠 Autonomous Personal Agent

**An industry-grade, autonomous AI assistant embedded directly into a modern developer portfolio.** Built with strict Domain-Driven Design, LangGraph State Machines, and Deep-Privacy encryptions.

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
*   **The Router Node**: Evaluates user inputs and mathematically decides if a LangChain tool must be invoked or if a direct chat response is sufficient.
*   **RBAC Layer**: Injected dynamically at the node level. If the user invokes a tool tagged with `requires_admin` (but isn't authenticated), the State Machine physically routes the packet into an exception wrapper, making prompt-injection hacking impossible.

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
The AI is completely autonomous and capable of deciding when to call external logic functions:
1.  `github`: Uses the GitHub API to dynamically scan your open source commits, PRs, and metrics.
2.  `leetcode`: Scrapes competitive programming statistics and algorithmic competencies dynamically.
3.  `portfolio`: Executes semantic vector searches against your cached database resume.
4.  `contact`: Bypasses external form submissions by authenticating and writing secure inquiries directly into the admin database for user feedback.

*(Each tool is abstracted so it automatically queries the identity parameters provided in your `.env`.)*

---

## 🧩 Architecture Stack

The platform is completely decoupled to ensure standard MVC / Domain-Driven constraints.

#### API & Backend (FastAPI / `Python 3.11`)
*   **`/api`**: External HTTP REST boundaries.
*   **`/agent`**: The Neural Layer (LangGraph logic, Nodes, Models).
*   **`/core`**: Auth.js stateless edge decoding, GCM Cryptography, Error Handlers.
*   **`/rag`**: The Vector Embedding and PostgreSQL contextual mechanisms.
*   **`/middlewares`**: Traffic monitoring and unique Request ID generation logic.

#### Client & Interface (`Next.js 15+`)
*   Fully server-side rendered App Router architecture.
*   Radix UI and Tailwind CSS for sophisticated, cinema-grade transitions.

*(For a highly technical breakdown of the psychological and design philosophy, see [ARCHITECTURE.md](ARCHITECTURE.md)).*

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
| `LEETCODE_USERNAME` | The string the `leetcode` tool scrapes for algorithmic power. | Optional |
| `DATABASE_URL` | The Neon Postgres Database targeting your environment. Must prefix with `postgresql+asyncpg://` | **Critical** |
| `AUTH_SECRET` | Next.js Auth.js cryptographic signing string. Must match exactly in both frontend and backend directories. | **Critical** |
| `OMNI_MEMORY_KEY` | 32-Byte Secret Key powering the AES-GCM deep privacy algorithm. Generatable via `import os, base64`. | **Critical** |
| `GEMINI_API_KEY` | HuggingFace or Gemini native developer key to orchestrate the internal LangGraph engine. | **Critical** |

---

## 📄 License
This architecture is proudly opened to the community.
Licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
