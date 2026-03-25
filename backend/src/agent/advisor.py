"""
AI Advisor Agent
Supports two modes:
1. Claude Code CLI (uses Max subscription, no API key)
2. Anthropic SDK (uses API credits, requires ANTHROPIC_API_KEY)
"""

import json
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.claude_code_adapter import ClaudeCodeAdapter
from src.agent.prompts import build_system_prompt
from src.agent.tools import ALL_TOOLS
from src.modules.comparison_engine import ComparisonEngine
from src.services.module_service import ModuleService


class AdvisorAgent:
    """
    The core AI advisor agent. Streams both text responses and panel commands via SSE.
    """

    def __init__(
        self,
        db: AsyncSession,
        anthropic_api_key: str = "",
        model: str = "claude-opus-4-20250514",
        use_claude_code: bool = True,
    ):
        self.db = db
        self.model = model
        self.use_claude_code = use_claude_code
        self.module_service = ModuleService(db)
        self.comparison_engine = ComparisonEngine(db)
        self.tools = ALL_TOOLS

        if use_claude_code:
            self.claude_code = ClaudeCodeAdapter(model=model)
            self.client = None
        else:
            import anthropic
            self.claude_code = None
            self.client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)

    async def stream_response(
        self,
        messages: list[dict],
        module_count: int = 0,
        category_count: int = 0,
        catalog_section: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Process conversation through Claude.
        Yields SSE-formatted events.
        """
        system_prompt = build_system_prompt(module_count, category_count, catalog_section)

        if self.use_claude_code:
            async for event in self._stream_claude_code(system_prompt, messages):
                yield event
        else:
            async for event in self._stream_anthropic_sdk(system_prompt, messages):
                yield event

    async def _stream_claude_code(
        self,
        system_prompt: str,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        """Stream response using Claude Code CLI."""
        # Add panel command instructions to system prompt
        enhanced_prompt = system_prompt + PANEL_COMMAND_INSTRUCTIONS

        async for event in self.claude_code.stream(enhanced_prompt, messages):
            if event["type"] == "text":
                yield _sse_event("text", {"content": event["content"]})
            elif event["type"] == "panel_command":
                yield _sse_event("panel_command", {"command": event["command"]})
            elif event["type"] == "done":
                yield _sse_event("done", {})

    async def _stream_anthropic_sdk(
        self,
        system_prompt: str,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        """Stream response using Anthropic SDK (original implementation)."""
        # Agent loop: keep calling Claude until no more tool_use
        max_iterations = 10
        iteration = 0
        seen_tool_calls: set[str] = set()

        while True:
            iteration += 1
            if iteration > max_iterations:
                yield _sse_event("text", {"content": "\n\n*Reached maximum iteration limit. Stopping agent loop.*"})
                break
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
                break

            # Add assistant response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Execute tools and build tool results
            tool_results = []
            duplicate_detected = False
            for tool_block in tool_use_blocks:
                tool_name = tool_block.name
                tool_input = tool_block.input

                # Duplicate tool call detection
                call_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
                if call_key in seen_tool_calls:
                    yield _sse_event("text", {"content": "\n\nI've already tried that search. Let me work with what I found.\n"})
                    # Still provide a tool_result to satisfy the API contract
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps({"error": "Duplicate tool call skipped"}),
                    })
                    duplicate_detected = True
                    continue
                seen_tool_calls.add(call_key)

                # Emit tool activity start event
                activity_message = _tool_activity_message(tool_name, tool_input)
                yield _sse_event("tool_activity", {"tool": tool_name, "status": "running", "message": activity_message})

                result, panel_command = await self._execute_tool(
                    tool_name, tool_input
                )

                # Emit tool activity complete event
                yield _sse_event("tool_activity", {"tool": tool_name, "status": "complete"})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": json.dumps(result) if isinstance(result, dict) else str(result),
                })

                if panel_command:
                    yield _sse_event("panel_command", {"command": panel_command})

            # If all tool calls in this iteration were duplicates, break out
            if duplicate_detected and all(
                "Duplicate tool call skipped" in r.get("content", "")
                for r in tool_results
            ):
                break

            messages.append({"role": "user", "content": tool_results})

        yield _sse_event("done", {})

    async def _execute_tool(
        self, tool_name: str, tool_input: dict
    ) -> tuple[dict, dict | None]:
        """Execute a tool and return (result_data, optional_panel_command)."""
        try:
            if tool_name == "search_modules":
                return await self._tool_search_modules(tool_input)
            elif tool_name == "get_module_detail":
                return await self._tool_get_module_detail(tool_input)
            elif tool_name == "compare_modules":
                return await self._tool_compare_modules(tool_input)
            elif tool_name == "search_knowledge":
                return await self._tool_search_knowledge(tool_input)
            elif tool_name == "list_categories":
                return await self._tool_list_categories(tool_input)
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
            elif tool_name == "present_options":
                return self._tool_present_options(tool_input)
            elif tool_name == "build_architecture_step":
                return self._tool_build_architecture_step(tool_input)
            else:
                return {"error": f"Unknown tool: {tool_name}"}, None
        except Exception as e:
            return {"error": f"Tool '{tool_name}' failed: {str(e)}"}, None

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

    async def _tool_list_categories(self, input: dict) -> tuple[dict, None]:
        categories = await self.module_service.list_categories()
        return {"categories": categories, "count": len(categories)}, None

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
        use_case = input["use_case"]
        constraints = input.get("constraints", {})
        preferences = input.get("preferences", [])

        categories = [
            "data_ingestion", "chunking", "embeddings",
            "vector_databases", "retrieval", "llm_layer",
            "agent_systems", "evaluation", "deployment",
        ]
        recommended = {}
        all_nodes = []
        all_edges = []

        for cat in categories:
            modules, _ = await self.module_service.list_modules(
                category=cat, per_page=3
            )
            if modules:
                best = modules[0]
                if constraints.get("budget") == "low":
                    for m in modules:
                        if m.pricing_model in ("open_source", "free"):
                            best = m
                            break
                recommended[cat] = {
                    "slug": best.slug,
                    "name": best.name,
                    "category": cat,
                    "pricing": best.pricing_model,
                }
                all_nodes.append({
                    "id": cat,
                    "label": best.name,
                    "category": cat,
                    "module_slug": best.slug,
                })

        pipeline_order = [
            "data_ingestion", "chunking", "embeddings",
            "vector_databases", "retrieval", "llm_layer",
        ]
        for i in range(len(pipeline_order) - 1):
            src = pipeline_order[i]
            tgt = pipeline_order[i + 1]
            if src in recommended and tgt in recommended:
                all_edges.append({"source": src, "target": tgt})

        if "evaluation" in recommended and "llm_layer" in recommended:
            all_edges.append({"source": "llm_layer", "target": "evaluation", "label": "evaluate"})
        if "deployment" in recommended and "llm_layer" in recommended:
            all_edges.append({"source": "llm_layer", "target": "deployment", "label": "deploy"})

        suggestion = {
            "use_case": use_case,
            "constraints": constraints,
            "preferences": preferences,
            "recommended_stack": recommended,
            "stack_size": len(recommended),
        }

        panel_command = {
            "action": "render",
            "panel": "architecture_diagram",
            "data": {
                "nodes": all_nodes,
                "edges": all_edges,
                "layout": "left-to-right",
            },
            "title": "Recommended Architecture",
        }
        return suggestion, panel_command

    def _tool_present_options(self, input: dict) -> tuple[dict, dict]:
        """Present interactive option cards in the visual panel."""
        question = input["question"]
        options = input["options"]
        panel_command = {
            "action": "render",
            "panel": "option_cards",
            "data": {
                "question": question,
                "options": options,
            },
        }
        return {"status": "options_presented", "option_count": len(options)}, panel_command

    def _tool_build_architecture_step(self, input: dict) -> tuple[dict, dict]:
        """Incrementally build an interactive architecture diagram."""
        action = input["action"]

        if action == "init":
            title = input.get("title", "Architecture Diagram")
            panel_command = {
                "action": "render",
                "panel": "interactive_architecture",
                "data": {
                    "nodes": [],
                    "edges": [],
                    "title": title,
                },
            }
            return {"status": "diagram_initialized", "title": title}, panel_command

        elif action == "add_node":
            node = input["node"]
            panel_command = {
                "action": "update",
                "data": {
                    "subAction": "add_node",
                    "node": node,
                },
            }
            return {"status": "node_added", "node_id": node["id"]}, panel_command

        elif action == "connect":
            edge = input["edge"]
            panel_command = {
                "action": "update",
                "data": {
                    "subAction": "add_edge",
                    "edge": edge,
                },
            }
            return {"status": "edge_added", "from": edge["from"], "to": edge["to"]}, panel_command

        elif action == "highlight":
            node_id = input["node_id"]
            panel_command = {
                "action": "update",
                "data": {
                    "subAction": "highlight",
                    "nodeId": node_id,
                },
            }
            return {"status": "node_highlighted", "node_id": node_id}, panel_command

        else:
            return {"error": f"Unknown action: {action}"}, None


# Panel command instructions appended to system prompt when using Claude Code
PANEL_COMMAND_INSTRUCTIONS = """

## Panel Commands (IMPORTANT)

You can control a visual panel alongside the chat. To render visualizations, emit special markers in your response:

### Architecture Diagram
```
<!--PANEL_CMD:{"action":"render","panel":"architecture_diagram","title":"My Diagram","data":{"nodes":[{"id":"n1","label":"Pinecone","category":"vector_databases"}],"edges":[{"source":"n1","target":"n2"}],"layout":"left-to-right"}}-->
```

### Comparison Chart (radar or bar)
```
<!--PANEL_CMD:{"action":"render","panel":"comparison_chart","title":"Technology Comparison","data":{"comparison":{"modules":[...],"rankings":[...],"dimensions":[...]},"chart_type":"radar"}}-->
```

### Comparison Table
```
<!--PANEL_CMD:{"action":"render","panel":"comparison_table","title":"Technology Comparison","data":{"comparison":{"modules":[...],"rankings":[...],"dimensions":[...]}}}-->
```

### Code Preview
```
<!--PANEL_CMD:{"action":"render","panel":"code_preview","title":"Setup Example","data":{"title":"Pinecone Setup","language":"python","code":"import pinecone\\npinecone.init(api_key='...')"}}-->
```

### Option Cards (interactive choices)
```
<!--PANEL_CMD:{"action":"render","panel":"option_cards","data":{"question":"What is your budget range?","options":[{"id":"low","label":"Low Budget","description":"Open source preferred"},{"id":"medium","label":"Medium Budget","description":"Mix of open source and managed"},{"id":"high","label":"High Budget","description":"Enterprise-grade managed services"}]}}-->
```

### Interactive Architecture (incremental building)
Init:
```
<!--PANEL_CMD:{"action":"render","panel":"interactive_architecture","data":{"nodes":[],"edges":[],"title":"RAG Pipeline"}}-->
```
Add node:
```
<!--PANEL_CMD:{"action":"update","data":{"subAction":"add_node","node":{"id":"embed","label":"OpenAI Embeddings","slug":"openai_embeddings","category":"embeddings"}}}-->
```
Connect:
```
<!--PANEL_CMD:{"action":"update","data":{"subAction":"add_edge","edge":{"from":"embed","to":"vectordb","label":"store vectors"}}}-->
```
Highlight:
```
<!--PANEL_CMD:{"action":"update","data":{"subAction":"highlight","nodeId":"embed"}}-->
```

RULES:
- Place panel commands on their own line, inline with your text response
- The JSON must be valid and on a single line (no newlines inside the JSON)
- Use these markers instead of just describing what should be shown
- Always include the panel command when showing comparisons, diagrams, or code
"""


def _tool_activity_message(tool_name: str, tool_input: dict) -> str:
    """Generate a human-readable activity message for a tool call."""
    if tool_name == "search_modules":
        query = tool_input.get("query", "")
        category = tool_input.get("category", "")
        if category:
            return f"Searching {category} modules for '{query}'..."
        return f"Searching modules for '{query}'..."
    elif tool_name == "get_module_detail":
        return f"Fetching details for {tool_input.get('slug', 'module')}..."
    elif tool_name == "compare_modules":
        slugs = tool_input.get("slugs", [])
        return f"Comparing {' vs '.join(slugs)}..."
    elif tool_name == "search_knowledge":
        return f"Searching knowledge base for '{tool_input.get('query', '')}'..."
    elif tool_name == "list_categories":
        return "Listing available categories..."
    elif tool_name == "get_benchmarks":
        slugs = tool_input.get("slugs", [])
        return f"Fetching benchmarks for {', '.join(slugs)}..."
    elif tool_name == "suggest_stack":
        return "Building stack recommendation..."
    elif tool_name == "render_architecture_diagram":
        return f"Rendering architecture diagram: {tool_input.get('title', '')}..."
    elif tool_name == "render_comparison":
        return "Rendering comparison visualization..."
    elif tool_name == "render_code_example":
        return f"Rendering code example: {tool_input.get('title', '')}..."
    elif tool_name == "present_options":
        return f"Presenting options: {tool_input.get('question', '')}..."
    elif tool_name == "build_architecture_step":
        action = tool_input.get("action", "")
        if action == "init":
            return f"Initializing diagram: {tool_input.get('title', '')}..."
        elif action == "add_node":
            node = tool_input.get("node", {})
            return f"Adding component: {node.get('label', '')}..."
        elif action == "connect":
            edge = tool_input.get("edge", {})
            return f"Connecting {edge.get('from', '')} → {edge.get('to', '')}..."
        elif action == "highlight":
            return f"Highlighting: {tool_input.get('node_id', '')}..."
        return f"Building architecture: {action}..."
    return f"Running {tool_name}..."


def _sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event string."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload)}\n\n"
