# AI Infrastructure Advisor — Application & Repository Guide

This document consolidates an end-to-end description of the **AI_tech_aggregator** repository: what the product is, how it is implemented, which services exist and what they do, user-facing features, known limitations, mitigations, and a structured way to study the codebase (including a time-boxed plan). Use it as a single reading path to understand the project without opening every file.

---

## Table of contents

1. [What this application is](#1-what-this-application-is)
2. [Repository layout](#2-repository-layout)
3. [System architecture](#3-system-architecture)
4. [End-to-end data flows](#4-end-to-end-data-flows)
5. [Backend services and their roles](#5-backend-services-and-their-roles)
6. [Agent implementation](#6-agent-implementation)
7. [Module system and database](#7-module-system-and-database)
8. [Frontend architecture](#8-frontend-architecture)
9. [REST API surface](#9-rest-api-surface)
10. [Authentication and configuration](#10-authentication-and-configuration)
11. [Supporting packages (SDK, CLI, MCP)](#11-supporting-packages-sdk-cli-mcp)
12. [Features checklist](#12-features-checklist)
13. [Limitations, risks, and mitigations](#13-limitations-risks-and-mitigations)
14. [How to study the repo efficiently](#14-how-to-study-the-repo-efficiently)
15. [Key files reference](#15-key-files-reference)
16. [One-page brief for a lead (template)](#16-one-page-brief-for-a-lead-template)
17. [Related documentation in this repo](#17-related-documentation-in-this-repo)

---

## 1. What this application is

### 1.1 Elevator pitch

**AI Infrastructure Advisor** is a platform that helps people choose and reason about **AI/ML infrastructure** (vector databases, embeddings, RAG patterns, LLMs, agents, evaluation tools, etc.). The knowledge base is a **catalog of “modules”**—each module is a real-world technology or pattern, described in **YAML**, loaded into **PostgreSQL**. Users interact primarily through an **AI chat advisor** that can search the catalog, compare options semantically or by scores, and drive a **visual panel** (architecture diagrams, comparison charts/tables, code snippets, interactive option cards, multi-file code projects).

### 1.2 Problem it solves

- **Discovery:** Many teams do not know which tools fit which stage of a pipeline (ingestion → chunking → embeddings → vector store → retrieval → LLM → evaluation → deployment).
- **Comparison:** Side-by-side comparison across consistent dimensions (performance, cost, maturity, etc.) reduces ad-hoc Googling.
- **Guidance:** The advisor combines structured DB data with an LLM to explain trade-offs and suggest stacks.

### 1.3 Tech stack summary

| Layer | Technologies |
|--------|----------------|
| Frontend | Next.js 16 (App Router, Turbopack), React 19, TypeScript, Tailwind CSS, Zustand, next-auth |
| Backend | Python 3.13, FastAPI, SQLAlchemy async, Alembic, PostgreSQL 16 + pgvector, Redis |
| LLM | Anthropic Claude (via **Claude Code CLI** or **Anthropic Messages API** with tools) |
| Embeddings (optional) | OpenAI API for vector search over `module_knowledge` |
| Infra (local) | `docker-compose.yml`: Postgres (mapped to host port **5433**), Redis **6379** |

---

## 2. Repository layout

| Path | Purpose |
|------|---------|
| `frontend/` | Next.js app: pages, BFF route `/api/chat`, components, Zustand stores |
| `backend/` | FastAPI app: REST + SSE, agent, services, models, tests |
| `modules_registry/specs/` | One YAML file per technology/module |
| `modules_registry/schema.yaml` | JSON-schema-style contract for specs |
| `scripts/` | Operational scripts: `seed_db.py`, `generate_embeddings.py`, `generate_module.py` |
| `sdk/` | Python HTTP client (`ai_advisor`) for the public API |
| `cli/` | Command-line entry point wrapping SDK-style usage |
| `mcp_server/` | MCP (stdio JSON-RPC) server exposing a subset of API as tools |
| `docs/` | Architecture notes, API reference, module guide, UI design, plans |
| `AGENTS.md` | Cursor/agent team prompts: conventions, ports, critical chat flow |
| `docker-compose.yml` | Local Postgres + Redis |

**Note:** You do not need to read every file under `modules_registry/specs/` to understand the app; read **one representative spec** plus `schema.yaml` and the loader.

---

## 3. System architecture

### 3.1 High-level diagram (logical)

```
                    +-----------------+
                    |   Next.js 16    |
                    |   Frontend      |
                    |   (port 3000)   |
                    +--------+--------+
                             |
                    BFF POST /api/chat
                             |
                    +--------v--------+
                    |   FastAPI       |
                    |   Backend       |
                    |   (port 8000)   |
                    +---+--------+---+
                        |        |
              +---------+        +------------------+
              |                                   |
     +--------v--------+                +---------v---------+
     |  PostgreSQL 16   |                |  Claude           |
     |  + pgvector      |                |  (CLI or API)     |
     +------------------+                +-------------------+
              |
     +--------v--------+
     |  Redis (cache)   |
     +------------------+
```

### 3.2 Component responsibilities

- **Next.js** renders the UI, holds client state (Zustand), and proxies authenticated chat to the backend without exposing API keys to the browser for backend-only secrets.
- **FastAPI** owns persistence (conversations, messages, modules), business rules (comparison, module listing), and the **SSE** streaming contract.
- **PostgreSQL** stores modules, categories, knowledge (with optional embeddings), users, conversations, messages, benchmarks, comparisons cache, etc.
- **Redis** caches expensive read paths (e.g. module list responses).
- **Claude** reasons over user messages and (in SDK mode) calls **tools** that read/write logical results and emit **panel commands** for the UI.

---

## 4. End-to-end data flows

### 4.1 Chat flow (primary user journey)

1. User types in the advisor UI; **`chatStore`** (`frontend/src/stores/chatStore.ts`) appends a user message and creates an empty assistant message.
2. Client **`POST /api/chat`** with JSON `{ message, session_id }` and `Authorization` header.
3. Next.js **BFF** (`frontend/src/app/api/chat/route.ts`) forwards to **`POST {BACKEND_URL}/api/v1/advisor/chat`** with the same body and auth header.
4. **`ChatService`** (`backend/src/services/chat_service.py`):
   - Resolves or creates a **`Conversation`** by `session_id` (UUID) or creates new.
   - Persists the user **`Message`**.
   - Builds Claude message list from prior messages (text only in history).
   - Loads module/category counts and a **catalog section** (categories + module slugs) for the system prompt.
   - Emits first SSE event: **`meta`** with `session_id`.
   - Instantiates **`AdvisorAgent`** and streams all agent SSE events through.
   - On completion (or partial failure), persists assistant **`Message`** with accumulated text and **`panel_commands`** array.

5. Client parses each `data: {...}` line:
   - **`text`** → append to assistant bubble.
   - **`panel_command`** → attach to message and call **`panelStore.renderPanel(command)`**.
   - **`meta`** → store `session_id` for thread continuity.
   - **`tool_activity`** (SDK path) → show running/complete tool indicators on the assistant message.
   - **`done`** → stream finished.
   - **`error`** → surfaced as error content.

### 4.2 Panel command protocol (contract between backend and UI)

Backend emits Server-Sent Events. Payload types include:

| Type | Role |
|------|------|
| `meta` | `{ session_id }` — client should reuse for the same conversation |
| `text` | Streamed assistant tokens |
| `panel_command` | `{ command: { action, panel, data?, title? } }` — drives right-hand panel |
| `tool_activity` | `{ tool, status: running\|complete, message? }` |
| `done` | Stream complete |
| `error` | Error string for display/logging |

**Panel command shape (conceptual):**

- `action: "render"` — switch panel type and replace panel data (history stack in `panelStore`).
- `action: "update"` — incremental updates (e.g. interactive architecture: add node, add edge, highlight).
- `action: "clear"` — reset to welcome panel.

**Panel types** used in code include: `welcome`, `architecture_diagram`, `comparison_chart`, `comparison_table`, `code_preview`, `option_cards`, `interactive_architecture`, `code_project`, plus placeholders for `module_detail`, `recommendation`, `document` in `MainPanel.tsx`.

### 4.3 Module content flow

```
modules_registry/specs/*.yaml
        │
        ▼
  loader.py (hash, upsert)
        │
        ▼
PostgreSQL: modules, module_knowledge, categories, benchmarks, ...
        │
        ▼
ModuleService + ComparisonEngine + agent tools + REST /modules
```

---

## 5. Backend services and their roles

### 5.1 FastAPI application

- **Entry:** `backend/src/main.py` — creates FastAPI app, CORS, rate limiter wiring, mounts **`api_v1_router`**.
- **Router aggregation:** `backend/src/api/v1/router.py` — prefixes all routes with `/api/v1`.

### 5.2 ChatService

**File:** `backend/src/services/chat_service.py`

- Owns **conversation lifecycle** and **message persistence**.
- Builds **Claude-compatible** history from DB (user/assistant text only).
- Injects **catalog** into the agent context via `build_catalog_section` / `ModuleService.list_categories_with_slugs`.
- **Does not** implement LLM logic itself — delegates to **`AdvisorAgent`**.

### 5.3 AdvisorAgent

**File:** `backend/src/agent/advisor.py`

- Chooses **Claude Code adapter** vs **Anthropic SDK** from settings.
- **SDK path:** streaming loop with **tools**; executes `_execute_tool`; emits SSE for text, tool activity, panel commands, done.
- **Claude Code path:** streams text and parses **`<!--PANEL_CMD:...-->`** markers into `panel_command` events (see `PANEL_COMMAND_INSTRUCTIONS` in the same file).
- Implements tool handlers: search modules, get detail, compare, search knowledge, list categories, render panels, benchmarks, suggest stack, present options, incremental architecture steps, code project.

### 5.4 ModuleService

**File:** `backend/src/services/module_service.py`

- **List/filter** modules (category, status, text search, pagination).
- **get_by_slug** with relationships (category, knowledge, integrations, benchmarks).
- **list_categories** / **list_categories_with_slugs** (for UI and system prompt).
- **search_knowledge:** tries **vector** search if embeddings can be generated; otherwise **ILIKE** fallback.

### 5.5 ComparisonEngine

**File:** `backend/src/modules/comparison_engine.py`

- Loads modules by slug; validates all exist.
- Reads **`comparison_scores`** (8 dimensions by default) from DB JSON.
- Produces **`ComparisonResult`**: per-dimension matrix, rankings, weighted overall ranking, highlights — used by REST `/compare` and agent tool `compare_modules`.

### 5.6 Module loader

**File:** `backend/src/modules/loader.py`

- Reads YAML from `modules_registry/specs/`.
- Computes **`spec_hash`** to skip unchanged files.
- Upserts **`Module`**, **`ModuleKnowledge`**, **`Benchmark`**, integrations, etc.

### 5.7 Core utilities

| Module | Role |
|--------|------|
| `backend/src/core/config.py` | Pydantic settings from env: DB, Redis, Anthropic, OpenAI, NextAuth, CORS, rate limits |
| `backend/src/core/security.py` | `get_current_user`: dev Bearer = email → auto user; prod NextAuth JWT |
| `backend/src/core/redis.py` | Cache get/set used by modules API |
| `backend/src/core/embeddings.py` | Embedding generation for knowledge search (when configured) |
| `backend/src/db/session.py` | Async SQLAlchemy session dependency **`get_db`** |

### 5.8 Agent tools (definitions)

**File:** `backend/src/agent/tools.py` — schemas for Claude **tool_use** (SDK mode). Tool names: `search_modules`, `get_module_detail`, `compare_modules`, `search_knowledge`, `list_categories`, `render_architecture_diagram`, `render_comparison`, `render_code_example`, `get_benchmarks`, `suggest_stack`, `present_options`, `build_architecture_step`, `render_code_project`.

---

## 6. Agent implementation

### 6.1 Dual-mode design

| Mode | Config | Behavior |
|------|--------|----------|
| Claude Code CLI | `USE_CLAUDE_CODE=true` (default in `Settings`) | Subprocess/adapter streams text; panel updates via HTML comment markers |
| Anthropic SDK | `USE_CLAUDE_CODE=false` + `ANTHROPIC_API_KEY` | Native tool loop, duplicate tool-call guard, `tool_activity` SSE |

**Endpoint guard:** `backend/src/api/v1/chat.py` returns **503** if not using Claude Code and API key is missing.

### 6.2 SDK tool loop (summary)

1. Stream one assistant turn with `tools=ALL_TOOLS`.
2. If response contains **`tool_use`** blocks, execute each via `_execute_tool`, append **`tool_result`** user message, repeat.
3. Max iterations (e.g. 25) to avoid infinite loops; duplicate identical tool calls are detected and short-circuited.
4. When no tools, emit **`done`**.

### 6.3 System prompt context

- **`build_system_prompt`** (`backend/src/agent/prompts.py`) receives module count, category count, and **catalog section** listing categories and slugs so the model knows what exists in the database.

---

## 7. Module system and database

### 7.1 YAML spec contents (conceptual)

Each spec aligns with `modules_registry/schema.yaml` and typically includes:

- **meta** — slug, version, category, status, etc.
- **identity** — name, tagline, description, links, pricing, license
- **capabilities** — use cases, operations
- **technical_specs** — structured fields
- **comparison_dimensions** — eight 1–10 scores with justifications
- **knowledge** — entries (embeddable text for RAG-style search)
- **code_examples**, **benchmarks**, **relationships** (alternatives, complements), **pipeline** position

### 7.2 Database (high level)

Described in `docs/architecture/README.md` and enforced by SQLAlchemy models under `backend/src/models/`:

- **modules** — core row + JSON for flexible fields
- **module_knowledge** — text + optional **pgvector** embeddings
- **module_categories** — taxonomy
- **conversations** / **messages** — chat history; messages store `panel_commands`
- **users** / **teams** — auth and tiers (dev user auto **pro**)
- **benchmarks** — numeric performance data
- **comparisons** — cached comparison results (where used)

**Migrations:** Alembic under `backend/alembic/`.

### 7.3 Seeding and maintenance scripts

| Script | Purpose |
|--------|---------|
| `scripts/seed_db.py` | Load/update YAML specs into DB (team workflow in `AGENTS.md`) |
| `scripts/generate_embeddings.py` | Populate embeddings for knowledge search |
| `scripts/generate_module.py` | AI-assisted generation of new specs (see `docs/modules/README.md`) |

---

## 8. Frontend architecture

### 8.1 Routing

- **`frontend/src/app/(public)/`** — marketing/explore/module pages, pricing, etc.
- **`frontend/src/app/(dashboard)/`** — authenticated-style shell: advisor, history, dashboard
- **`frontend/src/app/api/chat/route.ts`** — BFF proxy to FastAPI SSE

### 8.2 Layout pattern (advisor)

- **30/70 split:** chat column + **`MainPanel`** (see `AdvisorLayout` / advisor pages).
- **`MainPanel.tsx`** switches on **`usePanelStore.currentPanel`** to render the correct panel component.

### 8.3 State management

| Store | Responsibility |
|--------|------------------|
| `chatStore` | Messages, streaming chunks, session id, abort controller, tool activity list on messages |
| `panelStore` | Current panel type, data, title, history stack, `render` / `update` / `goBack` |

**Project rules (from `AGENTS.md`):** client components use `'use client'`; Tailwind only for styling; Zustand for this state (not Redux).

### 8.4 Implemented vs placeholder panels

**Fully wired panel types:** welcome, architecture_diagram, comparison_table, comparison_chart, code_preview, option_cards, interactive_architecture, code_project.

**Placeholder UI** (static text in `MainPanel.tsx`): `module_detail`, `recommendation`, `document` — types exist in the switch but are not full implementations.

---

## 9. REST API surface

Base URL: **`http://localhost:8000/api/v1`** (see `docs/api/README.md` for tables).

| Area | Prefix / path | Notes |
|------|----------------|-------|
| Health | `GET /health`, `GET /health/detailed` | DB + pgvector check on detailed |
| Auth | `/auth/login` (POST), `/auth/me` (GET) | Dev-oriented login; prod uses NextAuth |
| Modules | `/modules`, `/modules/categories`, `/modules/{slug}`, `/modules/{slug}/knowledge` | List uses Redis cache |
| Compare | `POST /compare` | Body: slugs, optional dimensions/weights |
| Chat | `POST /advisor/chat` | **SSE** stream, not JSON body response |
| Sessions | `GET /sessions`, `GET /sessions/{id}/messages` | Conversation history API |
| Users | `GET /users/me` | Profile / usage (per `docs/api/README.md`) |

---

## 10. Authentication and configuration

### 10.1 Development auth

- **`Authorization: Bearer <email>`** e.g. `Bearer dev@example.com`.
- Backend **`get_current_user`** (`backend/src/core/security.py`) creates a **pro-tier** user if missing.

### 10.2 Production auth

- Intended: **NextAuth JWT** validated with `fastapi-nextauth-jwt` and `NEXTAUTH_SECRET`.

### 10.3 Environment / ports

- **Docker Compose** exposes Postgres on host **5433** → container 5432.
- **Default `Settings.database_url`** in `backend/src/core/config.py` uses **localhost:5432** — local dev should set **`DATABASE_URL`** in `.env` to match Compose (**5433**) when using Docker.
- **Redis:** 6379.
- **Backend:** 8000; **Frontend:** 3000.

### 10.4 Critical env variables (conceptual)

- `ANTHROPIC_API_KEY` — required when `USE_CLAUDE_CODE=false`
- `USE_CLAUDE_CODE` — toggles Claude Code vs SDK
- `OPENAI_API_KEY` — enables embedding-based knowledge search
- `DATABASE_URL` / sync variant, `REDIS_URL`, `CORS_ORIGINS`, `NEXTAUTH_*`

---

## 11. Supporting packages (SDK, CLI, MCP)

### 11.1 Python SDK

**Path:** `sdk/src/ai_advisor/client.py` — **`AIAdvisorClient`**

- Sync HTTPX client against `/api/v1`.
- Methods include `list_modules`, `get_module`, `list_categories`, compare helpers (as exposed in client).

**Use case:** scripts, integrations, tests, or third-party apps that consume the REST API without the Next.js UI.

### 11.2 CLI

**Path:** `cli/src/ai_advisor_cli/` — thin wrapper for command-line access to advisor-related operations (entry in `main.py`).

### 11.3 MCP server

**Path:** `mcp_server/src/ai_advisor_mcp/server.py`

- JSON-RPC over **stdio** (minimal MCP implementation).
- Tool definitions: `list_modules`, `get_module`, `compare_modules`, `list_categories`.
- Uses **`AIAdvisorClient`** to call the backend.

**Use case:** attach the catalog to **Claude Code** or other MCP hosts without using the web UI.

---

## 12. Features checklist

### 12.1 User-facing (product)

- Browse/explore modules and categories (public routes + API).
- Chat with an **AI advisor** that reasons about infrastructure choices.
- **Streaming** answers with optional **tool activity** visibility (SDK mode).
- **Visual panel:** architecture graphs, comparisons (radar/bar/table), code preview, option cards, incremental interactive architecture, multi-file code project.
- **Conversation sessions** with persistence (backend conversations/messages; frontend stores `session_id` from SSE `meta`).
- **History / dashboard** routes exist under `(dashboard)` (implementation depth may vary—verify UI when demoing).

### 12.2 Platform / API

- RESTful module catalog with pagination and filters.
- Programmatic **compare** endpoint.
- Health checks for ops.
- Rate limiting middleware wired in FastAPI app (limits configured in settings).

### 12.3 Content operations

- Large library of YAML specs under `modules_registry/specs/`.
- Loader supports **idempotent** updates via content hash.
- Optional embedding pipeline for semantic knowledge retrieval.

---

## 13. Limitations, risks, and mitigations

| Limitation | Why it matters | Mitigation direction |
|------------|----------------|----------------------|
| **Two agent backends** (Claude Code vs SDK) | Behavior and capabilities differ (markers vs tools); harder to test one path and assume the other | Document which mode is “canonical” for prod; add integration tests per mode; align prompts |
| **Chat history for Claude is text-only** | Past `panel_commands` are stored on messages but not replayed into the model context in `_build_claude_messages` | Optionally inject summarized panel state or last N commands into prompts |
| **Placeholder panels** (`module_detail`, `recommendation`, `document`) | User sees stub UI if agent targets those panel types | Implement components or restrict agent from emitting those types until ready |
| **Dev auth is not production security** | Easy local testing but must not ship as-is | Enforce JWT path in prod; remove or protect dev login endpoints |
| **DB port default vs Docker** | Misconfiguration causes connection errors | Standardize `.env.example` on 5433 for Compose; document in README |
| **Knowledge search without embeddings** | Weaker retrieval (ILIKE fallback) | Run `generate_embeddings.py` when OpenAI key available; monitor quality |
| **suggest_stack heuristic** | Picks “first/top” modules per category with simple budget bias—not a full recommender | Replace with scored retrieval, user constraints, or dedicated tool + tests |
| **Large YAML corpus** | Impossible to “read all specs” in onboarding | Rely on schema + loader + one exemplar spec + category list |
| **MCP/SDK scope** | Smaller than full agent tool surface | Document which features are API-only vs MCP-only |

---

## 14. How to study the repo efficiently

This section expands the **time-boxed learning plan** (~2.5 hours) into actionable steps with **what to extract** at each step.

### 14.1 Phase A — First 15 minutes (orientation)

| Step | Read | Extract to your notes |
|------|------|------------------------|
| A1 | `AGENTS.md` | Ports, stack, chat flow summary, panel JSON example |
| A2 | `docs/architecture/README.md` | Diagram, agent loop, SSE types, module pipeline |
| A3 | `docker-compose.yml` | Service names, ports, volumes |

**Outcome:** You can explain the system in **2 minutes** without code.

### 14.2 Phase B — ~45 minutes (implementation spine)

| Step | Path(s) | Extract |
|------|---------|---------|
| B1 | `chatStore.ts` → `api/chat/route.ts` → `chat.py` → `chat_service.py` → `advisor.py` | Ordered list of functions/classes hit per request |
| B2 | `tools.py` + `advisor._execute_tool` | Table: tool name → what it does |
| B3 | `schema.yaml` + one spec file + `loader.py` (start) | Required YAML sections; loader upsert rules |
| B4 | `router.py` + skim each `api/v1/*.py` | Endpoint list |

**Outcome:** You can **draw** request/response and SSE on a whiteboard.

### 14.3 Phase C — ~45 minutes (frontend + docs)

| Step | Path(s) | Extract |
|------|---------|---------|
| C1 | `frontend/src/app/` tree | Public vs dashboard routes |
| C2 | `MainPanel.tsx` | Panel switch + which are placeholders |
| C3 | `panelStore.ts` | `render` vs `update` vs `goBack` |
| C4 | `docs/api/README.md`, `docs/modules/README.md` | Auth rules, endpoint tables, module workflow commands |

**Outcome:** You know **what users see** and **what is stubbed**.

### 14.4 Phase D — ~30 minutes (quality + gaps)

| Step | Action | Extract |
|------|--------|---------|
| D1 | List `backend/tests/`, `frontend/src/__tests__/` | What behavior is explicitly tested |
| D2 | Search codebase for `TODO`, `FIXME`, `placeholder` | Quick gap list |
| D3 | Re-read `chat.py` 503 guard, `config.py` defaults | Ops and env pitfalls |

**Outcome:** Credible **limitations** slide for your lead.

### 14.5 Mindset

- **Depth** on chat + modules + panels; **breadth** on routers and stores.
- It is acceptable to say you mapped architecture and flows without memorizing every module slug.

---

## 15. Key files reference

| Topic | File |
|--------|------|
| FastAPI app | `backend/src/main.py` |
| API mount | `backend/src/api/v1/router.py` |
| SSE chat endpoint | `backend/src/api/v1/chat.py` |
| Chat orchestration | `backend/src/services/chat_service.py` |
| Agent + tools execution | `backend/src/agent/advisor.py` |
| Tool schemas | `backend/src/agent/tools.py` |
| System prompt helpers | `backend/src/agent/prompts.py` |
| Claude Code adapter | `backend/src/agent/claude_code_adapter.py` |
| Module CRUD/search | `backend/src/services/module_service.py` |
| YAML → DB | `backend/src/modules/loader.py` |
| Compare logic | `backend/src/modules/comparison_engine.py` |
| Settings | `backend/src/core/config.py` |
| Auth | `backend/src/core/security.py` |
| Chat BFF | `frontend/src/app/api/chat/route.ts` |
| Chat UI state | `frontend/src/stores/chatStore.ts` |
| Panel UI state | `frontend/src/stores/panelStore.ts` |
| Panel router UI | `frontend/src/components/advisor/MainPanel.tsx` |
| Team conventions | `AGENTS.md` |

---

## 16. One-page brief for a lead (template)

Copy and fill after your read-through:

1. **Purpose:** (2 sentences — what problem, for whom.)
2. **Architecture:** (5 bullets or one diagram — Next → BFF → FastAPI → DB/Redis/Claude.)
3. **Main features:** (bullets — chat, panels, catalog, compare, sessions.)
4. **Key dependencies:** (Postgres+pgvector, Redis, Anthropic, optional OpenAI embeddings.)
5. **Risks / limitations:** (3–5 bullets from section 13.)
6. **Open questions:** (what you would clarify with the team next.)

---

## 17. Related documentation in this repo

| Document | Content |
|----------|---------|
| `AGENTS.md` | Agent team prompts, ports, panel SSE example |
| `docs/architecture/README.md` | Short architecture overview |
| `docs/api/README.md` | REST + SSE endpoint reference |
| `docs/modules/README.md` | Adding specs, validation, `generate_module.py`, categories |
| `docs/UI_design.md` | UI design notes |
| `docs/superpowers/plans/*.md` | Planning docs for launches and panels |

---

*This guide was produced to mirror the structure of the onboarding answers in the project chat: full application overview, services, features, limitations, and a time-boxed study plan—all in one place.*
