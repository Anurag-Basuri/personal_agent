# Personal Agent 2.0 Roadmap

This roadmap upgrades the current portfolio agent into a robust, extensible personal agent. It is structured as phases with deliverables, implementation steps, and acceptance criteria. Follow in order for lowest risk.

## Phase 0: Project Baseline (1-2 days)

### Goal

Capture the current system state, define scope, and prevent regressions.

### Tasks

1. Document current architecture
   - Backend: agent flow, tools, memory, prompts, and data sources.
   - Frontend: widget, session flow, message rendering.
2. Define target capabilities
   - Personal ops (email, calendar, task management, CRM).
   - Deep knowledge (portfolio + resume + blog + GitHub + external docs).
   - Operational constraints (cost, latency, privacy).
3. Establish QA checklist
   - Cold start: first response within 3-5s.
   - Tool call success rate > 95%.
   - Safe failure messaging.

### Deliverables

- One-page architecture diagram (text-based OK).
- Capability list with priorities.
- QA checklist.

### Acceptance

- You can explain the flow end-to-end and measure baseline latency/cost.

---

## Phase 0.5: Platform Bootstrap (Next.js + Node/Express) (2-4 days)

### Goal

Make the frontend and backend work end-to-end in the requested stack before adding advanced features.

### Tasks

1. Frontend (Next.js)
   - Create a Next.js app for the UI layer.
   - Reuse existing widget components and hook logic.
   - Add API client pointing to the Express server.
2. Backend (Node + Express)
   - Create Express app with /chat and /chat/reset routes.
   - Wire up the existing agent service and tools.
   - Add environment config and health route.
3. Wiring and local run
   - Enable CORS for the Next.js origin.
   - Add dev scripts to run frontend and backend together.

### Deliverables

- Next.js frontend working locally.
- Express backend working locally.
- Chat flow from UI -> API -> LLM -> response.

### Acceptance

- You can send messages in the UI and receive responses from the backend.
- Reset clears session memory without errors.

---

## Phase 1: Persistent Memory and Conversation History (3-5 days)

### Goal

Move from in-memory session history to database-backed memory and long-term personalization.

### Tasks

1. Create DB tables
   - `agent_session`: id, user_key, created_at, last_seen_at.
   - `agent_message`: id, session_id, role, content, tokens, created_at.
   - `agent_memory`: id, user_key, type, content, confidence, updated_at.
2. Implement message persistence
   - Save all user and assistant messages.
   - Load the last N messages per session.
3. Add summarization and memory distillation
   - Every 10-15 messages, summarize the session.
   - Extract user preferences into `agent_memory`.
4. Privacy controls
   - Do not store sensitive data unless user approves.
   - Add an explicit memory opt-out flag.

### Deliverables

- Prisma models and migration.
- Memory service using DB.
- Summarizer utility.

### Acceptance

- Conversations survive server restarts.
- Agent recalls preferences after refresh.

---

## Phase 2: True RAG Over Portfolio Content (5-7 days)

### Goal

Replace static profile context with dynamic retrieval over real portfolio data.

### Tasks

1. Build a content indexer
   - Sources: projects, resume, blogs, case studies, GitHub READMEs.
   - Extract clean text and metadata.
2. Vector store setup
   - Choose pgvector (recommended) or external vector DB.
   - Store embeddings with source metadata.
3. Retrieval pipeline
   - Query -> embed -> top-k chunks -> context assembly.
   - Add re-ranking if needed.
4. Prompt upgrades
   - Provide retrieved chunks with source tags.
   - Force grounded answers only.

### Deliverables

- Indexer script.
- Vector store schema.
- Retrieval module and tests.

### Acceptance

- Agent can answer portfolio questions using real content.
- Answers cite which source was used.

---

## Phase 3: Tooling for Personal Ops (7-12 days)

### Goal

Enable tasks beyond Q&A: scheduling, emailing, and lead handling.

### Tools to Add

1. Calendar scheduling
   - Integrate Calendly or Google Calendar API.
   - Provide available slots + book meetings.
2. Email assistant
   - Draft or send emails via provider (Resend/SendGrid).
   - Use confirmation step before sending.
3. CRM-lite pipeline
   - Track contacts, status, next follow-up.
   - Store in DB for future conversation continuity.
4. Task capture
   - Save action items ("follow up next week", "send resume").

### Deliverables

- New tool modules.
- DB models for contact and task pipeline.
- Confirmation UX in chat.

### Acceptance

- Agent can schedule a call and send a confirmation email.
- Agent creates follow-up tasks automatically.

---

## Phase 4: Multi-Mode Agent (3-5 days)

### Goal

Allow switching between modes for specialized behavior.

### Modes

- Portfolio Mode: strict factual responses.
- Recruiter Mode: highlight skills and results.
- Consultant Mode: problem-solving and guidance.
- Interview Prep Mode: coaching and Q&A.

### Tasks

1. Add `mode` to request payload.
2. Create separate system prompt templates.
3. Limit tools per mode.

### Deliverables

- Mode-aware prompt builder.
- UI toggle or quick-command to switch.

### Acceptance

- Behavior changes predictably by mode.

---

## Phase 5: Reliability, Observability, and Safety (4-6 days)

### Goal

Make the agent production-grade and safe.

### Tasks

1. Add structured logging
   - Capture request id, tool use, latency, errors.
2. Error handling and fallback
   - Circuit breaker for tool failures.
   - Safe user messaging when providers fail.
3. Prompt injection defenses
   - Strip tool output from direct user echo.
   - Validate tool args and enforce allow-list behavior.
4. Rate limits and quotas
   - Per IP + per session + per user.

### Deliverables

- Logging middleware.
- Error taxonomy with clean messages.
- Tool safety guard.

### Acceptance

- Agent continues to respond under partial failures.
- No tool misuse or policy bypass.

---

## Phase 6: UX and Product Polish (3-5 days)

### Goal

Make the assistant feel premium and purposeful.

### Tasks

1. Add suggestions row
   - Quick questions and actions.
2. Session panel
   - View history and reset memory easily.
3. Onboarding
   - First message explains capabilities and limits.
4. Reply formatting
   - Cards for projects, buttons for calls, links with icons.

### Deliverables

- Updated widget UI.
- Interaction patterns for quick actions.

### Acceptance

- User can discover features without reading docs.

---

## Phase 7: Cost and Performance Optimizations (2-4 days)

### Goal

Reduce latency and cost without losing quality.

### Tasks

1. Model routing
   - Use cheaper model for simple queries.
   - Use main model for complex tasks.
2. Cache retrieval results
   - Cache embeddings and top-k hits for popular queries.
3. Token trimming
   - Limit conversation length with summarization.

### Deliverables

- Model router.
- Cache layer.

### Acceptance

- Average response time < 4s.
- Costs reduced by 30-50%.

---

## Phase 8: Public vs Private Agent Split (Optional)

### Goal

Keep a public portfolio agent while creating a private personal agent.

### Tasks

1. Separate environments
   - Public: safe, factual, limited tools.
   - Private: full personal ops and automation.
2. Authentication
   - Private agent requires login.

### Deliverables

- Dual deployment config.
- Access control layer.

### Acceptance

- Public agent remains safe, private agent remains powerful.

---

# Execution Plan (Suggested Order)

1. Phase 1 (Memory) + Phase 2 (RAG)
2. Phase 3 (Personal Ops)
3. Phase 5 (Reliability + Safety)
4. Phase 6 (UX polish)
5. Phase 7 (Cost optimization)
6. Phase 4 and Phase 8 (Modes and Private split)

---

# What You Need From Me Next

1. Confirm which tools you want first (calendar, email, CRM, tasks).
2. Confirm your hosting and DB stack (Postgres + Prisma recommended).
3. Confirm if you want a private agent login.

Once you confirm, I will produce a phase-by-phase implementation checklist with actual code changes and file-by-file steps.
