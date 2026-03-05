# AI Infrastructure Advisor Platform

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker Desktop (for PostgreSQL + pgvector)

### Setup
```bash
# Start database
docker-compose up -d

# Backend
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env with your ANTHROPIC_API_KEY
python ../scripts/seed_db.py
uvicorn src.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Key URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Architecture

### Monorepo Layout
- `frontend/` — Next.js App Router (TypeScript, Tailwind, Zustand)
- `backend/` — Python FastAPI (SQLAlchemy async, Alembic)
- `modules_registry/specs/` — YAML spec files (source of truth for modules)
- `scripts/` — Database seeding, module generation

### Core Pattern: Agent-Driven Panel
The chat agent streams SSE events with two types:
1. `{"type": "text", "content": "..."}` → chat panel
2. `{"type": "panel_command", "command": {...}}` → main panel (diagrams, charts, code)

### Module Pattern
Every module is a YAML spec in `modules_registry/specs/{slug}.yaml` validated against `modules_registry/schema.yaml`. The loader (`backend/src/modules/loader.py`) reads specs into PostgreSQL.

### API Endpoints
- `POST /api/v1/advisor/chat` — SSE streaming chat
- `GET /api/v1/modules` — List modules
- `GET /api/v1/modules/{slug}` — Module detail
- `POST /api/v1/compare` — Compare modules
- `GET /api/v1/modules/categories` — List categories

## Development

### Adding a New Module
1. Create YAML spec in `modules_registry/specs/{slug}.yaml`
2. Validate against `modules_registry/schema.yaml`
3. Run `python scripts/seed_db.py` to load into DB

### Backend Development
```bash
cd backend && source .venv/Scripts/activate
uvicorn src.main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend && npm run dev
```

### Running Tests
```bash
cd backend && pytest
cd frontend && npm test
```
