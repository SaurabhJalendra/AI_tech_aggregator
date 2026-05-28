"""
Adapter that uses the `claude` CLI (Claude Code) instead of the Anthropic SDK.
Uses the user's Max subscription — no API key required.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

from src.agent.claude_code_concurrency import get_windows_cli_semaphore
from src.agent.subprocess_lifecycle import terminate_subprocess
from src.core.config import settings

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter:
    """Streams responses from the claude CLI subprocess."""

    def __init__(self, model: str = "claude-opus-4-20250514"):
        self.model = model
        self._mcp_config_path: str | None = None

    def _ensure_mcp_config(self) -> str | None:
        """Create or return path to MCP config for claude CLI."""
        if self._mcp_config_path and os.path.exists(self._mcp_config_path):
            return self._mcp_config_path

        # Check for static config next to backend
        static_config = Path(__file__).parent.parent.parent / "mcp_config.json"
        if static_config.exists():
            self._mcp_config_path = str(static_config)
            return self._mcp_config_path

        # No MCP config — Claude Code will run without custom tools
        return None

    async def stream(
        self,
        system_prompt: str,
        messages: list[dict],
    ) -> AsyncGenerator[dict, None]:
        """
        Stream a response from claude CLI.

        Yields dicts with:
          {"type": "text", "content": "..."} for text chunks
          {"type": "panel_command", "command": {...}} for panel commands
          {"type": "done"} when complete
        """
        prompt = self._build_prompt(system_prompt, messages)

        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--model", self.model,
            "--no-session-persistence",
            "--disable-slash-commands",
            "--permission-mode", "bypassPermissions",
            "--max-budget-usd", "1.0",
        ]

        # Add MCP config if available
        mcp_config = self._ensure_mcp_config()
        if mcp_config:
            cmd.extend(["--mcp-config", mcp_config])

        executable = shutil.which(cmd[0])
        if not executable:
            yield {"type": "text", "content": "\n\n*Error: Claude Code CLI was not found on PATH.*"}
            yield {"type": "done"}
            return

        if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
            native_executable = (
                Path(executable).parent
                / "node_modules"
                / "@anthropic-ai"
                / "claude-code"
                / "bin"
                / "claude.exe"
            )
            if native_executable.exists():
                executable = str(native_executable)
            else:
                yield {
                    "type": "text",
                    "content": "\n\n*Error: Claude Code was found only as a Windows command shim, but the native executable could not be located.*",
                }
                yield {"type": "done"}
                return

        if os.name == "nt":
            timeout_s = settings.claude_code_timeout_seconds
            async with get_windows_cli_semaphore():
                events = await asyncio.to_thread(
                    self._run_blocking,
                    executable,
                    cmd[1:],
                    timeout_s,
                )
            for event in events:
                yield event
            yield {"type": "done"}
            return

        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                *cmd[1:],
                stdin=subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            yield {"type": "text", "content": f"\n\n*Error starting Claude Code CLI: {e}*"}
            yield {"type": "done"}
            return

        accumulated_text = ""
        stderr_lines: list[str] = []

        async def _collect_stderr() -> None:
            if process.stderr is None:
                return
            async for raw_line in process.stderr:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line:
                    stderr_lines.append(line)

        stderr_task = asyncio.create_task(_collect_stderr())

        try:
            loop = asyncio.get_running_loop()
            timeout_s = settings.claude_code_timeout_seconds
            deadline = loop.time() + timeout_s

            if process.stdout is None:
                yield {"type": "text", "content": "\n\n*Error: Claude Code subprocess did not provide stdout.*"}
                return

            async for line in process.stdout:
                if loop.time() > deadline:
                    yield {
                        "type": "text",
                        "content": f"\n\n*Error: Claude Code subprocess timed out after {timeout_s} seconds.*",
                    }
                    break

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
                                accumulated_text += text
                                # Check for panel commands embedded in text
                                for chunk in self._extract_panel_commands(text):
                                    yield chunk

                elif event_type == "result":
                    result_text = event.get("result", "")
                    if result_text and not accumulated_text:
                        # Only yield result if we haven't streamed assistant messages
                        for chunk in self._extract_panel_commands(result_text):
                            yield chunk
                    break

        except Exception as e:
            yield {"type": "text", "content": f"\n\n*Error communicating with Claude Code: {e}*"}
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                    await asyncio.wait_for(process.wait(), timeout=10.0)
                except (ProcessLookupError, TimeoutError):
                    pass
            else:
                try:
                    await process.wait()
                except ProcessLookupError:
                    pass

            try:
                await asyncio.wait_for(stderr_task, timeout=1)
            except TimeoutError:
                stderr_task.cancel()

        if not accumulated_text and process.returncode not in (0, None):
            stderr_text = "\n".join(stderr_lines[-5:]).strip()
            detail = f": {stderr_text}" if stderr_text else ""
            yield {
                "type": "text",
                "content": f"\n\n*Claude Code exited with status {process.returncode}{detail}*",
            }
            yield {
                "type": "adapter_trace",
                "trace": {
                    "exit_code": process.returncode,
                    "stderr_tail": stderr_lines[-5:],
                    "platform": "posix",
                },
            }

        yield {"type": "done"}

    def _run_blocking(self, executable: str, args: list[str], timeout_s: int) -> list[dict]:
        """Run Claude Code synchronously.

        Uvicorn's Windows event loop may not support async subprocesses. Running
        the CLI in a worker thread keeps the request path async while avoiding
        the event-loop subprocess limitation.
        """
        events: list[dict] = []
        accumulated_text = ""

        try:
            process = subprocess.Popen(
                [executable, *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            events.append({
                "type": "text",
                "content": f"\n\n*Error starting Claude Code CLI: {exc}*",
            })
            return events

        if process.stdout is not None:
            for line in process.stdout:
                decoded = line.strip()
                if not decoded:
                    continue
                try:
                    event = json.loads(decoded)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")
                if event_type == "assistant":
                    content_blocks = event.get("message", {}).get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            if text:
                                accumulated_text += text
                                events.extend(self._extract_panel_commands(text))
                elif event_type == "result":
                    result_text = event.get("result", "")
                    if result_text and not accumulated_text:
                        events.extend(self._extract_panel_commands(result_text))
                    break

        stderr = ""
        try:
            try:
                _, stderr = process.communicate(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                trace = terminate_subprocess(
                    process,
                    reason=f"claude_cli_timeout_{timeout_s}s",
                )
                logger.warning(
                    "claude_code_blocking_timeout timeout_s=%s exit_code=%s trace=%s",
                    timeout_s,
                    trace.get("exit_code"),
                    trace,
                )
                events.append({
                    "type": "text",
                    "content": f"\n\n*Error: Claude Code subprocess timed out after {timeout_s} seconds.*",
                })
                events.append({"type": "adapter_trace", "trace": {**trace, "platform": "windows"}})
                return events
        finally:
            if process.poll() is None:
                terminate_subprocess(process, reason="claude_cli_finally_cleanup")

        if not events and process.returncode not in (0, None):
            stderr_tail = stderr.strip().splitlines()[-5:] if stderr else []
            detail = f": {stderr.strip()}" if stderr and stderr.strip() else ""
            logger.warning(
                "claude_code_blocking_exit exit_code=%s stderr_tail=%s",
                process.returncode,
                stderr_tail,
            )
            events.append({
                "type": "text",
                "content": f"\n\n*Claude Code exited with status {process.returncode}{detail}*",
            })
            events.append({
                "type": "adapter_trace",
                "trace": {
                    "exit_code": process.returncode,
                    "stderr_tail": stderr_tail,
                    "platform": "windows",
                },
            })

        return events

    def _extract_panel_commands(self, text: str) -> list[dict]:
        """
        Extract panel commands from text markers like <!--PANEL_CMD:{...}-->
        Returns a list of events (text chunks and panel commands).
        """
        results = []
        marker_start = "<!--PANEL_CMD:"
        marker_end = "-->"

        remaining = text
        while marker_start in remaining:
            before, _, after = remaining.partition(marker_start)

            # Yield text before the marker
            if before:
                results.append({"type": "text", "content": before})

            # Find end of marker
            if marker_end in after:
                json_str, _, remaining = after.partition(marker_end)
                try:
                    command = json.loads(json_str)
                    results.append({"type": "panel_command", "command": command})
                except json.JSONDecodeError:
                    # Malformed panel command, treat as text
                    results.append({"type": "text", "content": f"{marker_start}{json_str}{marker_end}"})
            else:
                # No closing marker, treat rest as text
                remaining = marker_start + after
                break

        # Yield any remaining text
        if remaining:
            results.append({"type": "text", "content": remaining})

        return results

    def _build_prompt(self, system_prompt: str, messages: list[dict]) -> str:
        """Convert system prompt + message history into a single prompt string."""
        parts = []

        # System context
        parts.append(f"<system>\n{system_prompt}\n</system>")

        # Conversation history
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
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

        return "\n\n".join(parts)
