# Production readiness audit

Final stabilization checklist for the AI Infrastructure Advisor (planner + agent architecture).

## Determinism

- [x] Pipeline shortlists use `sort_scored_records()` (score → confidence → retrieval_score → slug)
- [x] Module lists `ORDER BY slug`
- [x] Comparison engine rankings use slug tie-breakers
- [x] Semantic intent tie-break on `intent_id`

## Prompt safety

- [x] `validate_client_context()` — allowlist + deep `sanitize_nested()`
- [x] `format_prompt_context()` — bounded LLM narration only
- [x] Legacy flat `constraints` rejected
- [x] Injection pattern stripping + abuse counters (`security_context.py`)

## SSE / streaming resilience

- [x] `finishOnce()` idempotent cleanup (frontend)
- [x] 180s stream timeout
- [x] `done` / error / finally paths
- [x] Vitest chaos tests + Playwright mocked SSE

## Planner continuity

- [x] `ConstraintState` only (no dual flat state)
- [x] Falsy answers preserved (`state.has()`)
- [x] Long-session tests (20+ turns)

## Negotiation flows

- [x] `filter_exhausted` → negotiation option cards (no silent fallback)

## Shadow mode

- [x] `PLANNER_MODE=shadow` — planner runs, LLM responds, `compare_shadow_outcomes()` logged

## Telemetry

- [x] `PlannerTurnTelemetry` per turn (persisted + SSE)
- [x] `GET /api/v1/advisor/metrics/internal` (dev/staging)

## Subprocess lifecycle

- [x] `terminate_subprocess()` — kill, wait, close streams
- [x] Windows blocking + Unix async cleanup

## Architecture persistence

- [x] Consulting profile + constraint_state on assistant messages
- [x] Blueprint workspace store (existing feature — not expanded in this pass)

## Browser stability

- [x] Playwright e2e with mocked `/api/chat` (stream complete, options enabled, refresh)

## Long-session behavior

- [x] `test_long_session_continuity.py`

## Concurrency safety

- [x] Parallel validation tests + metrics isolation

## Explanation integrity

- [x] Structured sanitizer — artifacts only; metrics flagged not deleted
- [x] `explanation_integrity.py` semantic preservation assertions

## Operational commands

```bash
# Backend
cd backend && pytest tests/test_production_hardening.py tests/test_e2e_advisor_hardening.py \
  tests/test_explanation_integrity.py tests/test_long_session_continuity.py \
  tests/test_concurrency.py tests/test_streaming_chaos.py -v

# Frontend unit + streaming
cd frontend && npm test

# Playwright (requires dev server or CI with PLAYWRIGHT_BASE_URL)
cd frontend && npx playwright install chromium && npm run test:e2e
```

## Environment

| Variable | Values | Purpose |
|----------|--------|---------|
| `PLANNER_MODE` | `off` \| `shadow` \| `on` | Planner kill switch |
| `PLANNER_AUTHORITY_STRICT` | `true`/`false` | LLM panel gating |
| `LLM_FALLBACK_ENABLED` | `true`/`false` | Agent fallback |
