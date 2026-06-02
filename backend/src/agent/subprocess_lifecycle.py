"""Defensive subprocess termination for Claude Code adapter."""

from __future__ import annotations

import logging
import subprocess
import time
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_WAIT_TIMEOUT = 10.0


def terminate_subprocess(
    process: subprocess.Popen,
    *,
    reason: str,
    wait_timeout: float = DEFAULT_WAIT_TIMEOUT,
) -> dict[str, Any]:
    """Kill, wait, and close streams — returns trace event for observability."""
    started = time.monotonic()
    trace: dict[str, Any] = {
        "event": "subprocess_terminated",
        "reason": reason,
        "pid": process.pid,
        "killed": False,
        "waited": False,
        "returncode": None,
        "duration_ms": 0,
    }

    try:
        if process.poll() is None:
            process.kill()
            trace["killed"] = True
            logger.warning("subprocess kill pid=%s reason=%s", process.pid, reason)
    except OSError as exc:
        trace["kill_error"] = str(exc)

    try:
        process.wait(timeout=wait_timeout)
        trace["waited"] = True
        trace["returncode"] = process.returncode
    except subprocess.TimeoutExpired:
        trace["wait_timeout"] = True
        logger.error("subprocess wait timeout pid=%s reason=%s", process.pid, reason)
    except OSError as exc:
        trace["wait_error"] = str(exc)
    finally:
        for stream in (process.stdout, process.stderr, process.stdin):
            if stream is not None and hasattr(stream, "close"):
                try:
                    stream.close()
                except OSError:
                    pass

    trace["duration_ms"] = int((time.monotonic() - started) * 1000)
    return trace
