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

1. **Asks the right questions** — Budget? Scale? Team size? Privacy requirements? Presented as clickable option cards, not text walls.

2. **Designs the architecture live** — Builds a pipeline diagram node by node as it explains each technology choice. The user watches the system materialize.

3. **Grounds every recommendation in data** — 86 modules with structured comparison scores across 8 dimensions (performance, scalability, cost, privacy, etc.), not LLM hallucinations.

4. **Lets users interact** — Click a node to swap it for an alternative. See how the trade-offs change. Get integration code instantly.

5. **Generates starter code** — Complete multi-file projects ready to copy and run, not isolated snippets.

## The Self-Improving Architecture

This is the core design principle: **the platform grows by adding data, not code.**

```
YAML Spec (one file per technology)
    |
    v
seed_db.py (loads into PostgreSQL + pgvector)
    |
    v
Agent Tools (search, compare, recommend)
    |
    v
Claude LLM (reasons over the structured data)
    |
    v
Interactive UI (diagrams, cards, charts, code)
```

**When a new technology appears:**
1. Create one YAML file with scores, knowledge entries, and code examples
2. Run `python scripts/seed_db.py`
3. The advisor immediately knows about it — recommends it, compares it, includes it in architectures
4. No code changes. No redeployment. Just a YAML file.

### Module Spec Structure

Every technology is defined as a structured YAML spec:

```yaml
meta:
  slug: pinecone
  version: "1.0"

identity:
  name: Pinecone
  tagline: Fully managed vector database
  category: vector_databases
  pricing_model: free_tier

comparison_dimensions:
  performance:    { score: 8, justification: "Sub-100ms p99 query latency..." }
  scalability:    { score: 9, justification: "Serverless auto-scaling..." }
  ease_of_use:    { score: 9, justification: "Fully managed, simple API..." }
  cost_efficiency: { score: 5, justification: "Expensive at scale..." }
  # ... 8 dimensions total

knowledge:
  entries:
    - topic: "When to choose Pinecone"
      content: "Choose Pinecone when you need zero-ops..."

code_examples:
  - title: "Basic RAG Pipeline"
    language: python
    code: |
      from pinecone import Pinecone
      # ...

relationships:
  alternatives: [weaviate, qdrant, chromadb]
  complements: [openai_embeddings, langchain]
```

Currently: **86 modules across 18 categories.**

## How Users Access It

The platform serves everyone through multiple access methods:

| Access Method | Who It's For |
|---|---|
| **Web UI** | Product managers, CTOs, anyone exploring options |
| **REST API** | Developers building tools on top of the platform |
| **Python SDK** | Python developers who want programmatic access |
| **CLI** | Terminal-first engineers |
| **MCP Server** | AI coding tools (Claude Code, etc.) that want module data as tools |

## The Agentic Chat Experience

The advisor is not a regular chatbot. It's a tool-using agent with 13 specialized tools:

### Discovery Tools
- **search_modules** — find technologies by keyword, category, or use case
- **get_module_detail** — deep dive into one technology
- **compare_modules** — side-by-side comparison across 8 dimensions
- **search_knowledge** — semantic search across expert knowledge entries
- **list_categories** — browse the full technology landscape

### Interactive Tools
- **present_options** — show clickable option cards (user clicks to answer)
- **build_architecture_step** — build diagrams node by node (init, add_node, connect, highlight)

### Rendering Tools
- **render_comparison** — radar charts and comparison tables
- **render_code_example** — syntax-highlighted code blocks
- **render_code_project** — multi-file starter projects with file tree
- **render_architecture_diagram** — static architecture diagrams
- **suggest_stack** — generate a complete technology stack recommendation

### What the User Sees

**Step 1:** User describes their project
> "I need a RAG pipeline for 500K legal documents, SOC2 required, $500/mo budget"

**Step 2:** Advisor builds the architecture live
- Right panel: nodes appear one by one (Unstructured.io → Chunking → Voyage AI → pgvector → Hybrid Search → Claude → Langfuse)
- Left panel: streaming explanation of each choice
- Edges with labels show data flow between components

**Step 3:** User interacts
- Click a node → context menu: "Learn more", "Swap component", "Show code"
- Click "Swap component" → advisor suggests alternatives with trade-off analysis
- Click "Show code" → multi-file starter project appears

## The Business Model

| Tier | Price | Features |
|---|---|---|
| Free | $0 | 10 conversations/month, browse all 86 modules, basic comparisons |
| Pro | $29/month | Unlimited conversations, advanced comparisons, diagram export, starter code, 1K API calls |
| Team | $99/month | Everything in Pro + 10 team members, shared history, custom scoring, 10K API calls |
| API | Usage-based | Direct REST access, Python SDK, CLI, MCP integration, SLA |

The core data (all 86 modules, scores, knowledge) is always accessible. Monetization is on conversation depth, team features, and API volume.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, Zustand |
| Backend | Python 3.13, FastAPI, SQLAlchemy async, Alembic |
| Database | PostgreSQL 16 + pgvector (vector search) |
| Cache | Redis (optional, graceful fallback) |
| LLM | Anthropic Claude (SDK mode with API key, or Claude Code CLI with Max subscription) |
| Embeddings | OpenAI text-embedding-3-small (optional, text search fallback) |
| Containers | Docker Compose (PostgreSQL + Redis) |

## What Makes It Different

| Other tools | This platform |
|---|---|
| Static comparison tables | Live architecture building, node by node |
| Text-wall recommendations | Interactive option cards, clickable diagrams |
| Hallucinated opinions | Structured data with scored justifications |
| Single code snippets | Complete multi-file starter projects |
| Manual updates | Self-improving — add a YAML, platform updates |
| Web-only | Web + API + SDK + CLI + MCP |
| One-size-fits-all | Personalized to your budget, scale, team, and constraints |

## The Vision

**Make AI infrastructure decisions easy, data-driven, and visual.**

Every developer building an AI application should be able to describe what they need and watch a senior architect design the system in front of them — grounded in real data, interactive, and immediately actionable with starter code.
