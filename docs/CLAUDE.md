# AI Infrastructure Advisor Platform

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker Desktop (for PostgreSQL + pgvector + Redis)
- Claude Code CLI (for local dev with Max subscription)

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
# Edit .env: set ANTHROPIC_API_KEY or USE_CLAUDE_CODE=true
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
frontend/          Next.js 16 App Router (TypeScript, Tailwind, Zustand)
backend/           Python FastAPI (SQLAlchemy async, Alembic)
  src/agent/       LLM agent — dual-mode (Claude Code CLI or Anthropic SDK)
  src/api/v1/      REST + SSE endpoints
  src/models/      SQLAlchemy ORM models
  src/services/    Business logic
  src/modules/     Module loader + comparison engine
modules_registry/  86 YAML specs (source of truth for modules)
scripts/           Database seeding, embedding generation
```

### Core Pattern: Agent-Driven Panel
The chat agent streams SSE events with two types:
1. `{"type": "text", "content": "..."}` -> chat panel (left)
2. `{"type": "panel_command", "command": {...}}` -> main panel (right: diagrams, charts, code)

### Module Pattern
Every module is a YAML spec in `modules_registry/specs/{slug}.yaml` validated against `modules_registry/schema.yaml`. The loader (`backend/src/modules/loader.py`) reads specs into PostgreSQL.

### API Endpoints
- `POST /api/v1/advisor/chat` — SSE streaming chat (requires auth)
- `GET /api/v1/modules` — List modules (paginated, filterable)
- `GET /api/v1/modules/{slug}` — Module detail with knowledge
- `POST /api/v1/compare` — Compare modules across 8 dimensions
- `GET /api/v1/modules/categories` — List all categories
- `GET /api/v1/sessions` — User conversation history
- `GET /api/v1/health` — Health check

### Database
- PostgreSQL 16 + pgvector on Docker port **5433** (not 5432 — avoids local PG conflict)
- Redis on port 6379 (optional, graceful fallback for caching)
- 86 modules across 18 categories seeded from YAML specs

### Auth (Dev Mode)
- `Authorization: Bearer dev@example.com` auto-creates a pro-tier user
- No real auth needed for local development

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution
- Keep main context window clean

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review `tasks/lessons.md` at session start for relevant patterns

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Run `npm run build` for frontend changes, `python -c "from src.main import app"` for backend
- Test endpoints with curl after API changes
- Ask yourself: "Would a staff engineer approve this?"

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests -> then resolve them
- Zero context switching required from the user

---

## Development Rules

### Backend
- Always use `async/await` — the entire backend is async
- Database sessions via `get_db` dependency injection
- All models inherit from `Base` in `src/db/base.py`
- Agent tools in `src/agent/tools.py`, prompts in `src/agent/prompts.py`
- Run tests: `cd backend && pytest -v`

### Frontend
- All interactive components must be `'use client'`
- State management: Zustand stores only (no Redux, no Context for state)
- Styling: Tailwind only — no CSS modules, no styled-components
- Markdown rendering: `react-markdown` + `remark-gfm`
- Code highlighting: `shiki` package (NOT `@shikijs/core`)
- Run tests: `cd frontend && npm test`
- Build check: `cd frontend && npm run build`

### Git
- Commit messages: `type: description` (feat, fix, chore, refactor, test, docs)
- Never commit `.env` files — `.env.example` is the template
- No `Co-Authored-By` lines in commits

### Testing
- Backend: pytest with async fixtures (`conftest.py`)
- Frontend: vitest + @testing-library/react
- Always test after making changes — don't trust it works without proof

### Common Pitfalls
- Port 5432 conflict: local PostgreSQL vs Docker. Always use **5433**
- `@shikijs/core/engines/oniguruma` not found: use `shiki` package instead
- Multiple zombie uvicorn on Windows: `taskkill //F //PID` to clean up
- Claude CLI takes 8-15s per response (hook/plugin init overhead)
- SSE events need `data: {...}\n\n` format with double newline
