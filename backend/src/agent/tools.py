"""Tool definitions for the AI advisor agent."""

TOOL_SEARCH_MODULES = {
    "name": "search_modules",
    "description": (
        "Search for technology modules by keyword, category, or use case. "
        "Use this when the user mentions a technology or asks about options in a category. "
        "Returns a list of matching modules with their key attributes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (technology name, category, or use case description)",
            },
            "category": {
                "type": "string",
                "description": "Optional: filter by category slug",
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

TOOL_GET_MODULE_DETAIL = {
    "name": "get_module_detail",
    "description": (
        "Get detailed information about a specific technology module including "
        "its capabilities, technical specs, comparison scores, and relationships. "
        "Use this when the user asks about a specific technology."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "slug": {
                "type": "string",
                "description": "The module slug (e.g., 'pinecone', 'chunking_mechanisms')",
            },
        },
        "required": ["slug"],
    },
}

TOOL_COMPARE_MODULES = {
    "name": "compare_modules",
    "description": (
        "Compare 2-5 technology modules across dimensions like performance, "
        "cost, scalability, and ease of use. This produces structured comparison "
        "data with rankings and recommendations. Always follow this with "
        "render_comparison to show the results visually."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "slugs": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 5,
                "description": "Module slugs to compare",
            },
            "dimensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific dimensions to compare (omit for all 8 dimensions)",
            },
            "weights": {
                "type": "object",
                "description": (
                    "Priority weights for dimensions. Higher weight = more important. "
                    "Example: {'cost_efficiency': 2.0, 'performance': 1.5}"
                ),
            },
        },
        "required": ["slugs"],
    },
}

TOOL_SEARCH_KNOWLEDGE = {
    "name": "search_knowledge",
    "description": (
        "Semantic search over all module knowledge entries. "
        "Use this to find specific information about technologies, "
        "best practices, integration patterns, limitations, or trade-offs. "
        "Returns relevant knowledge snippets from across all modules."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query to search the knowledge base",
            },
            "module_slugs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: limit search to specific modules",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: filter by knowledge entry tags (e.g., 'performance', 'cost', 'integration')",
            },
            "limit": {
                "type": "integer",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

TOOL_RENDER_ARCHITECTURE = {
    "name": "render_architecture_diagram",
    "description": (
        "Render an interactive architecture diagram in the main panel showing "
        "how technologies connect in a pipeline. Use this when recommending "
        "a stack or explaining how components fit together. Each node represents "
        "a technology and edges show data flow."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title for the diagram",
            },
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "category": {"type": "string"},
                        "module_slug": {"type": "string"},
                    },
                    "required": ["id", "label", "category"],
                },
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "label": {"type": "string"},
                    },
                    "required": ["source", "target"],
                },
            },
            "layout": {
                "type": "string",
                "enum": ["left-to-right", "top-to-bottom"],
                "default": "left-to-right",
            },
        },
        "required": ["title", "nodes", "edges"],
    },
}

TOOL_RENDER_COMPARISON = {
    "name": "render_comparison",
    "description": (
        "Render a comparison visualization (table and/or chart) in the main panel. "
        "Call this after compare_modules to display results visually. "
        "Accepts the comparison result data and a chart type."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "comparison_data": {
                "type": "object",
                "description": "The comparison result from compare_modules",
            },
            "chart_type": {
                "type": "string",
                "enum": ["radar", "bar", "table"],
                "default": "radar",
                "description": "Type of visualization to render",
            },
        },
        "required": ["comparison_data"],
    },
}

TOOL_RENDER_CODE = {
    "name": "render_code_example",
    "description": (
        "Display a code example in the main panel with syntax highlighting. "
        "Use this when showing integration examples, setup code, or implementation patterns."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "language": {"type": "string"},
            "code": {"type": "string"},
            "module_slug": {
                "type": "string",
                "description": "Optional: the module this code relates to",
            },
        },
        "required": ["title", "language", "code"],
    },
}

TOOL_GET_BENCHMARKS = {
    "name": "get_benchmarks",
    "description": (
        "Retrieve benchmark data for one or more modules. "
        "Use when the user asks about performance numbers, latency, throughput, or speed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "slugs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Module slugs to get benchmarks for",
            },
            "benchmark_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: specific benchmark names to filter",
            },
        },
        "required": ["slugs"],
    },
}

TOOL_LIST_CATEGORIES = {
    "name": "list_categories",
    "description": (
        "List all available technology categories with their module counts. "
        "Use this when the user asks what categories or types of technologies are available, "
        "or when you need to understand the full scope of the catalog."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
    },
}

TOOL_SUGGEST_STACK = {
    "name": "suggest_stack",
    "description": (
        "Given a detailed use case description, suggest a complete technology stack "
        "spanning all relevant pipeline stages (ingestion, chunking, embedding, "
        "storage, retrieval, LLM, etc.). This also renders an architecture diagram. "
        "Use when the user describes their project and wants a full recommendation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "use_case": {
                "type": "string",
                "description": "Detailed description of the user's use case",
            },
            "constraints": {
                "type": "object",
                "description": "Known constraints",
                "properties": {
                    "budget": {"type": "string", "enum": ["low", "medium", "high"]},
                    "team_size": {"type": "string", "enum": ["solo", "small", "medium", "large"]},
                    "privacy": {
                        "type": "string",
                        "enum": ["public_cloud_ok", "private_required", "on_prem_required"],
                    },
                    "scale": {"type": "string", "enum": ["prototype", "startup", "enterprise"]},
                },
            },
            "preferences": {
                "type": "array",
                "items": {"type": "string"},
                "description": "User preferences (e.g., 'prefer open source', 'need Python SDK')",
            },
        },
        "required": ["use_case"],
    },
}


TOOL_PRESENT_OPTIONS = {
    "name": "present_options",
    "description": (
        "Present interactive option cards to the user in the visual panel. "
        "Use this instead of listing options as text when you want the user to "
        "choose between 2-6 options. Each option becomes a clickable card. "
        "The user's selection is automatically sent as a chat message."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question being asked of the user",
            },
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Unique identifier for this option",
                        },
                        "label": {
                            "type": "string",
                            "description": "Short display label for the option card",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional longer description shown on the card",
                        },
                        "icon": {
                            "type": "string",
                            "description": "Optional icon identifier for the card",
                        },
                    },
                    "required": ["id", "label"],
                },
                "minItems": 2,
                "maxItems": 6,
                "description": "The options to present as clickable cards",
            },
        },
        "required": ["question", "options"],
    },
}

TOOL_BUILD_ARCHITECTURE_STEP = {
    "name": "build_architecture_step",
    "description": (
        "Add a node or connection to the interactive architecture diagram. "
        "Call multiple times to build incrementally. Actions: init (start diagram), "
        "add_node (add component), connect (add edge), highlight (focus a node)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["init", "add_node", "connect", "highlight"],
                "description": "The action to perform on the diagram",
            },
            "title": {
                "type": "string",
                "description": "Title for the diagram (used with init action)",
            },
            "node": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "slug": {"type": "string", "description": "Optional module slug"},
                    "category": {"type": "string", "description": "Optional category"},
                    "description": {"type": "string", "description": "Optional description"},
                },
                "required": ["id", "label"],
                "description": "Node to add (used with add_node action)",
            },
            "edge": {
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "label": {"type": "string", "description": "Optional edge label"},
                },
                "required": ["from", "to"],
                "description": "Edge to add (used with connect action)",
            },
            "node_id": {
                "type": "string",
                "description": "Node ID to highlight (used with highlight action)",
            },
        },
        "required": ["action"],
    },
}


ALL_TOOLS = [
    TOOL_SEARCH_MODULES,
    TOOL_GET_MODULE_DETAIL,
    TOOL_COMPARE_MODULES,
    TOOL_SEARCH_KNOWLEDGE,
    TOOL_LIST_CATEGORIES,
    TOOL_RENDER_ARCHITECTURE,
    TOOL_RENDER_COMPARISON,
    TOOL_RENDER_CODE,
    TOOL_GET_BENCHMARKS,
    TOOL_SUGGEST_STACK,
    TOOL_PRESENT_OPTIONS,
    TOOL_BUILD_ARCHITECTURE_STEP,
]
