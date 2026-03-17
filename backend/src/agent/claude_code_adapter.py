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

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        accumulated_text = ""
        last_yielded_pos = 0

        try:
            deadline = asyncio.get_event_loop().time() + 120

            async for line in process.stdout:
                if asyncio.get_event_loop().time() > deadline:
                    yield {"type": "text", "content": "\n\n*Error: Claude Code subprocess timed out after 120 seconds.*"}
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
                    await process.wait()
                except ProcessLookupError:
                    pass

        yield {"type": "done"}

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
