"""Concurrency limits for Claude Code CLI on Windows (thread-pool protection)."""

from __future__ import annotations

import asyncio

from src.core.config import settings

_windows_cli_semaphore: asyncio.Semaphore | None = None


def get_windows_cli_semaphore() -> asyncio.Semaphore:
    global _windows_cli_semaphore
    if _windows_cli_semaphore is None:
        limit = max(1, int(settings.claude_code_windows_max_concurrent))
        _windows_cli_semaphore = asyncio.Semaphore(limit)
    return _windows_cli_semaphore
