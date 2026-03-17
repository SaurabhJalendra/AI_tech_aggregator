# Architecture

## System Overview

```
                    +-----------------+
                    |   Next.js 16    |
                    |   Frontend      |
                    |   (port 3000)   |
                    +--------+--------+
                             |
                    BFF Proxy (/api/chat)
                             |
                    +--------v--------+
                    |   FastAPI       |
                    |   Backend       |
                    |   (port 8000)   |
                    +---+--------+---+
                        |        |
              +---------+        +---------+
              |                            |
     +--------v--------+         +--------v--------+
     |  PostgreSQL 16   |         |  Claude API     |
     |  + pgvector      |         |  (Anthropic)    |
     +------------------+         +-----------------+
```

## Agent Architecture

The core pattern is an **agentic tool-use loop**:

1. User sends a message via SSE endpoint
2. `ChatService` loads conversation history and delegates to `AdvisorAgent`
3. Agent sends messages + tool definitions to Claude's Messages API (streaming)
4. Claude responds with text and/or tool_use blocks
5. Agent executes tools (DB queries, render commands)
6. Tool results are fed back to Claude as `tool_result` messages
7. Loop continues until Claude responds with text only (no tools)
8. Text is streamed to the chat panel; panel commands update the main panel

## SSE Event Protocol

The backend emits two types of SSE events:

```
data: {"type": "text", "content": "Here's what I found..."}

data: {"type": "panel_command", "command": {"action": "render", "panel": "comparison_chart", ...}}
```

## Module System

Modules are the core content unit:

```
modules_registry/specs/*.yaml  -->  loader.py  -->  PostgreSQL
```

Each YAML spec follows `schema.yaml` and contains:
- Identity (name, tagline, description, links)
- Capabilities (use cases, operations, integrations)
- Technical specs (technology-specific structured data)
- Comparison dimensions (8 scored dimensions, 1-10)
- Knowledge entries (expert-level content, embeddable)
- Code examples (working code snippets)
- Benchmarks (performance data)
- Relationships (alternatives, complements, pipeline position)

## Database Schema

Key tables:
- `modules` — Core module data + JSON fields for flexible content
- `module_knowledge` — Knowledge entries with pgvector embeddings
- `module_categories` — 18 categories with display ordering
- `conversations` / `messages` — Chat history
- `users` / `teams` — Auth and access control
- `benchmarks` — Performance data per module
- `comparisons` — Cached comparison results

## Frontend Architecture

- **Next.js App Router** with route groups: `(public)` and `(dashboard)`
- **Zustand stores**: `chatStore` (messages, streaming), `panelStore` (panel state), `authStore` (user)
- **30/70 split layout**: Chat panel (left) + Main panel (right)
- **Panel types**: Welcome, Architecture Diagram, Comparison Chart/Table, Code Preview
