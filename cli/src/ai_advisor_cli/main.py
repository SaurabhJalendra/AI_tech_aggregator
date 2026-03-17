"""CLI entry point for the AI Infrastructure Advisor."""

import argparse
import sys
import json

from ai_advisor import AIAdvisorClient


def get_client(args) -> AIAdvisorClient:
    return AIAdvisorClient(
        base_url=args.api_url,
        api_key=args.api_key,
    )


def cmd_modules(args):
    """List modules."""
    client = get_client(args)
    data = client.list_modules(
        category=args.category,
        search=args.search,
        page=args.page,
    )
    modules = data.get("modules", [])
    if not modules:
        print("No modules found.")
        return

    for m in modules:
        status = m.get("status", "")
        print(f"  {m['slug']:30s} {m.get('name', ''):30s} [{status}]")
    print(f"\nTotal: {data.get('total', len(modules))}")


def cmd_module_detail(args):
    """Show module detail."""
    client = get_client(args)
    data = client.get_module(args.slug)
    print(f"\n{data['name']} ({data['slug']})")
    print(f"  {data.get('tagline', '')}")
    print(f"  Status: {data.get('status', 'unknown')}")
    print(f"  Category: {data.get('category', {}).get('name', 'N/A')}")

    scores = data.get("comparison_scores", {})
    if scores:
        print("\n  Scores:")
        for dim, info in scores.items():
            score = info.get("score", info.get("value", "?"))
            print(f"    {dim:20s}: {score}/10")

    use_cases = data.get("primary_use_cases", [])
    if use_cases:
        print("\n  Use Cases:")
        for uc in use_cases:
            print(f"    - {uc}")


def cmd_categories(args):
    """List categories."""
    client = get_client(args)
    cats = client.list_categories()
    for cat in cats:
        count = cat.get("module_count", 0)
        print(f"  {cat['slug']:30s} {cat['name']:30s} ({count} modules)")


def cmd_compare(args):
    """Compare modules."""
    client = get_client(args)
    data = client.compare_modules(args.slugs)
    rankings = data.get("rankings", [])
    if rankings:
        print("\nRankings:")
        for r in rankings:
            print(f"  #{r.get('rank', '?')} {r.get('slug', '?'):20s} avg={r.get('avg_score', 0):.1f}")


def cmd_chat(args):
    """Interactive chat with the advisor."""
    client = get_client(args)
    session_id = None

    print("AI Infrastructure Advisor (type 'quit' to exit)")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print("\nAdvisor: ", end="", flush=True)
        for event in client.chat(user_input, session_id=session_id):
            if event.get("type") == "text":
                print(event.get("content", ""), end="", flush=True)
            elif event.get("type") == "meta" and event.get("session_id"):
                session_id = event["session_id"]
            elif event.get("type") == "panel_command":
                cmd = event.get("command", {})
                panel = cmd.get("panel", "unknown")
                print(f"\n  [Panel: {panel}]", end="", flush=True)
        print()


def main():
    parser = argparse.ArgumentParser(
        prog="ai-advisor",
        description="AI Infrastructure Advisor CLI",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/api/v1",
        help="API base URL",
    )
    parser.add_argument("--api-key", default=None, help="API key for authentication")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # modules
    p_modules = subparsers.add_parser("modules", help="List modules")
    p_modules.add_argument("--category", help="Filter by category slug")
    p_modules.add_argument("--search", help="Search term")
    p_modules.add_argument("--page", type=int, default=1)

    # module detail
    p_detail = subparsers.add_parser("module", help="Show module detail")
    p_detail.add_argument("slug", help="Module slug")

    # categories
    subparsers.add_parser("categories", help="List categories")

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare modules")
    p_compare.add_argument("slugs", nargs="+", help="Module slugs to compare")

    # chat
    subparsers.add_parser("chat", help="Interactive chat with the advisor")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "modules": cmd_modules,
        "module": cmd_module_detail,
        "categories": cmd_categories,
        "compare": cmd_compare,
        "chat": cmd_chat,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
