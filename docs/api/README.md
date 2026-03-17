# API Reference

The AI Infrastructure Advisor exposes a REST API on port 8000.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

In development, pass a Bearer token with any email:

```
Authorization: Bearer dev@example.com
```

In production, the backend verifies NextAuth JWTs.

## Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Database + pgvector status |

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Dev login (email/password) |
| GET | `/auth/me` | Get current user profile |

### Modules

| Method | Path | Description |
|--------|------|-------------|
| GET | `/modules` | List modules (filterable) |
| GET | `/modules/categories` | List categories with counts |
| GET | `/modules/{slug}` | Get module detail |
| GET | `/modules/{slug}/knowledge` | Get knowledge entries |

**Query params for `/modules`:**
- `category` — filter by category slug
- `status` — filter by status (stable, emerging, deprecated)
- `search` — text search in name/tagline/description
- `page` — page number (default 1)
- `page_size` — items per page (default 20, max 100)

### Compare

| Method | Path | Description |
|--------|------|-------------|
| POST | `/compare` | Compare 2-5 modules |

**Request body:**
```json
{
  "slugs": ["pinecone", "weaviate"],
  "dimensions": ["performance", "cost_efficiency"],
  "weights": {"cost_efficiency": 2.0}
}
```

### Chat (SSE)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/advisor/chat` | Stream AI advisor response |

**Request body:**
```json
{
  "message": "Compare vector databases for RAG",
  "session_id": "optional-uuid"
}
```

**Response:** Server-Sent Events stream with events:
- `{"type": "text", "content": "..."}` — streamed text tokens
- `{"type": "panel_command", "command": {...}}` — UI panel updates
- `{"type": "meta", "session_id": "uuid"}` — session metadata
- `{"type": "done"}` — stream complete

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sessions` | List user conversations |
| GET | `/users/me` | User profile + usage stats |

## Comparison Dimensions

The 8 standard comparison dimensions (1-10 scale):

1. **performance** — Speed, throughput, latency
2. **scalability** — Ability to handle growth
3. **ease_of_use** — Developer experience, docs, SDK quality
4. **cost_efficiency** — Total cost of ownership
5. **community** — Community size, ecosystem, support
6. **maturity** — Production readiness, stability
7. **flexibility** — Customization, extensibility
8. **data_privacy** — Data sovereignty, compliance options
