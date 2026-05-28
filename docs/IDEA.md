# AI Infrastructure Advisor — The Idea

## The Problem

Building an AI application today means choosing from hundreds of technologies across dozens of categories — vector databases, embedding models, LLM providers, agent frameworks, retrieval strategies, evaluation tools, and more.

A developer trying to build a RAG pipeline faces questions like:
- Pinecone or Qdrant or Weaviate? What about pgvector?
- OpenAI embeddings or Voyage AI or Cohere?
- LangChain or LlamaIndex or Haystack?
- How do these connect? What's the data flow?
- What will this cost at 500K documents?
- Can I meet SOC2 compliance with this stack?

They spend weeks reading documentation, watching comparison videos, asking on forums. They still pick wrong because every tool markets itself as "the best" and real-world trade-offs are buried in fine print.

## The Solution

A **living knowledge platform** with an AI advisor that acts like a senior architect — it doesn't just list tools, it **understands your constraints** and **designs the system visually in front of you**.

### What It Does

1. **Asks the right questions** — Budget? Scale? Deployment? Presented as **option cards** and intent clarification chips, not only free text.

2. **Designs the architecture live** — React Flow canvas with pipeline stages; nodes for ingestion → chunking → embeddings → vector store → retrieval → LLM → evaluation.

3. **Grounds every recommendation in data** — **102 modules** with structured comparison scores across 8 dimensions, plus playbook-specific **decision metadata** and deterministic **pipelines** (not LLM-only rankings).

4. **Lets users interact** — Click architecture nodes (Learn / Swap / Code), pick option cards, inspect **explainability** (scores, filters, shortlist) in the comparison decision surface.

5. **Generates starter code** — Single snippets (`code_preview`) and multi-file **`code_project`** panels.

## The Self-Improving Architecture

**The platform grows by adding data, not code.**

```
YAML Spec (one file per technology)
    |
    v
seed_db.py + advisor_registry overlays
    |
    v
PostgreSQL + pgvector (BGE 1024-dim knowledge embeddings)
    |
    v
Playbooks + Pipelines (deterministic retrieve → filter → score → shortlist)
    |
    v
Claude LLM (fallback narration + tools; constrained when playbook active)
    |
    v
Interactive UI (diagrams, decision surface, cards, code)
```

**When a new technology appears:**
1. Create one YAML file with scores, knowledge entries, and code examples
2. Run `python scripts/seed_db.py` (+ `sync_decision_metadata.py` if using decision overlays)
3. Optionally run `generate_embeddings.py` for semantic search
4. The advisor immediately knows about it — no application redeploy for catalog data

### Module Spec Structure

Every technology is defined as structured YAML under `modules_registry/specs/` (see `schema.yaml`).

**Scale:** 102 modules, 18 categories (17 with specs). Largest category: `llm_layer` (30 modules, including 19 `foundation_model` subcategory entries).

**Comparison dimensions (8):** performance, scalability, ease_of_use, cost_efficiency, community, maturity, flexibility, data_privacy.

## How Users Access It

| Access Method | Who It's For |
|---|---|
| **Web UI** | Product managers, CTOs, anyone exploring options |
| **REST API** | Developers building tools on top of the platform |
| **Python SDK** | Programmatic access (including streaming `chat()`) |
| **CLI** | Terminal-first engineers |
| **MCP Server** | AI coding tools (Claude Code, etc.) — subset of catalog tools |

## The Advisor Experience (Two Layers)

### Layer 1 — Deterministic planner (Phase-2, shipped)

Before (or instead of) open-ended LLM tool use:

- **Semantic intent** — BGE similarity to exemplars; clarification when ambiguous
- **Playbooks** — `vector_db_comparison`, `rag_pipeline_design`, `module_code`, `architecture_review`, `local_ai_stack`, category comparisons
- **Constraint state** — slots with provenance (`option_card`, `inferred`, `explicit`, …)
- **Pipelines** — retrieve → filter → score → shortlist; **`AdvisorTrace`** for explainability
- **Panel validator** — blocks conflicting LLM panel commands when a playbook owns the UX

### Layer 2 — Tool-using agent (dual-mode)

**Discovery tools:** `search_modules`, `get_module_detail`, `compare_modules`, `search_knowledge`, `list_categories`

**Interactive tools:** `present_options`, `build_architecture_step`

**Rendering tools:** `render_comparison`, `render_code`, `render_architecture_diagram`, `render_code_project`, `suggest_stack`, `get_benchmarks`

**Modes:** Anthropic SDK (native tools) or Claude Code CLI (panel HTML comment markers).

### What the User Sees

**Step 1:** User describes their project (or picks a starter prompt / clarification chip)

**Step 2:** Advisor runs a playbook
- Right panel: comparison decision surface, architecture canvas, or option cards
- Left panel: streamed explanation grounded in trace/explain payload
- Optional: `TraceDebugPanel` for developers

**Step 3:** User interacts
- Option cards → `client_context.option_answer` → updated constraints
- Architecture node drawer → chat with structured context
- Follow-up turns reuse `constraint_state` and panel snapshot in `client_context`

## The Business Model (target)

| Tier | Price | Features |
|---|---|---|
| Free | $0 | Limited conversations/month, browse modules, basic comparisons |
| Pro | $29/month | Unlimited conversations, advanced comparisons, diagram export, starter code, API quota |
| Team | $99/month | Team seats, shared history, custom scoring |
| API | Usage-based | REST, SDK, CLI, MCP |

Monetization is on conversation depth, team features, and API volume — core catalog data remains accessible for discovery.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind v4, Zustand, `@xyflow/react`, Recharts, Shiki |
| Backend | Python 3.11+, FastAPI, SQLAlchemy async, Alembic |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis (optional) |
| LLM | Anthropic Claude (SDK or Claude Code CLI) |
| Embeddings | Local BGE (`bge-large-en-v1.5`, 1024-dim) |
| Containers | Docker Compose (Postgres **5433**, Redis 6379) |

## What Makes It Different

| Other tools | This platform |
|---|---|
| Static comparison tables | Live decision surface + architecture canvas |
| Text-wall recommendations | Option cards + intent clarification |
| Hallucinated opinions | Scored specs + pipeline traces + explainability drawer |
| Single code snippets | Multi-file `code_project` panel |
| Manual updates | Add YAML → seed → advisor knows immediately |
| Web-only | Web + API + SDK + CLI + MCP |
| One-size-fits-all | Constraint slots + playbook-specific scoring |

## The Vision

**Make AI infrastructure decisions easy, data-driven, and visual.**

Every developer building an AI application should describe what they need and see a senior-architect-quality recommendation — grounded in structured data, inspectable scoring, and immediately actionable starter code.

---

See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for remaining gaps (placeholder panels, MCP expansion, SDK polish).
