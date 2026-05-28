# Backend implementation

How the **Python/FastAPI backend** is organized, how requests flow, and how Phase-2 advisor pipelines relate to the LLM agent. For data shapes and SSE payloads, see [APPLICATION_DATA.md](./APPLICATION_DATA.md).

---

## 1. Stack and entrypoint

| Piece | Technology |
|-------|------------|
| Runtime | Python ≥ 3.11 (`backend/pyproject.toml`) |
| Framework | FastAPI |
| DB | SQLAlchemy 2.x async + `asyncpg` |
| Migrations | Alembic |
| Vectors | pgvector, **1024** dimensions (BGE) |
| Cache | Redis (graceful degrade) |
| LLM | Anthropic Messages API **or** Claude Code CLI |
| Local embeddings | `sentence-transformers` — `BAAI/bge-large-en-v1.5` |

**Entry:** `backend/src/main.py` — FastAPI app, CORS, SlowAPI rate limiter, `api_v1_router`.

**Imports:** `from src....` package prefix.

---

## 2. HTTP API surface (`/api/v1`)

Router: `backend/src/api/v1/router.py`

| Method | Path | Module | Auth | Purpose |
|--------|------|--------|------|---------|
| `GET` | `/health` | `health.py` | No | Liveness |
| `GET` | `/health/detailed` | `health.py` | No | DB + pgvector check |
| `POST` | `/advisor/chat` | `chat.py` | Yes | **SSE** chat |
| `GET` | `/advisor/playbooks` | `advisor.py` | No | Playbook metadata |
| `GET` | `/advisor/trace/schema` | `advisor.py` | No | `AdvisorTrace` JSON schema |
| `GET` | `/advisor/sessions/{id}/trace/latest` | `advisor.py` | No* | Latest trace from messages |
| `POST` | `/auth/login` | `auth.py` | No | Dev login (403 outside development) |
| `GET` | `/auth/me` | `auth.py` | Yes | Current user |
| `GET` | `/modules` | `modules.py` | No | Paginated list (Redis 300s) |
| `GET` | `/modules/categories` | `modules.py` | No | Categories (Redis 3600s) |
| `GET` | `/modules/{slug}` | `modules.py` | No | Detail (Redis 600s) |
| `GET` | `/modules/{slug}/knowledge` | `modules.py` | No | Knowledge entries |
| `POST` | `/compare` | `compare.py` | No | 2–5 modules, 8 dimensions |
| `GET` | `/sessions` | `sessions.py` | Yes | User conversations |
| `GET` | `/sessions/{id}/messages` | `sessions.py` | Yes | History + `panel_commands` |
| `GET` | `/users/me` | `sessions.py` | Yes | Profile + stats |

\*Trace latest endpoint reads DB by session id without ownership check — treat as dev/debug unless hardened.

**Chat guard:** `chat.py` returns **503** if `USE_CLAUDE_CODE=false` and no `ANTHROPIC_API_KEY`.

---

## 3. Layered structure

```
src/
  main.py
  core/           config, security, redis, embeddings
  db/             base, async session, get_db
  models/         User, Module, Conversation, Message, ...
  schemas/        chat, compare, intent, constraint_state, advisor_trace, module
  api/v1/         thin routers
  services/       orchestration (see §4)
  services/pipelines/   Phase-2 playbook executors
  modules/        loader.py, comparison_engine.py
  agent/          advisor.py, tools.py, prompts.py, claude_code_adapter.py
  advisor_playbooks/    playbooks.yaml + loader
  advisor_registry/     decision + comparison_universe YAML
  advisor_intent/       intent exemplar registry YAML
```

**Pattern:** Routers → `get_db` → services/engines → models. Chat returns `StreamingResponse` (`text/event-stream`).

---

## 4. Services layer

### 4.1 Chat orchestration

| Service | File | Role |
|---------|------|------|
| **ChatService** | `chat_service.py` | Conversation CRUD, semantic intent, planner dispatch, LLM fallback, sanitization, persist trace/constraints |
| **RecommendationPlanner** | `recommendation_planner.py` | Task detection, slot questions, playbook routing, SSE events |
| **SemanticIntentDetector** | `semantic_intent.py` | BGE exemplar match, keyword overrides, clarification bands |
| **ConstraintStateService** | `constraint_state_service.py` | Build/merge `ConstraintState` from text + `client_context` |
| **SlotImpactPolicy** | `slot_impact_policy.py` | Ask only impactful missing slots |
| **panel_validator** | `panel_validator.py` | Validate panel commands; block LLM panels under active playbook |
| **explanation_fidelity** | `explanation_fidelity.py` | Narration vs trace checks; system addendum for agent |
| **response_sanitizer** | `response_sanitizer.py` | Strip UI artifacts; `SanitizationReport` logs every mutation for trace |
| **architecture_consulting** | `architecture_consulting.py` | Blueprint consulting payloads, strategy branches, evolution |
| **architecture_simulation** | `architecture_simulation.py` | What-if simulation hooks for blueprint workspace |
| **strategic_consulting** | `strategic_consulting.py` | Strategy branch detection, cross-turn consulting continuity |

### 4.2 Module & comparison

| Service | File | Role |
|---------|------|------|
| **ModuleService** | `module_service.py` | List, detail, categories, vector + ILIKE knowledge search |
| **ComparisonEngine** | `modules/comparison_engine.py` | 8-dimension matrix, rankings, recommendation string |
| **comparison_universe** | `comparison_universe.py` | Layered shortlists from YAML |
| **decision_metadata** | `decision_metadata.py` | Merge registry overlays into `technical_specs.decision` |
| **scoring** | `scoring.py` | Weighted scoring, dimension weights from constraints |

### 4.3 Pipelines (`services/pipelines/`)

Registered in `pipeline_registry.py` by `playbook_id`:

| Pipeline class | Playbook | File |
|----------------|----------|------|
| `VectorDbRecommendationPipeline` | `vector_db_comparison` | `vector_db.py` |
| `RagPipelineDesignPipeline` | `rag_pipeline_design` | `rag_design.py` |
| `ModuleCodePipeline` | `module_code` | `module_code.py` |
| `ArchitectureReviewPipeline` | `architecture_review` | `architecture_review.py` |
| `LocalAiStackPipeline` | `local_ai_stack` | `local_ai_stack.py` |
| `CategoryComparisonPipeline` | `category_*` | `category_comparison.py` |
| **Base** | — | `base.py` — `RecommendationPipeline`, `PipelineResult`, `AdvisorTrace` attachment |

Shared helpers: `runtime.py` (`sort_scored_records`, `build_shortlist`).

### 4.4 Module loader

`modules/loader.py` — YAML → ORM; `spec_hash`; sync knowledge, integrations, benchmarks; decision overlay merge.

---

## 5. Chat pipeline (per turn)

```
POST /advisor/chat
  → validate_client_context (allowlist, size caps) on ChatRequest
  → ChatService.stream_response
      → emit meta { session_id }
      → SemanticIntentDetector (skipped for explicit UI actions: option_answer, strategy_branch, …)
      → RecommendationPlanner.plan (unless PLANNER_MODE=off)
            → ConstraintStateService.build (merge client slots; falsy values preserved)
            → SlotImpactPolicy → pipeline.run → panel_command + text + trace
      → PLANNER_MODE routing:
            on + events → intercept (deterministic only)
            shadow + events → emit planner_routing meta, fall through to LLM
            off → planner_skipped, LLM if enabled
      → if not intercepted && llm_fallback_enabled:
            → AdvisorAgent.stream_response (_format_client_context uses allowlisted fields only)
            → filter_llm_panel_command (playbook authority)
      → sanitize text (logged SanitizationReport), persist Message + constraint_state + trace
      → emit done
```

**ConstraintState** (`schemas/constraint_state.py`): canonical slot map with `source`, `confidence`, `raw_label`. Slot presence uses `state.has(slot_id)` so `False`, `0`, and `""` are valid answers. Legacy flat `constraints` in client payloads is **rejected** — see [CONSTRAINT_STATE.md](./CONSTRAINT_STATE.md).

**Simulation / consulting:** architecture review and blueprint flows attach `architecture_consulting` payloads; `strategic_consulting` resolves strategy branches from UI context or message text; `architecture_simulation` supports sandbox posture changes without wiping constraints.

**Prompt boundary:** `validate_client_context()` + `payload_sanitizer.sanitize_nested()` enforce depth, array size, injection stripping, and prompt char budgets. LLM narration uses `format_prompt_context()` only (server trace/explain never from client).

**Filter exhaustion:** pipelines set `filter_exhausted`; planner emits **constraint negotiation** option cards (`constraint_negotiation.py`) instead of silent fallback or dead-ends.

**Planner telemetry:** each turn builds `PlannerTurnTelemetry` (persisted on assistant messages, emitted in SSE `planner_telemetry`). Shadow mode runs `compare_shadow_outcomes()`. Internal health: `GET /advisor/metrics/internal` (dev/staging).

**Deterministic ranking:** `sort_scored_records()` orders by `(score, confidence, retrieval_score, slug)` with rounded floats; module lists use `ORDER BY slug`; knowledge search ties on `Module.slug`.

**Subprocess lifecycle:** `subprocess_lifecycle.terminate_subprocess()` — kill, wait, close streams after Claude CLI timeouts.

---

## 6. Agent layer (`agent/`)

### 6.1 Dual mode

| Mode | Config | Behavior |
|------|--------|----------|
| Claude Code CLI | `USE_CLAUDE_CODE=true` (default) | `ClaudeCodeAdapter` streams text; panels via `<!--PANEL_CMD:...-->` markers |
| Anthropic SDK | `USE_CLAUDE_CODE=false` + API key | Tool loop (max ~25 iterations), `tool_activity` SSE |

### 6.2 Tools (`tools.py`)

`search_modules`, `get_module_detail`, `compare_modules`, `search_knowledge`, `list_categories`, `render_architecture_diagram`, `render_comparison`, `render_code`, `get_benchmarks`, `suggest_stack`, `present_options`, `build_architecture_step`, `render_code_project`.

When `planner_authority_strict` and a playbook is active, LLM cannot emit comparison/option/architecture panels — narration must align with deterministic trace.

---

## 7. Configuration (`core/config.py`)

| Setting | Role |
|---------|------|
| `database_url` | Async Postgres (default port **5433**) |
| `redis_url` | Cache |
| `use_claude_code`, `anthropic_api_key`, `anthropic_model` | LLM mode |
| `embeddings_enabled` | BGE on/off |
| `semantic_intent_*` | Confidence/margin thresholds |
| `planner_authority_strict`, `llm_fallback_enabled` | Planner vs LLM panel authority |
| `planner_mode` | `off` \| `shadow` \| `on` — kill switch / rollback (see chat pipeline §5) |
| `nextauth_secret`, `nextauth_url` | Production JWT |
| `cors_origins` | Allowed origins |

---

## 8. Models (`models/`)

`User`, `Team`, `Conversation`, `Message`, `Module`, `ModuleCategory`, `ModuleKnowledge` (embedding Vector(1024)), `ModuleIntegration`, `Benchmark`, `Comparison`, `UsageRecord`, `UsageAggregate`.

---

## 9. Testing

`backend/tests/` — 22+ modules including:

- `test_semantic_intent`, `test_paraphrase_regression`, `test_playbooks`
- `test_constraint_state`, `test_slot_impact_policy`, `test_scoring`
- `test_vector_db_pipeline`, `test_rag_pipeline`, `test_comparison_universe`
- `test_advisor_trace`, `test_explanation_fidelity`, `test_panel_validator`
- `test_chat_service_constraints`, `test_planner_hardening`, `test_embeddings`, `test_module_loader`
- Falsy constraint answers, filter exhaustion (no silent fallback), client_context allowlist, sanitizer reports

Run: `cd backend && pytest -v`

---

## 10. Related packages

| Package | Role |
|---------|------|
| `sdk/` | `AIAdvisorClient` — HTTP to `/api/v1` |
| `mcp_server/` | stdio MCP: list/get/compare/categories (subset of API) |
| `cli/` | CLI wrapper |

---

## 11. Cross-references

- [APPLICATION_DATA.md](./APPLICATION_DATA.md)
- [AGENTS.md](./AGENTS.md)
- [APPLICATION_REPOSITORY_GUIDE.md](./APPLICATION_REPOSITORY_GUIDE.md)
