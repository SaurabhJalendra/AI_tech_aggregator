# Backend implementation

This document describes how the **Python/FastAPI backend** is organized, how requests flow, and how configuration ties to dependencies. For tables, YAML specs, and streaming payloads, see [APPLICATION_DATA.md](./APPLICATION_DATA.md).

---

## 1. Stack and entrypoint

| Piece | Technology |
|-------|------------|
| Runtime | Python ≥ 3.11 (see `backend/pyproject.toml`) |
| Framework | FastAPI |
| DB access | SQLAlchemy 2.x **async** + `asyncpg` |
| Migrations | Alembic |
| Vector search | `pgvector` in PostgreSQL |
| Cache | Redis (async client; graceful degradation if down) |
| LLM | Anthropic Messages API **or** Claude Code CLI (adapter) |

**Application factory**: `backend/src/main.py` builds the FastAPI app, attaches CORS, registers **SlowAPI** rate limiting on `app.state.limiter`, and includes a single API router.

**ASGI app**: `app = create_app()` — run with uvicorn targeting `src.main:app` (per project conventions).

**Imports**: Application code uses the **`src.`** package prefix (e.g. `from src.api.v1.router import api_v1_router`).

---

## 2. HTTP API surface (`/api/v1`)

All versioned routes are mounted under **`/api/v1`** via `backend/src/api/v1/router.py`.

| Prefix / path | Module | Purpose |
|----------------|--------|---------|
| `GET /health`, `GET /health/detailed` | `health.py` | Liveness; detailed checks DB + pgvector cast |
| `POST /auth/login`, `GET /auth/me` | `auth.py` | Dev login (gated by `environment`); current user profile |
| `POST /advisor/chat` | `chat.py` | **SSE** advisor chat (requires Claude Code or API key) |
| `GET/POST .../modules` | `modules.py` | List modules, categories, detail by slug (Redis-backed cache) |
| `POST /compare` | `compare.py` | Structured multi-module comparison |
| `GET /sessions`, `GET /sessions/{id}/messages` | `sessions.py` | Conversation history for authenticated user |
| `GET /users/me` | `sessions.py` | User profile + simple conversation stats |

**Auth** (`backend/src/core/security.py`)

- **Development**: `Authorization: Bearer <email>` — email is resolved to a user via `_get_or_create_dev_user` (new users get `tier="pro"`).
- **Production**: Bearer token validated as **NextAuth JWT** (`fastapi_nextauth_jwt`, secret from settings).

---

## 3. Layered structure

```
src/
  main.py              # FastAPI app, CORS, router mount
  core/
    config.py          # Pydantic Settings → env / .env
    security.py        # JWT / dev bearer auth
    redis.py           # cache_get / cache_set / cache_delete
    embeddings.py      # embedding generation for knowledge search
  db/
    base.py            # SQLAlchemy declarative base
    session.py         # async engine, session factory, get_db dependency
  models/              # ORM entities (User, Module, Conversation, Message, …)
  schemas/             # Pydantic request/response models
  api/v1/              # Routers (thin): validate input, call services/engine
  services/            # chat_service, module_service — orchestration + DB
  modules/
    loader.py          # YAML → ORM (used by seed scripts / tooling)
    comparison_engine.py  # compare_modules API + agent tool backing
  agent/
    advisor.py         # Streaming agent loop (SDK vs Claude Code)
    tools.py           # Anthropic tool schemas + names
    prompts.py         # System prompt construction (catalog injection)
    claude_code_adapter.py
```

**Pattern**: Routers depend on **`get_db`** → **services** or **engines** → **models**. The chat router returns a **`StreamingResponse`** with `media_type="text/event-stream"` and no-cache headers.

---

## 4. Chat pipeline

1. **`ChatService.stream_response`** (`services/chat_service.py`): resolve/create `Conversation`, persist user `Message`, rebuild Claude message list from history, inject **module/category catalog** into the system prompt (`build_catalog_section`), emit initial SSE `meta` with `session_id`.
2. **`AdvisorAgent.stream_response`** (`agent/advisor.py`):
   - **Claude Code mode** (`settings.use_claude_code`): delegates to `ClaudeCodeAdapter.stream`, yields `text` and `panel_command` events per adapter output.
   - **Anthropic SDK mode**: streaming `messages.stream` with **tools** from `ALL_TOOLS`; on `tool_use`, executes handlers (module search, compare, render tools, etc.), appends `tool_result`, loops until no tools; guards against duplicate tool calls and max iterations.
3. **Persistence**: After streaming, assistant text and collected **`panel_commands`** are saved on a new `Message`; conversation title may be set from the first user message.

---

## 5. Module system in the backend

- **Source of truth in git**: `modules_registry/specs/*.yaml`.
- **Loader**: `modules/loader.py` resolves `SPECS_DIR` relative to the repo, parses YAML, maps fields onto `Module`, `ModuleKnowledge`, `ModuleIntegration`, `Benchmark`, and categories.
- **Runtime reads**: `ModuleService` provides listing, slug detail with eager loads, category aggregates, and **embedding-based knowledge search** for the agent.

---

## 6. Configuration (`backend/src/core/config.py`)

Loaded from **environment variables** and optional **`.env`** (via `pydantic-settings`).

| Setting | Role |
|---------|------|
| `DATABASE_URL` / `DATABASE_URL_SYNC` | Async and sync PostgreSQL URLs (default port in file is `5432`; **Docker Compose maps host `5433` → container `5432`** — align URL with how you run Postgres) |
| `REDIS_URL` | Redis connection |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | SDK mode |
| `USE_CLAUDE_CODE` | When true, use CLI adapter instead of API key streaming |
| `OPENAI_API_KEY` | Embeddings (when generating/searching vectors) |
| `NEXTAUTH_SECRET`, `NEXTAUTH_URL` | Production JWT verification alignment with frontend |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `ENVIRONMENT`, `DEBUG` | Environment mode |

Rate-limit-related defaults exist in settings for future enforcement (`free_tier_*`).

---

## 7. Testing and quality

- **Tests**: `backend/tests/` — pytest with `asyncio_mode = auto` (`pyproject.toml`).
- **Lint**: Ruff configuration in `backend/pyproject.toml`.

Suggested check after changes: `pytest -v` from `backend/`.

---

## 8. Related packages in the repo

| Package | Role |
|---------|------|
| `sdk/` | `AIAdvisorClient` — HTTP client to `/api/v1` for scripts and integrations |
| `mcp_server/` | Minimal MCP (stdio JSON-RPC) exposing list/get/compare via the SDK |
| `cli/` | CLI entry package (`ai_advisor_cli`) |

These consume the same REST API documented above; they do not embed business logic duplicated from the backend.

---

## 9. Cross-references

- [APPLICATION_DATA.md](./APPLICATION_DATA.md) — database tables, YAML registry, Redis keys, SSE types.
- [AGENTS.md](./AGENTS.md) — contributor-oriented paths and conventions.
- [docs/architecture/README.md](./docs/architecture/README.md) — system diagram and agent overview.
