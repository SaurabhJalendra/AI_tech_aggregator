# Application data

This document describes **what data the product uses**, where it lives, and how it flows between the registry, database, cache, advisor packages, and clients. For backend code layout, see [BACKEND_IMPLEMENTATION.md](./BACKEND_IMPLEMENTATION.md).

---

## 1. Module registry (YAML)

Technology modules are authored as **one YAML file per module** under `modules_registry/specs/{slug}.yaml`. The canonical shape is defined in `modules_registry/schema.yaml`.

**Scale:** 102 spec files, 18 category enums (category `infrastructure_comparison` has no specs yet).

**Typical sections**

| Section | Purpose |
|--------|---------|
| `meta` | `slug`, `name`, `category`, `subcategory`, `status`, `version`, `last_updated`, optional `maintainer` |
| `identity` | `tagline`, `description`, URLs, `license`, `pricing_model`, optional `logo_url` |
| `capabilities` | `primary_use_cases`, `supported_operations` |
| `technical_specs` | Structured fields; may include `decision` block for advisor scoring |
| `comparison_dimensions` | Eight 1–10 scores → `modules.comparison_scores` |
| `knowledge` | Topic/content entries → `module_knowledge` rows (embeddable) |
| `code_examples` | Titled snippets → `modules.code_examples` |
| `benchmarks` | Optional → `benchmarks` table |
| `relationships` | `alternatives`, `complements`, `typical_pipeline_position`, `pipeline_predecessors` / `pipeline_successors` |

**Ingestion**

- `scripts/seed_db.py` → `backend/src/modules/loader.py`
- Computes **`spec_hash`** (SHA256 of normalized YAML); skips unchanged bodies
- **`merge_overlay_into_technical_specs`** applies `advisor_registry` decision YAML on load
- `scripts/sync_decision_metadata.py` — backfill `technical_specs.decision` without full re-seed
- `scripts/scaffold_foundation_model_specs.py` — generates `llm_layer` / `foundation_model` specs (16 models)

---

## 2. Advisor configuration (YAML, not in DB)

| Path | Role |
|------|------|
| `backend/src/advisor_playbooks/playbooks.yaml` | Playbook ids, `required_slots`, `slot_impact_values`, `intent_ids`, `phase2_pipeline`, UI behavior |
| `backend/src/advisor_registry/vector_databases_decision.yaml` | Per-slug deployment/pricing/scores for vector DB shortlists |
| `backend/src/advisor_registry/rag_modules_decision.yaml` | RAG-stage module decision overlays |
| `backend/src/advisor_registry/comparison_universe.yaml` | Same-abstraction-layer comparison layers (e.g. retrieval vs reranker) |
| `backend/src/advisor_intent/registry.yaml` | Curated exemplar phrases → `intent_id` for semantic routing |

Loaded at runtime by `advisor_playbooks/loader.py`, `services/decision_metadata.py`, `services/comparison_universe.py`, `services/semantic_intent.py`.

**Phase-2 playbooks** (`phase2_pipeline: true`): `vector_db_comparison`, `rag_pipeline_design`, `module_code`, `architecture_review`, `local_ai_stack`, plus dynamic `category_<slug>` from planner.

---

## 3. PostgreSQL (primary store)

PostgreSQL 16 + **pgvector**. Migrations: `backend/alembic/versions/` (including `002_bge_embedding_dimensions.py` for **1024-dim** vectors).

### 3.1 Core tables

| Table | Role |
|-------|------|
| `module_categories` | Category slug, display name, ordering, icon |
| `modules` | One row per technology; JSON for specs, `comparison_scores`, relationships, `spec_hash` |
| `module_knowledge` | Knowledge chunks; **`embedding vector(1024)`** for semantic search |
| `module_integrations` | Edges (`target_slug`, `integration_type`) |
| `benchmarks` | Numeric benchmarks per module |
| `users` / `teams` | Accounts and teams |
| `conversations` | Chat sessions: title, counts, token/cost aggregates |
| `messages` | Turns: `role`, **`content` JSON**, **`panel_commands` JSON**, `sequence` |
| `comparisons` | Cached compare results (slugs, dimensions, weights, `result`, expiry) |
| `usage_records` / `usage_aggregates` | Usage tracking |

### 3.2 Message `content` JSON (assistant)

Beyond `text`, assistant messages may persist:

| Field | Purpose |
|-------|---------|
| `text` | Visible assistant reply |
| `constraint_state` | Canonical slot memory (`ConstraintState`) |
| `advisor_trace` | Pipeline trace for explainability (shortlist, scores, filters) |
| `recommendation_explain` | Compact explain payload for UI/LLM guardrails |

User messages typically `{ "text": "..." }`.

### 3.3 Embeddings

- Model: **`BAAI/bge-large-en-v1.5`** via `sentence-transformers` (`backend/src/core/embeddings.py`)
- Dimension: **1024** on `module_knowledge.embedding`
- Query prefix for retrieval: configured in embeddings module
- Generation: `scripts/generate_embeddings.py` when `EMBEDDINGS_ENABLED=true`
- Used for: **knowledge search**, **semantic intent** exemplar matching

### 3.4 Forward-looking tables (migration only)

`research_updates`, `expansion_candidates` — not wired in current ORM exports.

---

## 4. Redis (ephemeral cache)

Optional; misses fall through to PostgreSQL (`backend/src/core/redis.py`).

| Key pattern | TTL | Content |
|-------------|-----|---------|
| `modules:list:{category}:{status}:{search}:{page}:{per_page}` | 300s | Paginated module list |
| `modules:detail:{slug}` | 600s | Module detail |
| `modules:categories` | 3600s | Category list |

---

## 5. Streaming chat protocol (SSE)

`POST /api/v1/advisor/chat` returns `text/event-stream`. BFF at `POST /api/chat` proxies the stream unchanged.

### 5.1 Request body (`ChatRequest`)

```json
{
  "message": "string",
  "session_id": "uuid | null",
  "client_context": {
    "constraint_state": { "slots": {}, "playbook_id": null },
    "current_panel": "comparison_chart",
    "option_answer": { "answer_id": "...", "answer_label": "..." },
    "intent_clarification_choice": { "intent_id": "...", "label": "..." },
    "advisor_trace": {},
    "recommendation_explain": {}
  }
}
```

### 5.2 Event types

| `type` | Meaning |
|--------|---------|
| `meta` | `session_id`, optional `constraint_state`, `advisor_trace`, `recommendation_explain`, intent/playbook fields |
| `text` | Incremental assistant text |
| `panel_command` | `{ command: PanelCommand }` |
| `tool_activity` | Tool name + `running` \| `complete` (SDK path) |
| `done` | Stream finished |
| `error` | Error payload |

### 5.3 Panel commands

Persisted on assistant `messages.panel_commands` as a JSON array.

```json
{
  "action": "render | update | clear",
  "panel": "comparison_chart | interactive_architecture | option_cards | ...",
  "data": { },
  "title": "optional"
}
```

Architecture **updates** may include `subAction`: `add_node`, `add_edge`, `highlight`.

Frontend contract: `frontend/src/types/chat.ts`.

---

## 6. Constraint state

Canonical model: `backend/src/schemas/constraint_state.py` ↔ `frontend/src/types/chat.ts`.

| Concept | Description |
|---------|-------------|
| `ConstraintSlot` | `value`, `source` (`explicit`, `inferred`, `option_card`, `accumulated`, `default`), `confidence` |
| Slots | e.g. `budget_tier`, `scale`, `deployment`, `language`, `use_case` — playbook-specific |
| `ConstraintStateService` | Merges message text + `client_context.option_answer` + prior state |

Slot impact: `SlotImpactPolicy` only asks missing slots that change pipeline `preview_signature`.

---

## 7. Advisor trace & explainability

`AdvisorTrace` (`schemas/advisor_trace.py`): `retrieved`, `filtered_out`, `scores`, `shortlist`, `steps`, `slot_impact_notes`.

- `to_explain_payload()` → user-visible explainability (internal filter reasons hidden via `explainability_filters.ts`)
- `explanation_fidelity.py` validates LLM narration against trace when LLM fallback runs
- Debug UI: `TraceDebugPanel.tsx` (collapsible JSON + entity chips)

---

## 8. REST JSON shapes (high level)

- **Modules list** — paginated summaries
- **Module detail** — full module + knowledge + integrations + benchmarks
- **Compare** — `ComparisonResult`: dimension matrix, rankings, weighted overall, highlights, recommendation string
- **Sessions** — conversation metadata; messages include `panel_commands`
- **Advisor playbooks** — declarative playbook list for tooling/docs

---

## 9. Comparison data

**Eight dimensions** (1–10): `performance`, `scalability`, `ease_of_use`, `cost_efficiency`, `community`, `maturity`, `flexibility`, `data_privacy`.

Sources:
- Spec `comparison_dimensions` → DB `comparison_scores`
- Playbook scoring (`services/scoring.py`) may blend **decision metadata** overlays with comparison scores
- `ComparisonEngine` for REST `/compare` and agent `compare_modules` tool

**Comparison universe** layers prevent mixing incompatible modules (e.g. reranker vs retrieval strategy) — see `comparison_universe.yaml`.

---

## 10. Client-side state (not server DB)

| Store | Data |
|-------|------|
| `chatStore` | Messages, streaming, `sessionId`, intent clarification, `constraintState`, `lastAdvisorTrace`, `lastRecommendationExplain` |
| `panelStore` | `currentPanel`, `panelData`, `panelTitle`, `panelHistory`, debounced render |
| `themeStore` | `light` / `dark` / `system` |
| `visualIdentityStore` | Session-stable colors for comparison/architecture entities |

---

## 11. Related paths

| Path | Content |
|------|---------|
| `modules_registry/schema.yaml` | Module YAML schema |
| `modules_registry/specs/*.yaml` | 102 module definitions |
| `scripts/seed_db.py` | Load/update DB |
| `scripts/generate_embeddings.py` | BGE embedding backfill |
| `scripts/sync_decision_metadata.py` | Decision overlay backfill |
| `backend/alembic/` | Schema migrations |
| `docs/architecture/README.md` | Architecture diagram |
