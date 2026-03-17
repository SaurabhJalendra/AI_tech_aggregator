# Local Launch & User-Testing Ready Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the AI Infrastructure Advisor fully runnable on local Windows PC using Claude Code CLI (Max subscription) instead of Anthropic API, fix all remaining gaps, and verify end-to-end.

**Architecture:** Replace the `anthropic` Python SDK in the backend advisor agent with a subprocess adapter that spawns `claude` CLI. The CLI uses the user's Max subscription (no API key needed). An enhanced MCP server provides the advisor's 9 tools to Claude Code. Missing API endpoints are added. Docker services (Postgres + Redis) are started, DB is seeded, and the full stack is verified end-to-end.

**Tech Stack:** Python 3.11+, FastAPI, `claude` CLI (v2.1.76), MCP (JSON-RPC stdio), Next.js 16, PostgreSQL 16 (pgvector), Redis 7

---

## Chunk 1: Claude Code Integration

### Task 1: Create Claude Code subprocess adapter

**Files:**
- Create: `backend/src/agent/claude_code_adapter.py`

The adapter spawns `claude -p <prompt> --output-format stream-json --verbose --model claude-opus-4-20250514` as an async subprocess. It parses the newline-delimited JSON events and yields text chunks.

Key details from testing the CLI:
- Events have `{"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}]}}` for text
- `{"type": "result", ...}` for final result
- `--output-format stream-json` requires `--verbose` flag
- MCP servers are configured via `--mcp-config <path>` pointing to a JSON file

- [ ] **Step 1: Create the adapter module**

```python
# backend/src/agent/claude_code_adapter.py
"""
Adapter that uses the `claude` CLI (Claude Code) instead of the Anthropic SDK.
Uses the user's Max subscription — no API key required.
"""

import asyncio
import json
import os
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path


class ClaudeCodeAdapter:
    """Streams responses from the claude CLI subprocess."""

    def __init__(self, model: str = "claude-opus-4-20250514"):
        self.model = model
        self._mcp_config_path = self._get_mcp_config_path()

    def _get_mcp_config_path(self) -> str:
        """Return the path to the MCP config file for claude CLI."""
        config_dir = Path(__file__).parent.parent.parent / "mcp_config.json"
        return str(config_dir)

    async def stream(
        self,
        system_prompt: str,
        messages: list[dict],
    ) -> AsyncGenerator[dict, None]:
        """
        Stream a response from claude CLI.

        Yields dicts with:
          {"type": "text", "content": "..."} for text chunks
          {"type": "done"} when complete
        """
        # Build the full prompt from message history
        prompt = self._build_prompt(system_prompt, messages)

        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--model", self.model,
        ]

        # Add MCP config if file exists
        if os.path.exists(self._mcp_config_path):
            cmd.extend(["--mcp-config", self._mcp_config_path])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async for line in process.stdout:
                decoded = line.decode("utf-8").strip()
                if not decoded:
                    continue

                try:
                    event = json.loads(decoded)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")

                if event_type == "assistant":
                    message = event.get("message", {})
                    content_blocks = message.get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            if text:
                                yield {"type": "text", "content": text}

                elif event_type == "result":
                    result_text = event.get("result", "")
                    if result_text:
                        yield {"type": "text", "content": result_text}
                    yield {"type": "done"}
                    return

        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()

        yield {"type": "done"}

    def _build_prompt(self, system_prompt: str, messages: list[dict]) -> str:
        """Convert system prompt + message history into a single prompt string."""
        parts = []
        parts.append(f"<system>\n{system_prompt}\n</system>\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                # Handle content blocks (tool results etc)
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_result":
                            text_parts.append(f"[Tool Result: {block.get('content', '')}]")
                        elif block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)

            if role == "user":
                parts.append(f"Human: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")

        parts.append("Assistant:")
        return "\n\n".join(parts)
```

- [ ] **Step 2: Verify file created**

Run: `python -c "from src.agent.claude_code_adapter import ClaudeCodeAdapter; print('OK')"`
Expected: `OK`

---

### Task 2: Create MCP config for Claude Code

**Files:**
- Create: `backend/mcp_config.json`

This tells the `claude` CLI to connect to our MCP server which provides advisor tools.

- [ ] **Step 1: Create the MCP config**

```json
{
  "mcpServers": {
    "ai-advisor": {
      "command": "python",
      "args": ["-m", "ai_advisor_mcp.server"],
      "cwd": "<absolute-path-to>/mcp_server/src",
      "env": {
        "API_BASE_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

Note: The actual path will be computed at runtime. We'll generate this config dynamically.

- [ ] **Step 2: Update adapter to generate config dynamically**

Update `_get_mcp_config_path` to write a temp config with the correct absolute paths if the static config doesn't exist.

---

### Task 3: Enhance MCP server with all advisor tools

**Files:**
- Modify: `mcp_server/src/ai_advisor_mcp/server.py`

Add the remaining 5 tools (render_architecture_diagram, render_comparison, render_code_example, get_benchmarks, suggest_stack) that currently only exist in the advisor agent. The render tools just return formatted JSON — they don't need API calls.

- [ ] **Step 1: Add render tools to MCP server**

The render tools format data into panel command JSON. They don't call any API — they just structure the input data and return it.

- [ ] **Step 2: Add get_benchmarks and suggest_stack tools**

These call the backend API like the existing tools.

- [ ] **Step 3: Verify MCP server has all 9 tools**

---

### Task 4: Rewrite advisor agent to use Claude Code

**Files:**
- Modify: `backend/src/agent/advisor.py`

Replace the `anthropic` SDK streaming with Claude Code adapter. The key change: Claude Code + MCP handles tool execution internally, so we just stream text. For panel commands, we instruct Claude to output them as `<!--PANEL_CMD:{"action":"render",...}-->` markers in its text, which we parse and emit as separate SSE events.

- [ ] **Step 1: Update advisor to support both modes**

Add a `use_claude_code: bool` parameter. When True, use the ClaudeCodeAdapter. When False, use the existing anthropic SDK (for backward compatibility).

- [ ] **Step 2: Update system prompt with panel command instructions**

Add instructions to the system prompt telling Claude to emit panel commands as `<!--PANEL_CMD:{...}-->` markers.

- [ ] **Step 3: Add panel command extraction in stream_response**

Parse text chunks for `<!--PANEL_CMD:...-->` markers, extract them, and yield as `panel_command` SSE events.

- [ ] **Step 4: Verify import chain works**

Run: `python -c "from src.agent.advisor import AdvisorAgent; print('OK')"`

---

### Task 5: Update chat service and config

**Files:**
- Modify: `backend/src/core/config.py`
- Modify: `backend/src/services/chat_service.py`

- [ ] **Step 1: Add `use_claude_code` config option**

```python
# In config.py
use_claude_code: bool = True  # Default to Claude Code
```

- [ ] **Step 2: Update chat_service to pass the flag**

```python
agent = AdvisorAgent(
    db=self.db,
    anthropic_api_key=settings.anthropic_api_key,
    model=settings.anthropic_model,
    use_claude_code=settings.use_claude_code,
)
```

- [ ] **Step 3: Add USE_CLAUDE_CODE=true to backend/.env**

---

## Chunk 2: Fix Missing Endpoint & Backend Gaps

### Task 6: Add session messages endpoint

**Files:**
- Modify: `backend/src/api/v1/sessions.py`

The frontend requests `GET /api/v1/sessions/{session_id}/messages` to load conversation history. This endpoint is missing.

- [ ] **Step 1: Add the endpoint**

```python
@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a conversation session."""
    try:
        conv_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    conversation = (await db.execute(
        select(Conversation).where(
            Conversation.id == conv_uuid,
            Conversation.user_id == user.id,
        )
    )).scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_uuid)
        .order_by(Message.sequence_num)
    )).scalars().all()

    return [
        {
            "role": msg.role,
            "content": msg.content.get("text", ""),
            "panel_commands": msg.panel_commands or [],
            "created_at": str(msg.created_at) if msg.created_at else None,
        }
        for msg in messages
    ]
```

- [ ] **Step 2: Run backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass

---

## Chunk 3: Start Services & Seed Database

### Task 7: Start Docker containers

- [ ] **Step 1: Start PostgreSQL + Redis**

```bash
cd "D:\Git repos\AI_tech_aggregator"
docker-compose up -d
```

- [ ] **Step 2: Verify containers are healthy**

```bash
docker-compose ps
```
Expected: Both `ai_advisor_db` and `ai_advisor_redis` are "Up" and healthy

---

### Task 8: Seed the database

- [ ] **Step 1: Run Alembic migrations (or create tables)**

```bash
cd backend
source .venv/Scripts/activate
python ../scripts/seed_db.py
```

- [ ] **Step 2: Verify modules loaded**

```bash
python -c "
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config import settings
from src.models.module import Module, ModuleCategory

async def check():
    engine = create_async_engine(settings.database_url)
    session = async_sessionmaker(engine)()
    modules = (await session.execute(select(func.count(Module.id)))).scalar()
    cats = (await session.execute(select(func.count(ModuleCategory.id)))).scalar()
    print(f'{modules} modules, {cats} categories')
    await session.close()
    await engine.dispose()

asyncio.run(check())
"
```
Expected: `86 modules, 18 categories` (approximately)

---

## Chunk 4: Start & Verify Full Stack

### Task 9: Start backend

- [ ] **Step 1: Start uvicorn**

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

- [ ] **Step 2: Verify health endpoint**

```bash
curl http://localhost:8000/api/v1/health
```
Expected: `{"status": "ok"}`

- [ ] **Step 3: Verify modules endpoint**

```bash
curl http://localhost:8000/api/v1/modules?page_size=3
```
Expected: JSON with `modules` array and `total` count

---

### Task 10: Start frontend

- [ ] **Step 1: Install dependencies and start**

```bash
cd frontend
npm install
npm run dev
```

- [ ] **Step 2: Verify frontend loads**

Open http://localhost:3000 in browser
Expected: Landing page with module categories

- [ ] **Step 3: Navigate to advisor**

Open http://localhost:3000/advisor
Expected: Chat panel (left) + Welcome panel (right)

---

### Task 11: End-to-end chat test

- [ ] **Step 1: Send a test message in the advisor**

Type: "What vector databases do you recommend for a RAG application?"

- [ ] **Step 2: Verify response streams**

Expected: Text appears progressively in the chat. Panel may update with comparison or architecture diagram.

- [ ] **Step 3: Verify panel commands work**

If Claude uses render tools, the right panel should show diagrams/charts/code.

---

## Chunk 5: Polish & Final Fixes

### Task 12: Fix any runtime errors found during testing

This is a catch-all task for issues discovered during the E2E test.

- [ ] **Step 1: Check browser console for errors**
- [ ] **Step 2: Check backend terminal for errors**
- [ ] **Step 3: Fix any issues found**

### Task 13: Run full test suite

- [ ] **Step 1: Backend tests**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: All 37+ tests pass

- [ ] **Step 2: Frontend tests**

```bash
cd frontend && npx vitest run
```
Expected: All 15 tests pass

- [ ] **Step 3: YAML spec validation**

```bash
cd backend && python -c "
import yaml
from pathlib import Path
specs = list(Path('../modules_registry/specs').glob('*.yaml'))
errors = 0
for f in sorted(specs):
    try:
        data = yaml.safe_load(f.read_text(encoding='utf-8'))
        assert 'meta' in data and 'slug' in data['meta']
    except Exception as e:
        print(f'  FAIL: {f.name}: {e}')
        errors += 1
print(f'{len(specs)} specs, {errors} errors')
"
```
Expected: `86 specs, 0 errors`

### Task 14: Commit all changes

- [ ] **Step 1: Stage and commit**

```bash
git add -A
git commit -m "feat: integrate Claude Code CLI, add missing endpoints, launch-ready"
```
