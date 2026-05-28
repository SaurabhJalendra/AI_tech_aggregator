# Implementation roadmap — IDEA alignment

This document tracks **gaps between the product vision** ([IDEA.md](./IDEA.md)) **and the codebase**, plus **what has already shipped**. Update this file as milestones complete.

**Related:** [APPLICATION_DATA.md](./APPLICATION_DATA.md), [BACKEND_IMPLEMENTATION.md](./BACKEND_IMPLEMENTATION.md), [AGENTS.md](./AGENTS.md)

---

## Shipped (current codebase)

These were roadmap items or misconceptions; they are **implemented** today:

| Area | What shipped |
|------|----------------|
| **Phase-2 planner** | `RecommendationPlanner`, playbooks YAML, 6 pipeline classes, `AdvisorTrace`, scoring + decision metadata |
| **Semantic intent** | BGE exemplars, clarification bands, `IntentClarification` UI |
| **Constraint state** | `ConstraintState` schema, `ConstraintStateService`, `client_context`, option-card merge |
| **Slot impact policy** | Only asks slots that change pipeline preview |
| **Comparison UX** | `ComparisonDecisionSurface` (hero, capability bars, tradeoff spectrum, explainability drawer, radar) |
| **Architecture UX** | React Flow `ArchitectureCanvas`, stage groups, `NodeDetailsDrawer`, simple/advanced views |
| **Visual identity** | Session-stable entity colors for comparisons |
| **Theme** | Light/dark/system via `themeStore` + CSS variables |
| **Panel authority** | `panel_validator` + `planner_authority_strict` |
| **Explainability** | Trace persistence, `explanation_fidelity`, filtered filter reasons in UI |
| **Embeddings** | BGE 1024-dim, Alembic migration `002_bge_embedding_dimensions` |
| **Module catalog** | **102** YAML specs (+16 foundation models in `llm_layer`) |
| **Advisor API** | `/advisor/playbooks`, `/advisor/trace/schema`, trace latest endpoint |
| **Interactive panels** | `option_cards`, `interactive_architecture`, `code_project` (not stubs) |
| **SDK chat** | `AIAdvisorClient.chat()` streaming SSE exists |
| **Node actions** | Architecture drawer sends chat with `client_context.architecture_node` |

---

## Summary table — remaining work

| # | Item | Status | Goal |
|---|------|--------|------|
| 1 | Constraint-aware `suggest_stack` | Partial | Agent tool still heuristic; pipelines use scoring — unify `suggest_stack` with `scoring` + broader candidate pools |
| 2 | `module_detail`, `recommendation`, `document` panels | **Open** | Replace `MainPanel` placeholders |
| 3 | Panel state in agent context | Partial | `client_context` has panel snapshot; LLM history still text-only — richer summarization |
| 4 | Expand MCP tools | **Open** | Beyond list/get/compare/categories |
| 5 | Polish SDK streaming | **Open** | Typed events, async client, README |
| 6 | Structured node actions | Partial | `architecture_node` in context; optional `client_action` schema |

---

## Item 1 — Constraint-aware stack suggestion

### Shipped
- Playbook pipelines score with `decision_metadata` + `comparison_scores`
- `ConstraintState` + option cards via `client_context.option_answer`
- `SlotImpactPolicy` for targeted questions

### Remaining
- **`suggest_stack` agent tool** — still simpler than pipeline scoring; align with `scoring.py` and larger candidate pools per category
- **Compliance filters** — only when module metadata supports SOC2/HIPAA-style tags

---

## Item 2 — Placeholder panels

### Open
- `module_detail`, `recommendation`, `document` in `MainPanel.tsx` show placeholder copy

### Design (unchanged)
- Prefer `module_detail` with `{ slug }` + `GET /modules/{slug}`
- `recommendation`: structured `items[]` with rationale
- `document`: `markdown` via `react-markdown`

---

## Item 3 — Panel state in agent context

### Shipped
- `ChatRequest.client_context`: `current_panel`, `constraint_state`, `advisor_trace`, `recommendation_explain`, architecture focus

### Remaining
- `_build_claude_messages` does not inject historical `panel_commands` — add capped `summarize_panel_commands()` to system prompt or user prefix

---

## Item 4 — Expand MCP tools

### Open
- Add REST endpoints for knowledge search, stack suggestion (shared with planner), then SDK + MCP

---

## Item 5 — Polish SDK streaming

### Open
- TypedDict/dataclass events, `AsyncAIAdvisorClient`, timeouts, `sdk/README.md`

---

## Item 6 — Structured node actions

### Partial
- `NodeDetailsDrawer` → chat with `client_context.architecture_node`

### Optional
- Formal `client_action` enum (`swap` | `learn` | `code`) on `ChatRequest`

---

## Execution order (suggested)

| Sprint | Scope |
|--------|--------|
| **A** | Item 2 — three panels + agent emission paths |
| **B** | Item 3 — panel summarization in LLM context |
| **C** | Item 1 — `suggest_stack` parity with pipelines |
| **D** | Item 4 + 5 — REST + MCP + SDK polish |
| **E** | Item 6 — optional `client_action` hardening |

---

## Cross-cutting conventions

1. **API contract first** — `schemas/chat.py` + `types/chat.ts`
2. **Tests** — `pytest` + Vitest per milestone
3. **Docs** — update APPLICATION_DATA, BACKEND_IMPLEMENTATION, UI_design when behavior changes

---

*Last updated: reflects Phase-2 planner, 102 modules, BGE 1024-dim, and comparison/architecture UI as implemented.*
