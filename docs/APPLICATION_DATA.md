# Application data

This document describes **what data the product uses**, where it lives, and how it flows between the registry, database, cache, and clients. For how the backend is structured in code, see [BACKEND_IMPLEMENTATION.md](./BACKEND_IMPLEMENTATION.md).

---

## 1. Module registry (YAML)

Technology modules are authored as **one YAML file per module** under `modules_registry/specs/{slug}.yaml`. The canonical shape is defined in `modules_registry/schema.yaml`.

**Typical sections and purpose**

| Section | Purpose |
|--------|---------|
| `meta` | `slug`, `name`, `category` (enum), `status`, `version`, `last_updated`, optional `subcategory`, `maintainer` |
| `identity` | `tagline`, `description`, URLs, `license`, `pricing_model`, optional `logo_url` |
| `capabilities` | `primary_use_cases`, `supported_operations`, and other capability fields per spec |
| `technical_specs` | Structured, module-specific fields (stored as JSON on the row) |
| `comparison_dimensions` | Scored dimensions; loaded into `modules.comparison_scores` |
| `knowledge` | Topic/content entries; each becomes a `module_knowledge` row (embeddable text) |
| `code_examples` | List of titled snippets; stored on `modules.code_examples` |
| `benchmarks` | Optional benchmark facts → `benchmarks` table |
| `relationships` | Alternatives, complements, pipeline predecessors/successors (JSON on `modules`) |
| `pipeline` | Position and graph hints mapped into pipeline columns on `modules` |

**Ingestion**

- `scripts/seed_db.py` (and the loader in `backend/src/modules/loader.py`) reads specs, computes a **content hash** (`spec_hash`), and inserts or updates rows without duplicating unchanged specs.

---

## 2. PostgreSQL (primary store)

The database is **PostgreSQL 16 with the `pgvector` extension**. Migrations live under `backend/alembic/versions/` (initial schema: `001_initial_schema.py`).

### 2.1 Core product tables (actively used by ORM and APIs)

| Table | Role |
|-------|------|
| `module_categories` | Category slug, display name, ordering, icon |
| `modules` | One row per technology: identity, JSON blobs for specs/capabilities/relationships, `spec_hash` |
| `module_knowledge` | Per-module knowledge chunks; **`embedding vector(1536)`** for semantic search |
| `module_integrations` | Edges to other modules (`target_slug`, `integration_type`) |
| `benchmarks` | Numeric benchmarks linked to a module |
| `users` | Accounts: email, tier, optional team, API key field |
| `teams` | Team container (owner reference in migration) |
| `conversations` | Chat sessions per user: title, counts, cost/token aggregates |
| `messages` | Chat turns: `role`, **`content` JSON** (e.g. `{"text": "..."}`), optional **`panel_commands` JSON** (list of UI commands), sequence |
| `comparisons` | Cached comparison results (module slugs, dimensions, weights, JSON `result`, expiry) |
| `usage_records` | Per-event usage (tokens, cost, optional `conversation_id`, `metadata`) |
| `usage_aggregates` | Rolled-up usage by user and period |

### 2.2 Schema present in migrations; limited or no ORM usage in `src/models`

These tables exist in the database for forward-looking features (research queue, expansion). They may not appear in `backend/src/models/__init__.py`:

| Table | Role |
|-------|------|
| `research_updates` | Findings linked to modules, review workflow |
| `expansion_candidates` | Suggested new modules / draft specs |

### 2.3 Embeddings

- Column: `module_knowledge.embedding`, type **`vector(1536)`** (OpenAI-style dimension; generation is configured in `backend/src/core/embeddings.py` and related scripts).
- Used by agent/tooling for **semantic knowledge search** over module content.

---

## 3. Redis (ephemeral cache)

Redis is optional at runtime: if the client cannot connect, cache helpers return misses and the API still serves from PostgreSQL.

**Usage** (`backend/src/core/redis.py`)

- JSON-serialized values with TTL.
- **Module list**: keys like `modules:list:{category}:{status}:{search}:{page}:{per_page}` (TTL 300s).
- **Module detail**: `modules:detail:{slug}` (see `modules.py` for exact TTL).
- **Categories**: `modules:categories` (TTL 3600s).

---

## 4. Streaming chat protocol (SSE payloads)

The advisor chat endpoint streams **Server-Sent Events** (`data: …`). The frontend and BFF parse lines starting with `data: ` as JSON.

**Common event types**

| `type` | Meaning |
|--------|---------|
| `meta` | e.g. `session_id` (conversation UUID) for the client to reuse |
| `text` | Incremental assistant text (`content`) |
| `panel_command` | UI instruction: `command` matches the panel command shape below |
| `tool_activity` | Optional progress for tool execution (when emitted) |
| `done` | Stream finished |
| `error` | Error payload |

**Panel commands (persisted and replayed)**

- Stored on assistant `messages.panel_commands` as a JSON array.
- Shape aligns with the frontend contract in `frontend/src/types/chat.ts`: `action` (`render` \| `update` \| `clear`), `panel` (e.g. `architecture_diagram`, `comparison_chart`, `code_preview`, …), `data`, optional `title`.
- `GET /api/v1/sessions/{id}/messages` returns each message’s `panel_commands` for history replay.

---

## 5. REST JSON shapes (high level)

- **Modules list** (`GET /api/v1/modules`): paginated list with summary fields (`slug`, `name`, `category`, `tagline`, etc.).
- **Module detail** (`GET /api/v1/modules/{slug}`): full module payload including knowledge, integrations, benchmarks as implemented in the route.
- **Compare** (`POST /api/v1/compare`): request body per `CompareRequest`; response is the comparison engine’s structured result (dimensions, rankings, etc.).
- **Sessions**: list metadata and per-session messages as built in `sessions.py`.

---

## 6. Client-side state (not server data, but “data the app uses”)

- **Zustand** (`frontend/src/stores/chatStore.ts`, `panelStore.ts`): messages, streaming state, session id, current panel and history.
- **Next.js BFF** (`frontend/src/app/api/chat/route.ts`): proxies the raw SSE body to the backend; does not reinterpret panel payloads.

---

## 7. Related paths

| Path | Content |
|------|---------|
| `modules_registry/schema.yaml` | Module YAML schema |
| `modules_registry/specs/*.yaml` | Module definitions |
| `scripts/seed_db.py` | Load/update DB from specs |
| `scripts/generate_embeddings.py` | Embedding backfill / generation |
| `backend/alembic/` | Schema migrations |
| `docs/architecture/README.md` | High-level architecture diagram |
