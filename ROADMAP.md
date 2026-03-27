# Personal Agent 2.0 — Roadmap

A hands-on learning project to build a real-world **personal AI agent** that manages Telegram, WhatsApp, emails, scheduling, tasks, and more — using RAG, MCP, LangChain, LangGraph, and agentic AI patterns.

> **Guiding Principle**: Each phase teaches a specific AI/engineering skill. The agent should evolve from "talks about you" → "does things for you."

---

## Phase 0: Project Baseline ✅ (Mostly Done)

### Goal

Capture the current system state and prevent regressions.

### What Exists

- Express backend with LangChain agent loop (tool-calling while-loop, max 3 iterations)
- Dual-LLM failover: HuggingFace Qwen2.5-72B (primary) → Gemini 2.5 Flash (fallback)
- Sticky fallback logic — if primary fails once per request, skip it for remaining loops
- 5 read-only tools: GitHub profile, GitHub repos, LeetCode stats, portfolio search, contact form
- Prisma/SQLite persistence for chat history (sessions stored as serialized JSON)
- In-memory cache with 60s TTL to reduce DB roundtrips
- Structured logging via `agentLogger`
- Next.js frontend with chat widget (4 components)
- Zod-validated environment config

### Remaining Tasks

- [ ] Create a one-page architecture diagram (text-based in `ARCHITECTURE.md`)
- [ ] Document all tool schemas and what they do
- [ ] Write baseline QA checklist (cold-start time, tool success rate, error recovery)

### You'll Learn

- How to document and reason about system architecture

---

## Phase 0.5: Platform Bootstrap ✅ (Done)

### Goal

Next.js frontend + Express backend working end-to-end.

### Completed

- [x] Express app with `/chat`, `/chat/reset`, `/health` routes
- [x] Next.js frontend with chat widget
- [x] CORS configured
- [x] Dev scripts for frontend + backend
- [x] Chat flow: UI → API → LLM → tool calls → response

---

## Phase 1: True RAG Pipeline (Priority: 🥇)

### Goal

Replace the static `context.builder.ts` (which just reads a DB row) with a real retrieval-augmented generation pipeline. **This is the #1 learning priority.**

### What You'll Learn

- Embedding models, vector stores, similarity search
- Document chunking and preprocessing
- LangChain retrieval chains
- Grounded generation with citations

### Tasks

#### 1.1 — Choose and Set Up a Vector Store

- **Option A (Recommended for learning)**: [ChromaDB](https://www.trychroma.com/) — runs locally, simple API, great for dev
- **Option B (Production-ready)**: [Pinecone](https://www.pinecone.io/) — managed, free tier available
- **Option C (Self-hosted)**: pgvector extension on PostgreSQL
- Install and configure chosen store
- Create a vector store service module: `backend/rag/vector.store.ts`

#### 1.2 — Build the Document Ingester

- Create `backend/rag/ingester.ts` — a script that:
  - Fetches portfolio projects from the DB
  - Fetches your resume content (PDF → text)
  - Fetches GitHub READMEs for your repos via the GitHub API
  - Optionally fetches blog posts if you have any
- Chunk documents using LangChain's `RecursiveCharacterTextSplitter` (chunk size ~500, overlap ~50)
- Store metadata with each chunk: `{ source, title, type, url }`

#### 1.3 — Choose an Embedding Model

- **Option A (Free)**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2` via API
- **Option B (Cheap + good)**: OpenAI `text-embedding-3-small` ($0.02/1M tokens)
- **Option C (Local)**: Run a local embedding model via Ollama
- Create `backend/rag/embedder.ts`

#### 1.4 — Build the Retrieval Chain

- Replace `getBasePortfolioContext()` with a proper retrieval function
- Flow: user query → embed query → similarity search (top-k=5) → assemble context
- Add source attribution: each chunk carries its origin metadata
- Optionally add a re-ranker (Cohere Rerank or cross-encoder) for better precision

#### 1.5 — Update Prompts for RAG

- Modify `SYSTEM_PERSONA` to instruct the LLM to only answer from retrieved context
- Add `[SOURCE: project_name]` tags so the agent cites its sources
- Handle "no relevant context found" gracefully

### Deliverables

- `backend/rag/vector.store.ts` — vector DB connection + query
- `backend/rag/ingester.ts` — document ingestion script (`npx ts-node backend/rag/ingester.ts`)
- `backend/rag/embedder.ts` — embedding wrapper
- `backend/rag/retriever.ts` — retrieval chain
- Updated `context.builder.ts` using the retrieval chain
- Unit tests for ingestion and retrieval

### Acceptance Criteria

- Agent answers portfolio questions using _retrieved_ chunks, not static context
- Answers include source citations
- Adding a new project to the DB + re-running ingester makes it immediately queryable
- Retrieval latency < 500ms

---

## Phase 2: Telegram Bot Integration (Priority: 🥈)

### Goal

Give the agent a second interface beyond the web widget. Users (including you) can chat with the agent on Telegram.

### What You'll Learn

- Telegram Bot API, webhooks vs polling
- Multi-transport agent architecture
- Message formatting for different channels

### Tasks

#### 2.1 — Create the Telegram Bot

- Talk to [@BotFather](https://t.me/botfather) to create a bot and get the token
- Add `TELEGRAM_BOT_TOKEN` to `env.ts` schema

#### 2.2 — Build the Telegram Transport Layer

- Install `node-telegram-bot-api` or use raw Telegram Bot API via `fetch`
- Create `backend/transports/telegram.ts`:
  - **Polling mode** for development (simpler, no HTTPS needed)
  - **Webhook mode** for production (set via `setWebhook` API)
  - Map incoming Telegram messages → `processUserMessage()` → send reply back
  - Use Telegram `chat.id` as the `sessionId` for memory continuity

#### 2.3 — Message Formatting

- Convert markdown responses to Telegram's `MarkdownV2` or `HTML` parse mode
- Handle long responses (Telegram has 4096 char limit) — split into multiple messages
- Support inline keyboards for confirmations ("Send this email? ✅ / ❌")

#### 2.4 — Command Handlers

- `/start` — welcome message explaining capabilities
- `/reset` — clear session memory
- `/status` — show active tasks/reminders
- `/help` — list available commands

### Deliverables

- `backend/transports/telegram.ts` — Telegram bot service
- `backend/transports/telegram.commands.ts` — command handlers
- Environment variable for bot token
- Works in both polling (dev) and webhook (prod) modes

### Acceptance Criteria

- Send a message on Telegram → get an agent response
- Session memory persists across Telegram messages
- `/reset` clears memory
- Agent can use all existing tools (GitHub, LeetCode, portfolio) via Telegram

---

## Phase 3: Email Agent (Priority: 🥉)

### Goal

Teach the agent to read, draft, and send emails. This is where the agent starts _doing things_ for you.

### What You'll Learn

- Gmail API / OAuth2 flow
- Multi-step tool orchestration
- Human-in-the-loop confirmation pattern
- Action vs read-only tools

### Tasks

#### 3.1 — Gmail API Setup

- Create a Google Cloud project, enable Gmail API
- Set up OAuth2 credentials (or use a service account for personal use)
- Store tokens securely; implement refresh logic
- Add `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` to env

#### 3.2 — Read Tools

- `read_inbox` — Fetch latest N unread emails, return sender, subject, snippet
- `read_email` — Fetch full email body by ID
- `search_emails` — Search by sender, subject, date range
- Create `backend/tools/email.read.tool.ts`

#### 3.3 — Write Tools

- `draft_email` — Create a draft (to, subject, body) — does NOT send
- `send_email` — Send a previously drafted email (requires explicit user confirmation)
- `reply_to_email` — Reply to an existing thread
- Create `backend/tools/email.write.tool.ts`

#### 3.4 — Summarization

- `summarize_inbox` — Use the LLM to summarize unread emails: "You have 3 important emails — one from X about Y..."
- Great use of chaining: tool fetches data → LLM summarizes

#### 3.5 — Confirmation Loop

- Before sending any email, the agent must present the draft and ask for confirmation
- On Telegram: use inline keyboard buttons (✅ Send / ✏️ Edit / ❌ Cancel)
- On web: show a confirmation card in the chat

### Deliverables

- `backend/tools/email.read.tool.ts`
- `backend/tools/email.write.tool.ts`
- `backend/services/gmail.service.ts` — Gmail API wrapper
- Confirmation UX for both web and Telegram

### Acceptance Criteria

- "Summarize my inbox" → returns summary of recent emails
- "Draft an email to X about Y" → shows draft in chat
- User confirms → email is sent
- Agent never sends an email without explicit approval

---

## Phase 4: MCP Server Architecture (Priority: High)

### Goal

Refactor tools into proper **Model Context Protocol** servers, learning the industry-standard pattern.

### What You'll Learn

- MCP protocol specification
- Tool server vs tool client architecture
- Dynamic tool discovery
- Composable, pluggable agent capabilities

### Tasks

#### 4.1 — Understand MCP

- Read the [MCP specification](https://modelcontextprotocol.io/)
- MCP defines a standard way for LLMs to discover and call tools
- Your agent becomes an **MCP client**, your tools become **MCP servers**

#### 4.2 — Create MCP Tool Servers

- **Portfolio MCP Server**: serves portfolio data, project search, profile info
- **GitHub MCP Server**: GitHub profile, repos, READMEs, activity
- **Email MCP Server**: Gmail read/write/search operations
- Each server is a standalone process that exposes tools via MCP protocol

#### 4.3 — MCP Client in Agent

- Replace hardcoded `agentTools` array with dynamic MCP tool discovery
- Agent queries available MCP servers → gets tool schemas → binds them
- Add/remove capabilities by starting/stopping MCP servers

#### 4.4 — Configuration

- Create `mcp.config.json` listing available servers and their endpoints
- Hot-reload: add a new MCP server without restarting the agent

### Deliverables

- `backend/mcp/servers/portfolio.server.ts`
- `backend/mcp/servers/github.server.ts`
- `backend/mcp/servers/email.server.ts`
- `backend/mcp/client.ts` — MCP client that discovers and binds tools
- `mcp.config.json` — server registry

### Acceptance Criteria

- Agent dynamically discovers tools from MCP servers
- Adding a new MCP server makes new tools available without code changes to the agent
- Existing functionality works identically through MCP

---

## Phase 5: Persistent Memory & Summarization

### Goal

Upgrade from simple chat history to intelligent, long-term memory.

### What You'll Learn

- Conversation summarization
- User preference extraction
- Memory distillation and retrieval

### Tasks

#### 5.1 — Improve DB Schema

- Add `agent_memory` table:
  ```
  id, user_key, type (preference|fact|task), content, confidence, source_session, created_at, updated_at
  ```
- Add `agent_message` table for per-message persistence (instead of serialized JSON blob):
  ```
  id, session_id, role, content, tool_calls, tokens_used, created_at
  ```

#### 5.2 — Conversation Summarization

- Every 15-20 messages, summarize the conversation using a cheap LLM call
- Store summary as a "memory" entry
- Use summaries as context for future sessions instead of raw message history

#### 5.3 — Preference Extraction

- After each conversation, extract user preferences:
  - "User prefers TypeScript over Python"
  - "User is interested in AI/ML"
  - "User's timezone is IST"
- Store in `agent_memory` with confidence scores
- Inject relevant memories into the system prompt

#### 5.4 — Privacy Controls

- Add opt-out flag per session
- Never persist sensitive data (passwords, tokens, personal IDs)
- Add `/forget` command to delete all stored memories

### Deliverables

- Updated Prisma schema with `agent_memory` and `agent_message` models
- `backend/core/summarizer.ts` — conversation summarizer
- `backend/core/memory.extractor.ts` — preference extraction
- Updated `memory.service.ts` with new capabilities

### Acceptance Criteria

- Agent recalls your preferences across sessions ("Last time you mentioned you prefer...")
- Conversations survive restarts with full fidelity
- `/forget` completely wipes memory

---

## Phase 6: Public API Integrations

### Goal

Expand the agent's toolbox with useful real-world APIs. Each integration is a new tool that teaches API patterns.

### What You'll Learn

- REST API integration patterns
- API key management
- Error handling for external services
- Data transformation for LLM consumption

### Tools to Add

| Tool | API | What It Does |
|---|---|---|
| `get_weather` | OpenWeatherMap | Current weather + forecast for any city |
| `get_news` | NewsAPI.org | Top headlines by category/country |
| `search_hackernews` | HN Algolia API | Search & trending stories (free, no key) |
| `search_wikipedia` | Wikipedia API | Knowledge lookup (free, no key) |
| `search_stackoverflow` | Stack Exchange API | Find answers to coding questions |
| `get_crypto_prices` | CoinGecko API | Crypto prices (free, no key) |
| `web_search` | SerpAPI / Tavily | General web search |
| `scrape_url` | Cheerio / Puppeteer | Read and summarize any web page |

### Implementation Pattern (per tool)

1. Create `backend/tools/<name>.tool.ts`
2. Define Zod schema for inputs
3. Fetch API → parse response → format human-readable output
4. Add error handling + timeout (10s)
5. Register in `tools/index.ts`

### Acceptance Criteria

- "What's the weather in Delhi?" → accurate current weather
- "Summarize today's tech news" → relevant headlines
- "What's trending on Hacker News?" → top 5 stories with links
- Each tool handles API failures gracefully

---

## Phase 7: Task & Note Management

### Goal

Give the agent personal productivity capabilities — todos, reminders, notes.

### What You'll Learn

- CRUD tool design
- Scheduled actions (reminders)
- Persistent user data management

### Tasks

#### 7.1 — DB Models

```prisma
model Task {
  id          String   @id @default(cuid())
  title       String
  description String?
  status      String   @default("pending")  // pending, in_progress, done
  priority    String   @default("medium")    // low, medium, high, urgent
  dueDate     DateTime?
  tags        String?  // JSON array
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model Note {
  id        String   @id @default(cuid())
  title     String
  content   String
  tags      String?  // JSON array
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

#### 7.2 — Task Tools

- `add_task` — Create a task ("Remind me to review PRs tomorrow")
- `list_tasks` — List pending tasks, optionally filter by status/priority
- `complete_task` — Mark a task as done
- `delete_task` — Remove a task

#### 7.3 — Note Tools

- `save_note` — Save a note with title and content
- `search_notes` — Full-text search across notes
- `list_notes` — List recent notes

#### 7.4 — Reminders (Optional)

- Use `node-cron` or `bull` queue for scheduled reminders
- "Remind me to call John in 2 hours" → schedule a message delivery

### Acceptance Criteria

- "Add to my todo: finish the RAG module by Friday" → task created
- "What's on my task list?" → formatted list with priorities
- "Done with the RAG module" → task marked complete

---

## Phase 8: LangGraph Migration (Advanced)

### Goal

Replace the simple while-loop agent with a proper LangGraph state machine for complex workflows.

### What You'll Learn

- LangGraph nodes, edges, and conditional routing
- Agent state management
- Checkpointing and human-in-the-loop
- Parallel tool execution
- Sub-agent orchestration

### Tasks

#### 8.1 — Define the Agent Graph

```
START → route_intent → [tool_node | direct_reply | multi_step_workflow]
tool_node → should_continue? → [tool_node | synthesize_reply]
multi_step_workflow → [email_flow | task_flow | research_flow]
synthesize_reply → END
```

#### 8.2 — Implement State

- Define `AgentState` interface with: messages, current_tools, metadata, step_count
- Use LangGraph's built-in checkpointer for persistence
- Replace `memory.service.ts` with LangGraph memory

#### 8.3 — Intent Router

- First node classifies intent: simple_qa, tool_use, multi_step, clarification_needed
- Route to appropriate sub-graph based on intent
- Simple queries skip the tool loop entirely (faster, cheaper)

#### 8.4 — Human-in-the-Loop

- For dangerous actions (send email, delete data), pause execution
- Wait for user confirmation before proceeding
- Use LangGraph's `interrupt` mechanism

### Deliverables

- `backend/graph/agent.graph.ts` — main graph definition
- `backend/graph/nodes/` — individual node implementations
- `backend/graph/state.ts` — state definition
- Migration from `agent.service.ts` to graph-based flow

### Acceptance Criteria

- Same functionality as before but via LangGraph
- Complex workflows (email draft → review → send) work as multi-step graphs
- Human-in-the-loop confirmation works for sensitive actions

---

## Phase 9: WhatsApp Integration

### Goal

Add WhatsApp as a third transport channel.

### What You'll Learn

- Twilio / Meta WhatsApp Business API
- Webhook verification
- Media message handling

### Tasks

#### 9.1 — API Setup

- **Option A**: Twilio WhatsApp Sandbox (free for dev)
- **Option B**: Meta WhatsApp Business Cloud API (free tier: 1000 messages/month)
- Configure webhook endpoint

#### 9.2 — Transport Layer

- Create `backend/transports/whatsapp.ts`
- Map incoming WhatsApp messages → `processUserMessage()` → reply
- Use phone number as session identifier
- Handle text, image, document messages

#### 9.3 — Rich Messaging

- Use WhatsApp interactive messages: buttons, lists, quick replies
- Format agent responses for mobile readability

### Acceptance Criteria

- Send a WhatsApp message → get agent response
- Session memory works across messages
- Rich formatting and buttons for confirmations

---

## Phase 10: Calendar & Scheduling

### Goal

Integrate Google Calendar for scheduling and availability management.

### What You'll Learn

- Google Calendar API, OAuth2
- Date/time handling and timezone awareness
- Booking workflows

### Tasks

- Set up Google Calendar API + OAuth2
- `check_availability` — Show free slots for a given date/range
- `create_event` — Book a meeting (title, time, attendees, description)
- `list_events` — Show upcoming events
- `cancel_event` — Cancel an existing event
- Timezone handling (user's timezone from memory or explicit)

### Acceptance Criteria

- "Am I free tomorrow at 3pm?" → accurate availability check
- "Schedule a meeting with X on Friday at 2pm" → event created, confirmation shown
- "What's on my calendar this week?" → formatted event list

---

## Phase 11: Multi-Mode Agent

### Goal

Allow switching between specialized behavior modes.

### Modes

| Mode | Behavior | Tools Available |
|---|---|---|
| **Portfolio** | Strict factual answers about your work | portfolio, github, leetcode |
| **Recruiter** | Highlight skills, pitch achievements | portfolio, github, contact |
| **Assistant** | Full personal ops | all tools |
| **Research** | Web search, summarization | web_search, scrape, wikipedia, news |

### Tasks

- Add `mode` parameter to request payload
- Create separate system prompt templates per mode
- Limit available tools per mode
- UI toggle or `/mode` command to switch

### Acceptance Criteria

- Mode switch changes agent behavior predictably
- Tool availability is correctly scoped per mode

---

## Phase 12: Reliability, Observability & Safety

### Goal

Make the agent production-grade.

### Tasks

#### Structured Logging & Observability
- Request tracing with unique request IDs
- Tool call latency tracking
- LLM token usage monitoring
- Dashboard-ready metrics (Prometheus / Grafana compatible)

#### Error Handling
- Circuit breaker for external API failures
- Graceful degradation: if a tool fails, agent explains and continues
- Retry logic with exponential backoff for transient failures

#### Prompt Injection Defenses
- Validate tool arguments against allow-lists
- Strip tool output from direct user echo
- Input sanitization for user messages
- System prompt protection

#### Rate Limiting
- Per-IP, per-session, per-user rate limits
- Token budget tracking per session and globally

### Acceptance Criteria

- Agent continues to respond under partial failures
- No tool misuse or prompt injection bypass
- Rate limits enforced without breaking UX

---

## Phase 13: UX & Product Polish

### Goal

Make the assistant feel premium and purposeful.

### Tasks

- **Suggestion chips**: Quick-action buttons below messages ("Show my projects", "Check GitHub")
- **Session panel**: View conversation history, manage sessions, clear memory
- **Onboarding flow**: First message explains capabilities and limitations
- **Rich reply cards**: Project cards with images, CTA buttons for calls, icon links
- **Typing indicators**: Show what the agent is doing ("Searching GitHub...", "Drafting email...")
- **Dark/light theme** with smooth transitions

### Acceptance Criteria

- User can discover features without reading documentation
- Responses are visually rich and formatted

---

## Phase 14: Cost & Performance Optimizations

### Goal

Reduce latency and cost without losing quality.

### Tasks

- **Model routing**: Use cheap/fast model for simple queries, primary model for complex tasks
- **Cache layer**: Cache embeddings and retrieval results for popular queries (Redis or in-memory)
- **Token trimming**: Limit conversation context via summarization before sending to LLM
- **Streaming responses**: Stream LLM output to frontend for perceived speed
- **Connection pooling**: Reuse HTTP connections for external APIs

### Acceptance Criteria

- Average response time < 4 seconds
- Costs reduced by 30-50% via smart routing
- Streaming enabled on web and Telegram

---

## Phase 15: Public vs Private Agent Split (Optional)

### Goal

Keep a safe public portfolio agent while running a powerful private personal agent.

### Tasks

- **Authentication**: Private agent requires login (JWT or session-based)
- **Public agent**: Safe, factual, limited tools (portfolio, GitHub, contact)
- **Private agent**: Full personal ops (email, calendar, tasks, all integrations)
- **Dual deployment**: Separate environment configs for public/private

### Acceptance Criteria

- Public agent remains safe — no access to personal data
- Private agent has full capabilities behind auth
- Same codebase, different configs

---

# Execution Plan (Recommended Order)

Ordered by **learning value** and **dependency chain**:

| Order | Phase | Est. Time | Key Skill |
|---|---|---|---|
| 1️⃣ | Phase 1: True RAG | 5-7 days | Embeddings, vector stores, retrieval |
| 2️⃣ | Phase 2: Telegram Bot | 2-3 days | Multi-transport, webhooks |
| 3️⃣ | Phase 3: Email Agent | 5-7 days | Gmail API, tool orchestration, confirmation UX |
| 4️⃣ | Phase 5: Memory & Summarization | 3-4 days | LangChain memory, preference extraction |
| 5️⃣ | Phase 6: Public API Tools | 3-4 days | API integration patterns (quick wins) |
| 6️⃣ | Phase 7: Task Management | 2-3 days | CRUD tools, personal productivity |
| 7️⃣ | Phase 4: MCP Architecture | 4-5 days | MCP protocol, dynamic tool discovery |
| 8️⃣ | Phase 8: LangGraph | 5-7 days | State machines, advanced orchestration |
| 9️⃣ | Phase 12: Reliability & Safety | 3-4 days | Production hardening |
| 🔟 | Phase 9-11, 13-15 | Ongoing | Polish, additional transports, optimization |
