# AI Infrastructure Advisor Platform

**Canonical copy:** Mirrors `CLAUDE.md` at the repo root; keep both in sync.

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker Desktop (for PostgreSQL + pgvector + Redis)
- Claude Code CLI (for local dev with Max subscription) **or** `ANTHROPIC_API_KEY` with `USE_CLAUDE_CODE=false`

### Setup
```bash
# Start database + Redis
docker-compose up -d

# Backend
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env: ANTHROPIC_API_KEY and/or USE_CLAUDE_CODE=true; EMBEDDINGS_ENABLED=true for semantic intent
python ../scripts/seed_db.py
uvicorn src.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Key URLs
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Architecture

### Monorepo Layout
```
frontend/              Next.js 16 App Router (TypeScript, Tailwind v4, Zustand)
backend/               Python FastAPI (SQLAlchemy async, Alembic)
  src/agent/           LLM agent — dual-mode (Claude Code CLI or Anthropic SDK)
  src/api/v1/          REST + SSE endpoints
  src/services/        Chat, planner, pipelines, scoring, semantic intent
  src/advisor_playbooks/   Playbook definitions (YAML)
  src/advisor_registry/    Decision metadata + comparison universe (YAML)
  src/advisor_intent/      Intent exemplars (YAML)
  src/models/          SQLAlchemy ORM
  src/modules/         Module loader + comparison engine
modules_registry/      102 YAML specs (source of truth for modules)
scripts/               seed_db, generate_embeddings, sync_decision_metadata, scaffold specs
sdk/ cli/ mcp_server/  API clients and MCP integration
```

### Core Pattern: Planner + Agent-Driven Panel

Chat is **not** LLM-only. Each turn:

1. **Semantic intent** (BGE embeddings vs exemplars in `advisor_intent/registry.yaml`) may ask for clarification.
2. **`RecommendationPlanner`** runs deterministic **playbooks** and **pipelines** (vector DB compare, RAG design, module code, architecture review, local AI stack, category comparison).
3. Pipelines emit SSE **`text`** and **`panel_command`** events with scored shortlists and **`advisor_trace`** for explainability.
4. If the planner produces no events and `llm_fallback_enabled`, **`AdvisorAgent`** streams (tools in SDK mode; panel markers in Claude Code mode). LLM panel commands are **restricted** when a playbook is active (`planner_authority_strict`).

SSE event types:
| Type | Role |
|------|------|
| `meta` | `session_id`, `constraint_state`, `advisor_trace`, `recommendation_explain`, intent fields |
| `text` | Streamed assistant text |
| `panel_command` | Right-hand panel update |
| `tool_activity` | Tool progress (SDK mode) |
| `done` | Stream finished |
| `error` | Error payload |

### Module Pattern
Every module is a YAML spec in `modules_registry/specs/{slug}.yaml` validated against `modules_registry/schema.yaml`. The loader (`backend/src/modules/loader.py`) reads specs into PostgreSQL and merges **decision metadata** from `backend/src/advisor_registry/`.

### API Endpoints (`/api/v1`)

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/advisor/chat` | SSE streaming chat (auth required) |
| `GET` | `/advisor/playbooks` | List playbooks + Phase-2 flags |
| `GET` | `/advisor/trace/schema` | JSON schema for advisor trace |
| `GET` | `/advisor/sessions/{id}/trace/latest` | Latest trace from session messages |
| `GET` | `/modules` | Paginated list (Redis cache) |
| `GET` | `/modules/categories` | Categories + counts |
| `GET` | `/modules/{slug}` | Module detail |
| `GET` | `/modules/{slug}/knowledge` | Knowledge entries |
| `POST` | `/compare` | Compare 2–5 modules, 8 dimensions |
| `GET` | `/sessions` | User conversations |
| `GET` | `/sessions/{id}/messages` | Message history + `panel_commands` |
| `GET` | `/users/me` | Profile + stats |
| `GET` | `/health`, `/health/detailed` | Liveness + DB/pgvector |

### Database
- PostgreSQL 16 + pgvector on Docker port **5433** (not 5432)
- Redis on port 6379 (optional; graceful cache miss)
- **102 modules** across **18 categories** (17 categories have specs; `infrastructure_comparison` is empty)
- Knowledge embeddings: **BAAI/bge-large-en-v1.5**, **1024 dimensions** (`module_knowledge.embedding`)

### Auth (Dev Mode)
- `Authorization: Bearer dev@example.com` auto-creates a pro-tier user

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Use plan mode for verification steps, not just building

### 2. Subagent Strategy
- Offload research and parallel analysis to subagents
- Keep main context window clean

### 3. Self-Improvement Loop
- After corrections: update `tasks/lessons.md`
- Review `tasks/lessons.md` at session start

### 4. Verification Before Done
- `npm run build` (frontend), `pytest -v` (backend)
- `python -c "from src.main import app"` for import sanity

### 5. Demand Elegance (Balanced)
- Prefer simple correct diffs; avoid over-engineering obvious fixes

### 6. Autonomous Bug Fixing
- Fix bugs from logs/tests without hand-holding

---

## Development Rules

### Backend
- Always `async/await`; `get_db` for sessions
- Agent tools: `src/agent/tools.py`; prompts: `src/agent/prompts.py`
- Run tests: `cd backend && pytest -v`

### Frontend
- `'use client'` on interactive components
- Zustand for state; Tailwind + CSS variables
- `shiki` for code highlighting (NOT `@shikijs/core`)
- Run tests: `cd frontend && npm test`
- Build: `cd frontend && npm run build`

### Git
- Commit messages: `type: description`
- Never commit `.env`

### Common Pitfalls
- Postgres port **5433** with Docker Compose
- Stale docs saying "86 modules" — use **102**
- Claude CLI 8–15s startup overhead
- SSE: `data: {...}\n\n` with double newline
- Embeddings dimension is **1024**, not 1536

---

## Related docs

| Document | Content |
|----------|---------|
| [APPLICATION_DATA.md](./APPLICATION_DATA.md) | Data model, SSE, constraints, trace |
| [BACKEND_IMPLEMENTATION.md](./BACKEND_IMPLEMENTATION.md) | Backend layers and services |
| [APPLICATION_REPOSITORY_GUIDE.md](./APPLICATION_REPOSITORY_GUIDE.md) | Full repo tour |
| [UI_design.md](./UI_design.md) | Frontend UI inventory |
| [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) | Planned vs shipped features |
