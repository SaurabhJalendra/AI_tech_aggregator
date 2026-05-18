# Implementation roadmap — IDEA alignment (six workstreams)

This document captures a **detailed implementation plan** for closing gaps between the product vision ([IDEA.md](../IDEA.md)) and the current codebase. It is derived from architecture review and gap analysis; some items correct earlier misconceptions (for example, the Python SDK already exposes streaming `chat()`—see [Item 5](#item-5--polish-sdk-streaming-async-types-docs-robustness)).

**Related references**

- [APPLICATION_DATA.md](../APPLICATION_DATA.md) — data shapes, SSE, DB
- [BACKEND_IMPLEMENTATION.md](../BACKEND_IMPLEMENTATION.md) — backend layout, APIs
- [AGENTS.md](../AGENTS.md) — paths and conventions

---

## Summary table

| # | Item | One-line goal |
|---|------|----------------|
| 1 | Constraint-aware stack suggestion | `suggest_stack` uses structured constraints and scoring; option cards can feed constraints |
| 2 | `module_detail`, `recommendation`, `document` panels | Replace `MainPanel.tsx` stubs with real UI |
| 3 | Panel state in agent context | Claude receives a compact summary of what the user sees |
| 4 | Expand MCP tools | Expose more advisor capabilities beyond the current four MCP tools |
| 5 | Polish SDK streaming | Typed events, async client, docs, robustness (chat streaming already exists) |
| 6 | (Optional) Structured node actions | Machine-readable architecture node actions + optional diagram update loop |

---

## Cross-cutting conventions

Apply to every item where relevant:

1. **API contract first** — Extend `backend/src/schemas/chat.py` (and any new route schemas), then the Next.js BFF (`frontend/src/app/api/chat/route.ts`) to forward new fields, then `chatStore` / callers.
2. **Type alignment** — Keep `frontend/src/types/chat.ts` and backend Pydantic models aligned for `PanelCommand.data` per panel type.
3. **Testing** — Backend: `pytest` for services and schemas; frontend: Vitest for stores and panel components; manual E2E for chat + panels after each milestone.
4. **Documentation** — Update [APPLICATION_DATA.md](../APPLICATION_DATA.md), [BACKEND_IMPLEMENTATION.md](../BACKEND_IMPLEMENTATION.md), or `sdk/README.md` when public behavior or APIs change.

---

## Item 1 — Constraint-aware stack suggestion (`suggest_stack` + option cards)

### Objectives

- **`suggest_stack` uses structured constraints**, not only “first module among three per category” plus a narrow `budget == low` branch.
- **Optional tie-in**: option card selections **reliably** inform the backend of “current constraints,” not only the visible label text as a plain user message.

### Current behavior (baseline)

- `_tool_suggest_stack` in `backend/src/agent/advisor.py` loads up to three modules per category, picks `modules[0]`, and if `constraints.get("budget") == "low"` prefers `open_source` / `free` within that small set. Most constraint keys and `preferences` do not affect ranking.

### Design

#### 1. Constraint model (backend)

- Add a Pydantic model, e.g. `StackConstraints` / `UserConstraints`, with fields such as:
  - `budget_tier`: low | medium | high
  - Optional `max_monthly_usd`
  - `scale`: document count or QPS band (enum or ranges)
  - `data_sensitivity` / `compliance`: list of strings (e.g. SOC2)—only use in v1 if mappable to DB fields or clear heuristics
  - `team_size`, `prefer_open_source`, optional `excluded_slugs` / required categories
- **Rule**: only add fields that can be **applied** with existing data (`modules.pricing_model`, `comparison_scores`, tags, etc.). Defer strict compliance filtering until module metadata supports it.

#### 2. Tool schema

- Extend `TOOL_SUGGEST_STACK` in `backend/src/agent/tools.py` so `constraints` is a structured object matching the Pydantic model, with descriptions that steer the LLM to populate it from user chat.

#### 3. Ranking logic

- In `_tool_suggest_stack`:
  - Per category, load a **larger candidate set** (e.g. 15–30 modules), not `per_page=3` only.
  - **Phase 1 — hard filters**: e.g. `prefer_open_source` → filter by `pricing_model`; `budget_tier=low` → align with cost-friendly models.
  - **Phase 2 — soft scoring**: derive **dimension weights** from constraints (e.g. sensitivity → weight `data_privacy`, `maturity`; cost focus → `cost_efficiency`). Reuse patterns from `ComparisonEngine` reading `module.comparison_scores`.
  - Select **top module per category** (or top diverse stacks if product requires it).
  - Continue emitting a **`panel_command`** for the architecture (`architecture_diagram` vs `interactive_architecture`—pick one product-wide convention).

#### 4. Prompts

- Update `backend/src/agent/prompts.py` so the model is instructed to call `suggest_stack` with **structured `constraints`** when the user states budget, scale, privacy, team size, etc.

#### 5. Option cards tie-in

- Extend `OptionCard` in `frontend/src/types/chat.ts` with optional metadata, e.g. `constraints: Partial<StackConstraints>` or a stable `value` key the server maps to constraints.
- When building options, `TOOL_PRESENT_OPTIONS` / the agent should attach that metadata on options where appropriate.
- In `frontend/src/components/advisor/panels/OptionCards.tsx`, on select: send not only human text but **structured `client_context`** on the chat request (requires **Item 3’s `ChatRequest` extension**—see dependency note below).

### Deliverables

- New or updated: `backend/src/schemas/` (constraints), `advisor.py` (`_tool_suggest_stack`), `tools.py`, `prompts.py`.
- Optional: `ModuleService` helpers for efficient “many modules by category” queries.

### Acceptance criteria

- Same scenario with explicit constraints (e.g. low budget + high privacy emphasis) yields **different** recommended slugs than the default stack when module scores support it.
- Option card clicks, when wired, update constraints visible to the **next** backend turn.

### Risks

- **Compliance (e.g. SOC2)** may not be first-class on `Module` rows; v1 may use **weights only** or **tag/knowledge** heuristics—document limitations.

### Dependency note

- **Option card → backend** needs **`client_context` (or similar) on `ChatRequest`**—overlaps with **Item 3**. You can ship **Item 1** first using **only** LLM-filled `suggest_stack` arguments from user text, then add option-card payload in the same item or immediately after Item 3.

---

## Item 2 — `module_detail`, `recommendation`, `document` panels (replace stubs)

### Objectives

- When the agent emits `panel_command` with `panel` ∈ `module_detail` | `recommendation` | `document`, the main panel shows **real content**, not placeholders in `frontend/src/components/advisor/MainPanel.tsx`.

### Current behavior (baseline)

- `MainPanel.tsx` renders placeholder copy for those three `case`s.

### Design

#### 1. Data contracts (document before coding)

- **`module_detail`**: prefer `{ "slug": string }`; the panel component loads **`GET /api/v1/modules/{slug}`** for full detail (avoids huge SSE payloads). Alternative: inline summary in `data` if offline use is required.
- **`recommendation`**: e.g. `{ "title"?, "summary"?, "items": [{ "slug", "name", "rationale", "highlights"? }] }`.
- **`document`**: e.g. `{ "title"?, "markdown": string }` rendered with **`react-markdown`** + **`remark-gfm`** (consistent with chat).

#### 2. New components

- Add under `frontend/src/components/advisor/panels/`:
  - `ModuleDetailPanel.tsx` — loading/error, typography aligned with existing panels.
  - `RecommendationPanel.tsx` — list/cards; links to public module pages if routes exist.
  - `DocumentPanel.tsx` — scrollable markdown; safe GFM defaults.

#### 3. `MainPanel.tsx`

- Replace stub branches with the new components.

#### 4. Agent / tools

- **`get_module_detail`** today feeds the **model**, not necessarily the **`module_detail` panel**. Add or extend tool handlers in `advisor.py` / `tools.py` so the UX can show **`module_detail`** when appropriate (same for recommendation/document), keeping **Claude Code** vs **Anthropic SDK** paths consistent where possible.

### Deliverables

- Three panel components + `MainPanel` wiring; tool or prompt behavior so these panels are actually emitted in realistic flows.

### Acceptance criteria

- Manual test: inject or trigger each `panel` type and verify correct rendering and no placeholder text.

### Risks

- **Payload size** for inline module blobs vs **extra HTTP round-trip**—prefer slug + fetch unless latency is unacceptable.

---

## Item 3 — Panel state / summary in agent message construction

### Objectives

- The model receives a **compact** description of the **current UI** (and optionally recent panel commands), without dumping full historical `panel_commands` JSON.

### Current behavior (baseline)

- `ChatService._build_claude_messages` in `backend/src/services/chat_service.py` maps each DB message to plain text from `content.text` only; **`panel_commands` are not** included.

### Design

#### 1. Sources

- **Server**: last assistant message’s `panel_commands` from the database.
- **Client** (recommended): optional **`client_context`** on each chat request: `currentPanel`, `panelTitle`, optional `focusedSlug`—reflects back/forward navigation the DB might not encode.

#### 2. Summarization

- Implement `summarize_panel_commands(commands: list) -> str` (and/or summarize `client_context`):
  - One line per command: panel type, title, key slugs, comparison participants, etc.
  - **Hard cap** length (e.g. 500–1500 characters) to control tokens.

#### 3. Injection point

- Either:
  - **Append to system prompt** for this request only (e.g. `build_system_prompt` + UI appendix), or
  - **Prefix synthetic context** to the latest user turn (less ideal semantically).

#### 4. Request schema

- Extend `ChatRequest` in `backend/src/schemas/chat.py` with optional `client_context: dict | None` (or a typed Pydantic sub-model).
- Forward through BFF and `chatStore.sendMessage` / equivalent.

### Deliverables

- `chat_service.py` summarization helper; `chat.py` route accepting extended body; frontend POST body; tests for truncation and shape.

### Acceptance criteria

- Follow-up questions after a comparison or diagram reference the correct modules **without** the user repeating full context.

### Risks

- **Token creep** — enforce caps; never embed full code-project source in the summary.

---

## Item 4 — Expand MCP tools beyond the current four

### Objectives

- `mcp_server` exposes more than `list_modules`, `get_module`, `compare_modules`, `list_categories`, aligned with advisor data access (search, knowledge, stack suggestion, etc.).

### Current behavior (baseline)

- `mcp_server/src/ai_advisor_mcp/server.py` defines four tools and delegates to `AIAdvisorClient`.

### Design

#### 1. REST-first

- Keep MCP thin: **new FastAPI routes** that mirror tool logic, then **SDK methods**, then MCP `tools/list` + `call_tool`.

Examples:

- **Search modules** — `GET /api/v1/modules` with `search` already exists; MCP can expose `search_modules` mapping query params.
- **Knowledge search** — `POST /api/v1/knowledge/search` with body `{ query, module_slugs?, limit? }` delegating to `ModuleService` semantic search.
- **Stack suggestion** — `POST /api/v1/stack/suggest` (or `/advisor/suggest-stack`) with `{ use_case, constraints }` returning JSON; **share implementation** with `_tool_suggest_stack` via a extracted **`StackSuggestionService`** (or shared function) to avoid drift.

#### 2. SDK

- Add methods on `sdk/src/ai_advisor/client.py` for each new endpoint (sync first; async in Item 5).

#### 3. MCP

- Extend `create_tool_definitions()` and `call_tool()` to match.

### Deliverables

- New router modules under `backend/src/api/v1/` registered in `router.py`; SDK + MCP updates.

### Acceptance criteria

- An MCP client can run knowledge search and stack suggestion **without** using the chat SSE endpoint.

### Risks

- **Auth**: new routes must use the same **`get_current_user`** / dev bearer pattern as existing APIs.

---

## Item 5 — Polish SDK streaming (async, types, docs, robustness)

### Objectives

- Improve developer experience around **existing** streaming `chat()` on `AIAdvisorClient`—not to add chat from scratch.

### Current behavior (baseline)

- `sdk/src/ai_advisor/client.py` includes `chat()` using sync `httpx` streaming and yields `dict` events parsed from SSE lines.

### Design

#### 1. Types

- Discriminated **TypedDict**s or small dataclasses: `MetaEvent`, `TextEvent`, `PanelCommandEvent`, `ErrorEvent`, `DoneEvent`, etc.

#### 2. Async client

- `AsyncAIAdvisorClient` with `httpx.AsyncClient` and `async def chat_stream(...) -> AsyncIterator[ChatEvent]`.

#### 3. Robustness

- Separate **connect** vs **read** timeouts; document long **read** timeout for SSE.
- Bounded buffer / clear errors on non-200 responses.

#### 4. Documentation

- `sdk/README.md`: installation, `BACKEND_URL`, authorization, sync vs async examples.

### Deliverables

- Refactored or split SDK modules; README; optional `examples/` script.

### Acceptance criteria

- A new developer can copy-paste an example and consume typed events without reading implementation source.

### Risks

- MCP may stay **sync**; keep sync `AIAdvisorClient` stable for `mcp_server`.

---

## Item 6 — (Optional) Structured node actions / diagram updates

### Objectives

- Architecture node actions are **structured** (operation, node id, label, optional `module_slug`) so the backend and model parse them reliably; optionally tighten the loop so the agent **updates** the diagram via existing `panel_command` `update` / `subAction` patterns.

### Current behavior (baseline)

- `InteractiveArchitecture.tsx` opens a popover and calls `sendMessage` with **natural-language** strings (“What alternatives…”, etc.). This already closes a loop but is not machine-readable.

### Design

#### 1. Request schema

- Extend `ChatRequest` with optional `client_action`, e.g.:

```json
{
  "type": "arch_node",
  "op": "swap" | "learn" | "code",
  "node_id": "string",
  "label": "string",
  "module_slug": "string | null"
}
```

#### 2. Frontend

- Replace raw-string-only sends with **`sendChatMessage({ message, client_action })`** (or equivalent) from `chatStore`, forwarded by the BFF.

#### 3. Backend

- `ChatService`: merge `client_action` into the **UI summary** (Item 3) or a fixed prefix on the user message for the model.

#### 4. Optional diagram mutation

- Prompt the model to respond with **`panel_command`** `action: "update"` and `subAction` / node payloads that `panelStore` already supports (`add_node`, `highlight`, etc.) for **swap** flows.

### Deliverables

- Schema + BFF + store + `InteractiveArchitecture.tsx` updates; prompt guidance for swap behavior.

### Acceptance criteria

- Swap/learn/code actions always expose **node id** (and slug when known) to the agent in a **stable** format.

---

## Execution order and milestones

### Strict numeric order (1 → 6)

You can implement **strictly one through six**, with this caveat:

- **Item 1 (option card tie-in)** is easier once **Item 3’s `client_context`** exists. **Item 1 core** (better `suggest_stack` without option metadata) can ship **before** Item 3.

### Suggested sprint breakdown

| Sprint | Scope | Exit criteria |
|--------|--------|----------------|
| **1a** | Item 1 — schema, tool, ranking, prompts | `suggest_stack` uses weighted scoring + broader candidate pool; manual chat validation |
| **1b** | Item 1 — option cards + `client_context` | Prefer after Item 3, or fold 3’s request extension early |
| **2** | Item 2 — all three panels + agent emission | No stub panels; realistic flows emit each type |
| **3** | Item 3 — summarization + `client_context` | Follow-up chat references prior panel correctly |
| **4** | Item 4 — REST + SDK + MCP | New MCP tools callable against running API |
| **5** | Item 5 — SDK types, async, README, timeouts | Documented developer path |
| **6** | Item 6 — structured node actions | Stable payloads; optional diagram updates |

---

## Historical note (fact-check summary)

Earlier gap analyses claimed the **SDK could not chat** and that **interactive node menus were missing**. The codebase **does** include:

- **`AIAdvisorClient.chat()`** — streaming SSE to `POST /advisor/chat`.
- **`InteractiveArchitecture`** — node click popover with Learn more / Swap / Show code sending messages via `sendMessage`.

This roadmap **does not** re-require those as greenfield work; Items **5** and **6** **refine** them (SDK polish and structured actions).

---

*Last updated: aligned with repository conventions and chat-derived plan. Update this file as milestones ship.*
