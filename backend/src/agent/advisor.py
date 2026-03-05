"""
AI Advisor Agent
Core agent class that uses Claude Messages API with tool use and streaming.
"""

import json
from collections.abc import AsyncGenerator

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.prompts import build_system_prompt
from src.agent.tools import ALL_TOOLS
from src.modules.comparison_engine import ComparisonEngine
from src.services.module_service import ModuleService


class AdvisorAgent:
    """
    The core AI advisor agent. Uses Claude Messages API with tool use.
    Streams both text responses and panel commands via SSE.
    """

    def __init__(
        self,
        db: AsyncSession,
        anthropic_api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        self.model = model
        self.module_service = ModuleService(db)
        self.comparison_engine = ComparisonEngine(db)
        self.tools = ALL_TOOLS

    async def stream_response(
        self,
        messages: list[dict],
        module_count: int = 0,
        category_count: int = 0,
    ) -> AsyncGenerator[str, None]:
        """
        Process conversation through Claude with tool use.
        Yields SSE-formatted events.
        """
        system_prompt = build_system_prompt(module_count, category_count)

        # Agent loop: keep calling Claude until no more tool_use
        while True:
            collected_text = ""
            tool_use_blocks = []

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=self.tools,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            collected_text += event.delta.text
                            yield _sse_event("text", {"content": event.delta.text})

                response = await stream.get_final_message()

            # Collect tool use blocks from the response
            tool_use_blocks = [
                block for block in response.content if block.type == "tool_use"
            ]

            if not tool_use_blocks:
                # No tools requested — conversation turn complete
                break

            # Add assistant response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Execute tools and build tool results
            tool_results = []
            for tool_block in tool_use_blocks:
                result, panel_command = await self._execute_tool(
                    tool_block.name, tool_block.input
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": json.dumps(result) if isinstance(result, dict) else str(result),
                })

                # If tool produces a panel command, emit it
                if panel_command:
                    yield _sse_event("panel_command", {"command": panel_command})

            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})

        yield _sse_event("done", {})

    async def _execute_tool(
        self, tool_name: str, tool_input: dict
    ) -> tuple[dict, dict | None]:
        """
        Execute a tool and return (result_data, optional_panel_command).
        """
        if tool_name == "search_modules":
            return await self._tool_search_modules(tool_input)

        elif tool_name == "get_module_detail":
            return await self._tool_get_module_detail(tool_input)

        elif tool_name == "compare_modules":
            return await self._tool_compare_modules(tool_input)

        elif tool_name == "search_knowledge":
            return await self._tool_search_knowledge(tool_input)

        elif tool_name == "render_architecture_diagram":
            return self._tool_render_architecture(tool_input)

        elif tool_name == "render_comparison":
            return self._tool_render_comparison(tool_input)

        elif tool_name == "render_code_example":
            return self._tool_render_code(tool_input)

        elif tool_name == "get_benchmarks":
            return await self._tool_get_benchmarks(tool_input)

        elif tool_name == "suggest_stack":
            return await self._tool_suggest_stack(tool_input)

        else:
            return {"error": f"Unknown tool: {tool_name}"}, None

    async def _tool_search_modules(self, input: dict) -> tuple[dict, None]:
        modules, total = await self.module_service.list_modules(
            search=input.get("query"),
            category=input.get("category"),
            per_page=input.get("limit", 5),
        )
        result = {
            "modules": [
                {
                    "slug": m.slug,
                    "name": m.name,
                    "category": m.category.slug if m.category else None,
                    "tagline": m.tagline,
                    "status": m.status,
                    "pricing_model": m.pricing_model,
                }
                for m in modules
            ],
            "total": total,
        }
        return result, None

    async def _tool_get_module_detail(self, input: dict) -> tuple[dict, None]:
        module = await self.module_service.get_by_slug(input["slug"])
        if not module:
            return {"error": f"Module '{input['slug']}' not found"}, None

        result = {
            "slug": module.slug,
            "name": module.name,
            "tagline": module.tagline,
            "description": module.description,
            "status": module.status,
            "pricing_model": module.pricing_model,
            "technical_specs": module.technical_specs,
            "primary_use_cases": module.primary_use_cases,
            "comparison_scores": module.comparison_scores,
            "alternatives": module.alternatives,
            "complements": module.complements,
        }
        return result, None

    async def _tool_compare_modules(self, input: dict) -> tuple[dict, None]:
        try:
            comparison = await self.comparison_engine.compare(
                slugs=input["slugs"],
                dimensions=input.get("dimensions"),
                weights=input.get("weights"),
            )
            return comparison.model_dump(), None
        except ValueError as e:
            return {"error": str(e)}, None

    async def _tool_search_knowledge(self, input: dict) -> tuple[dict, None]:
        entries = await self.module_service.search_knowledge(
            query=input["query"],
            module_slugs=input.get("module_slugs"),
            tags=input.get("tags"),
            limit=input.get("limit", 5),
        )
        return {"entries": entries, "count": len(entries)}, None

    def _tool_render_architecture(self, input: dict) -> tuple[dict, dict]:
        panel_command = {
            "action": "render",
            "panel": "architecture_diagram",
            "data": {
                "nodes": input["nodes"],
                "edges": input["edges"],
                "layout": input.get("layout", "left-to-right"),
            },
            "title": input["title"],
        }
        return {"rendered": True, "panel": "architecture_diagram"}, panel_command

    def _tool_render_comparison(self, input: dict) -> tuple[dict, dict]:
        chart_type = input.get("chart_type", "radar")
        panel_type = "comparison_chart" if chart_type in ("radar", "bar") else "comparison_table"

        panel_command = {
            "action": "render",
            "panel": panel_type,
            "data": {
                "comparison": input["comparison_data"],
                "chart_type": chart_type,
            },
            "title": "Technology Comparison",
        }
        return {"rendered": True, "panel": panel_type}, panel_command

    def _tool_render_code(self, input: dict) -> tuple[dict, dict]:
        panel_command = {
            "action": "render",
            "panel": "code_preview",
            "data": {
                "title": input["title"],
                "language": input["language"],
                "code": input["code"],
                "module_slug": input.get("module_slug"),
            },
            "title": input["title"],
        }
        return {"rendered": True, "panel": "code_preview"}, panel_command

    async def _tool_get_benchmarks(self, input: dict) -> tuple[dict, None]:
        results = {}
        for slug in input["slugs"]:
            module = await self.module_service.get_by_slug(slug)
            if module:
                benchmarks = [
                    {
                        "name": b.name,
                        "value": float(b.value),
                        "unit": b.unit,
                        "context": b.context,
                    }
                    for b in module.benchmarks
                ]
                if input.get("benchmark_names"):
                    benchmarks = [
                        b for b in benchmarks if b["name"] in input["benchmark_names"]
                    ]
                results[slug] = benchmarks
        return {"benchmarks": results}, None

    async def _tool_suggest_stack(self, input: dict) -> tuple[dict, dict]:
        # For now, return a template recommendation
        # In production, this would use the comparison engine + knowledge search
        # to build a data-driven recommendation
        suggestion = {
            "use_case": input["use_case"],
            "constraints": input.get("constraints", {}),
            "preferences": input.get("preferences", []),
            "note": "Stack suggestion is based on available module data. Use search_modules and compare_modules for detailed analysis.",
        }

        # Render a placeholder architecture diagram
        panel_command = {
            "action": "render",
            "panel": "architecture_diagram",
            "data": {
                "nodes": [],
                "edges": [],
                "layout": "left-to-right",
            },
            "title": "Recommended Architecture",
        }
        return suggestion, panel_command


def _sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event string."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload)}\n\n"
