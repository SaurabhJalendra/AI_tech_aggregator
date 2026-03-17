"""MCP server exposing AI Advisor tools for use in Claude Code and other MCP clients."""

import json
import sys

from ai_advisor import AIAdvisorClient

# MCP protocol uses JSON-RPC over stdio
# This is a minimal MCP server implementation


def create_tool_definitions():
    return [
        {
            "name": "list_modules",
            "description": "List AI infrastructure modules. Optionally filter by category or search term.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category slug to filter by"},
                    "search": {"type": "string", "description": "Search term"},
                    "page": {"type": "integer", "default": 1},
                },
            },
        },
        {
            "name": "get_module",
            "description": "Get detailed information about a specific AI infrastructure module by its slug.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Module slug (e.g., 'pinecone', 'langchain')"},
                },
                "required": ["slug"],
            },
        },
        {
            "name": "compare_modules",
            "description": "Compare two or more AI infrastructure modules across multiple dimensions.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "slugs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Module slugs to compare (2-5)",
                    },
                },
                "required": ["slugs"],
            },
        },
        {
            "name": "list_categories",
            "description": "List all AI infrastructure module categories with module counts.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def handle_request(request: dict, client: AIAdvisorClient) -> dict:
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "ai-advisor-mcp",
                    "version": "0.1.0",
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": create_tool_definitions()},
        }

    if method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})

        try:
            result = call_tool(tool_name, arguments, client)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True,
                },
            }

    # notifications (no response needed)
    if method.startswith("notifications/"):
        return None

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def call_tool(name: str, arguments: dict, client: AIAdvisorClient):
    if name == "list_modules":
        return client.list_modules(
            category=arguments.get("category"),
            search=arguments.get("search"),
            page=arguments.get("page", 1),
        )
    elif name == "get_module":
        return client.get_module(arguments["slug"])
    elif name == "compare_modules":
        return client.compare_modules(arguments["slugs"])
    elif name == "list_categories":
        return client.list_categories()
    else:
        raise ValueError(f"Unknown tool: {name}")


def main():
    """Run the MCP server on stdio."""
    api_url = "http://localhost:8000/api/v1"
    # Check for --api-url argument
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--api-url" and i < len(sys.argv):
            api_url = sys.argv[i + 1]

    client = AIAdvisorClient(base_url=api_url)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request, client)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
