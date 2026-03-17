"""Synchronous and async HTTP client for the AI Advisor API."""

from __future__ import annotations

import json
from typing import Any, Generator

import httpx


class AIAdvisorClient:
    """Client for the AI Infrastructure Advisor API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/api/v1",
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._headers: dict[str, str] = {}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"
        self._timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self._timeout,
        )

    # -- Modules --

    def list_modules(
        self,
        category: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        with self._client() as c:
            resp = c.get("/modules", params=params)
            resp.raise_for_status()
            return resp.json()

    def get_module(self, slug: str) -> dict[str, Any]:
        with self._client() as c:
            resp = c.get(f"/modules/{slug}")
            resp.raise_for_status()
            return resp.json()

    def list_categories(self) -> list[dict[str, Any]]:
        with self._client() as c:
            resp = c.get("/modules/categories")
            resp.raise_for_status()
            return resp.json()

    def compare_modules(self, slugs: list[str], dimensions: list[str] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"slugs": slugs}
        if dimensions:
            body["dimensions"] = dimensions
        with self._client() as c:
            resp = c.post("/compare", json=body)
            resp.raise_for_status()
            return resp.json()

    # -- Chat (streaming) --

    def chat(
        self,
        message: str,
        session_id: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Send a chat message and yield SSE events."""
        body: dict[str, Any] = {"message": message}
        if session_id:
            body["session_id"] = session_id

        with self._client() as c:
            with c.stream("POST", "/advisor/chat", json=body) as resp:
                resp.raise_for_status()
                buffer = ""
                for chunk in resp.iter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                return
                            try:
                                yield json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
