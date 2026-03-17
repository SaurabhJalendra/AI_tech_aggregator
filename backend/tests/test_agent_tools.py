"""Tests for the agent tool definitions."""

from src.agent.tools import ALL_TOOLS


def test_all_tools_have_required_fields():
    """Each tool must have name, description, and input_schema."""
    for tool in ALL_TOOLS:
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert "description" in tool, f"Tool {tool.get('name')} missing 'description'"
        assert "input_schema" in tool, f"Tool {tool['name']} missing 'input_schema'"
        assert tool["input_schema"]["type"] == "object"


def test_all_tools_have_unique_names():
    """Tool names must be unique."""
    names = [t["name"] for t in ALL_TOOLS]
    assert len(names) == len(set(names)), f"Duplicate tool names: {[n for n in names if names.count(n) > 1]}"


def test_tool_schemas_have_required_fields():
    """Tools with required fields should list them in the schema."""
    for tool in ALL_TOOLS:
        schema = tool["input_schema"]
        if "required" in schema:
            props = schema.get("properties", {})
            for req in schema["required"]:
                assert req in props, f"Tool {tool['name']}: required field '{req}' not in properties"


def test_expected_tools_exist():
    """Verify all expected tools are present."""
    expected = {
        "search_modules",
        "get_module_detail",
        "compare_modules",
        "search_knowledge",
        "render_architecture_diagram",
        "render_comparison",
        "render_code_example",
        "get_benchmarks",
        "suggest_stack",
    }
    actual = {t["name"] for t in ALL_TOOLS}
    assert expected == actual
