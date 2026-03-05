"""
Generate module YAML specs using the Anthropic API.

Usage:
    python scripts/generate_module.py                    # List all pending modules
    python scripts/generate_module.py weaviate           # Generate one module
    python scripts/generate_module.py --batch chunking   # Generate all in a category
    python scripts/generate_module.py --all              # Generate all remaining
"""

import argparse
import os
import sys
import time
from pathlib import Path

import anthropic
import yaml

SPECS_DIR = Path(__file__).parent.parent / "modules_registry" / "specs"
SCHEMA_PATH = Path(__file__).parent.parent / "modules_registry" / "schema.yaml"

# Complete list of 54 modules across 18 categories
ALL_MODULES = {
    "data_ingestion": [
        {"slug": "unstructured", "name": "Unstructured", "status": "stable"},
        {"slug": "llamaparse", "name": "LlamaParse", "status": "stable"},
        {"slug": "apache_tika", "name": "Apache Tika", "status": "stable"},
    ],
    "chunking": [
        {"slug": "chunking_mechanisms", "name": "Chunking Mechanisms", "status": "stable"},
        {"slug": "langchain_text_splitters", "name": "LangChain Text Splitters", "status": "stable"},
        {"slug": "llamaindex_node_parsers", "name": "LlamaIndex Node Parsers", "status": "stable"},
    ],
    "embeddings": [
        {"slug": "embedding_models", "name": "Embedding Models", "status": "stable"},
        {"slug": "openai_embeddings", "name": "OpenAI Embeddings", "status": "stable"},
        {"slug": "cohere_embed", "name": "Cohere Embed", "status": "stable"},
        {"slug": "voyage_ai", "name": "Voyage AI", "status": "stable"},
    ],
    "vector_databases": [
        {"slug": "pinecone", "name": "Pinecone", "status": "stable"},
        {"slug": "weaviate", "name": "Weaviate", "status": "stable"},
        {"slug": "qdrant", "name": "Qdrant", "status": "stable"},
        {"slug": "chromadb", "name": "ChromaDB", "status": "stable"},
        {"slug": "milvus", "name": "Milvus", "status": "stable"},
    ],
    "retrieval": [
        {"slug": "reranking_models", "name": "Reranking Models", "status": "stable"},
        {"slug": "hybrid_search", "name": "Hybrid Search", "status": "stable"},
        {"slug": "query_transformation", "name": "Query Transformation", "status": "stable"},
    ],
    "rag_architectures": [
        {"slug": "rag_architectures", "name": "RAG Architectures", "status": "stable"},
        {"slug": "graph_rag", "name": "GraphRAG", "status": "emerging"},
        {"slug": "agentic_rag", "name": "Agentic RAG", "status": "emerging"},
    ],
    "llm_layer": [
        {"slug": "claude", "name": "Claude (Anthropic)", "status": "stable"},
        {"slug": "gpt4", "name": "GPT-4 (OpenAI)", "status": "stable"},
        {"slug": "gemini", "name": "Gemini (Google)", "status": "stable"},
        {"slug": "llama", "name": "Llama (Meta)", "status": "stable"},
        {"slug": "mistral", "name": "Mistral", "status": "stable"},
    ],
    "agent_systems": [
        {"slug": "agent_communication_protocols", "name": "Agent Communication Protocols", "status": "emerging"},
        {"slug": "langgraph", "name": "LangGraph", "status": "stable"},
        {"slug": "crewai", "name": "CrewAI", "status": "stable"},
        {"slug": "autogen", "name": "AutoGen", "status": "emerging"},
    ],
    "evaluation": [
        {"slug": "ragas", "name": "RAGAS", "status": "stable"},
        {"slug": "deepeval", "name": "DeepEval", "status": "stable"},
        {"slug": "phoenix_arize", "name": "Phoenix (Arize)", "status": "stable"},
    ],
    "caching": [
        {"slug": "semantic_caching", "name": "Semantic Caching", "status": "emerging"},
        {"slug": "gptcache", "name": "GPTCache", "status": "stable"},
        {"slug": "prompt_caching", "name": "Prompt Caching", "status": "stable"},
    ],
    "fine_tuning": [
        {"slug": "fine_tuning_strategies", "name": "Fine-Tuning Strategies", "status": "stable"},
        {"slug": "lora_qlora", "name": "LoRA / QLoRA", "status": "stable"},
        {"slug": "rlhf_dpo", "name": "RLHF & DPO", "status": "stable"},
    ],
    "deployment": [
        {"slug": "vllm", "name": "vLLM", "status": "stable"},
        {"slug": "ollama", "name": "Ollama", "status": "stable"},
        {"slug": "modal", "name": "Modal", "status": "stable"},
    ],
    "voice_conversational": [
        {"slug": "elevenlabs", "name": "ElevenLabs", "status": "stable"},
        {"slug": "whisper", "name": "Whisper (OpenAI)", "status": "stable"},
        {"slug": "livekit", "name": "LiveKit", "status": "stable"},
    ],
    "workflow_orchestration": [
        {"slug": "langchain", "name": "LangChain", "status": "stable"},
        {"slug": "llamaindex", "name": "LlamaIndex", "status": "stable"},
        {"slug": "haystack", "name": "Haystack", "status": "stable"},
    ],
    "security_compliance": [
        {"slug": "guardrails_ai", "name": "Guardrails AI", "status": "stable"},
        {"slug": "nemo_guardrails", "name": "NeMo Guardrails", "status": "stable"},
    ],
    "search_discovery": [
        {"slug": "elasticsearch_vector", "name": "Elasticsearch Vector Search", "status": "stable"},
        {"slug": "algolia_ai", "name": "Algolia AI Search", "status": "stable"},
    ],
    "specialized_applications": [
        {"slug": "code_generation", "name": "Code Generation", "status": "stable"},
        {"slug": "document_intelligence", "name": "Document Intelligence", "status": "emerging"},
    ],
}

# Reference spec for the prompt (use chunking_mechanisms as the template)
REFERENCE_SPEC = """
meta:
  slug: "pinecone"
  name: "Pinecone"
  version: "1.0.0"
  category: "vector_databases"
  subcategory: "managed"
  status: "stable"
  last_updated: "2026-02-24"
  maintainer: "system"

identity:
  tagline: "Fully managed vector database for production AI applications"
  description: |
    [2-4 paragraph description of the technology]
  website: "https://..."
  documentation: "https://..."
  github: "https://..."
  license: "..."
  pricing_model: "freemium"

capabilities:
  primary_use_cases:
    - "Use case 1"
    - "Use case 2"
  supported_operations:
    - "operation_1"
    - "operation_2"
  integrations:
    - slug: "langchain"
      type: "native"

technical_specs:
  [technology-specific structured data]

comparison_dimensions:
  performance:
    score: 8
    justification: "..."
  scalability:
    score: 9
    justification: "..."
  ease_of_use:
    score: 9
    justification: "..."
  cost_efficiency:
    score: 5
    justification: "..."
  community:
    score: 7
    justification: "..."
  maturity:
    score: 9
    justification: "..."
  flexibility:
    score: 5
    justification: "..."
  data_privacy:
    score: 7
    justification: "..."

knowledge:
  entries:
    - topic: "Topic Title"
      content: |
        [3-6 paragraphs of expert-level knowledge]
      tags: ["tag1", "tag2"]

code_examples:
  - title: "Example Title"
    language: "python"
    code: |
      [working code example]

benchmarks:
  last_run: "2026-02-20"
  results:
    - name: "metric_name"
      value: 123
      unit: "ms"
      context: "Description of test conditions"

relationships:
  alternatives:
    - slug: "alternative_slug"
      note: "Brief comparison note"
  complements:
    - slug: "complement_slug"
      role: "How it complements this module"
  typical_pipeline_position: "position"
  pipeline_predecessors: ["predecessor"]
  pipeline_successors: ["successor"]
"""

GENERATION_PROMPT = """You are an AI infrastructure expert generating a YAML specification file for a technology module in the AI Tech Aggregator platform.

Generate a complete, accurate YAML spec for the following module:
- Name: {name}
- Slug: {slug}
- Category: {category}
- Status: {status}

IMPORTANT RULES:
1. Be factually accurate. Use real URLs, real benchmarks, and real technical details.
2. Knowledge entries should be expert-level — the kind of advice a senior AI engineer would give.
3. Each knowledge entry should be 3-6 paragraphs of substantive content.
4. Include at least 4-5 knowledge entries covering: overview, when to use, trade-offs, best practices, and advanced topics.
5. Code examples must be working, real code (not pseudocode).
6. Include at least 2 code examples.
7. Comparison scores should be fair and honest (1-10 scale), with specific justifications.
8. Benchmarks should use realistic values from real-world usage.
9. Relationships should reference other modules in our system by their slug.
10. The description should be 2-4 paragraphs covering what it is, why it matters, and key differentiators.

Available module slugs for relationships: {all_slugs}

Use this template structure (output ONLY valid YAML, no markdown fences):

{template}

Generate the complete YAML spec now. Output only the YAML content, nothing else."""


def get_all_slugs():
    """Get list of all module slugs."""
    slugs = []
    for modules in ALL_MODULES.values():
        for m in modules:
            slugs.append(m["slug"])
    return slugs


def get_existing_specs():
    """Get slugs of already-generated specs."""
    existing = set()
    if SPECS_DIR.exists():
        for f in SPECS_DIR.glob("*.yaml"):
            existing.add(f.stem)
    return existing


def get_pending_modules():
    """Get modules that don't have specs yet."""
    existing = get_existing_specs()
    pending = []
    for category, modules in ALL_MODULES.items():
        for m in modules:
            if m["slug"] not in existing:
                pending.append({**m, "category": category})
    return pending


def generate_spec(slug: str, name: str, category: str, status: str) -> str:
    """Generate a module spec using Claude."""
    client = anthropic.Anthropic()

    all_slugs = ", ".join(get_all_slugs())

    prompt = GENERATION_PROMPT.format(
        name=name,
        slug=slug,
        category=category,
        status=status,
        all_slugs=all_slugs,
        template=REFERENCE_SPEC,
    )

    print(f"  Generating spec for {name} ({slug})...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text.strip()

    # Remove markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()

    return content


def validate_spec(content: str, slug: str) -> bool:
    """Basic validation of generated spec."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"  YAML parse error for {slug}: {e}")
        return False

    if not isinstance(data, dict):
        print(f"  Invalid spec for {slug}: not a dict")
        return False

    required = ["meta", "identity", "capabilities", "comparison_dimensions", "knowledge"]
    for key in required:
        if key not in data:
            print(f"  Missing required section '{key}' in {slug}")
            return False

    # Verify slug matches
    if data.get("meta", {}).get("slug") != slug:
        print(f"  Slug mismatch in {slug}: got {data.get('meta', {}).get('slug')}")
        return False

    # Verify knowledge entries exist
    entries = data.get("knowledge", {}).get("entries", [])
    if len(entries) < 3:
        print(f"  Too few knowledge entries in {slug}: {len(entries)}")
        return False

    return True


def save_spec(content: str, slug: str):
    """Save spec to file."""
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    path = SPECS_DIR / f"{slug}.yaml"
    path.write_text(content, encoding="utf-8")
    print(f"  Saved: {path}")


def generate_one(slug: str):
    """Generate a single module spec."""
    # Find module info
    module_info = None
    module_category = None
    for category, modules in ALL_MODULES.items():
        for m in modules:
            if m["slug"] == slug:
                module_info = m
                module_category = category
                break

    if not module_info:
        print(f"Unknown module slug: {slug}")
        print(f"Available slugs: {', '.join(get_all_slugs())}")
        return False

    # Check if already exists
    spec_path = SPECS_DIR / f"{slug}.yaml"
    if spec_path.exists():
        print(f"Spec already exists for {slug}. Use --force to regenerate.")
        return True

    content = generate_spec(
        slug=module_info["slug"],
        name=module_info["name"],
        category=module_category,
        status=module_info["status"],
    )

    if validate_spec(content, slug):
        save_spec(content, slug)
        return True
    else:
        # Save with .draft extension for manual review
        draft_path = SPECS_DIR / f"{slug}.yaml.draft"
        draft_path.write_text(content, encoding="utf-8")
        print(f"  Validation failed. Saved draft: {draft_path}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate module YAML specs")
    parser.add_argument("slug", nargs="?", help="Module slug to generate")
    parser.add_argument("--batch", metavar="CATEGORY", help="Generate all modules in a category")
    parser.add_argument("--all", action="store_true", help="Generate all remaining modules")
    parser.add_argument("--list", action="store_true", help="List pending modules")
    parser.add_argument("--force", action="store_true", help="Regenerate even if exists")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between API calls (seconds)")
    args = parser.parse_args()

    if args.list or (not args.slug and not args.batch and not args.all):
        pending = get_pending_modules()
        existing = get_existing_specs()
        print(f"\nExisting specs: {len(existing)}")
        print(f"Pending specs: {len(pending)}")
        print()
        for category, modules in ALL_MODULES.items():
            cat_pending = [m for m in modules if m["slug"] not in existing]
            cat_done = [m for m in modules if m["slug"] in existing]
            status = f"[{len(cat_done)}/{len(modules)}]"
            print(f"  {category} {status}")
            for m in modules:
                marker = "  [x]" if m["slug"] in existing else "  [ ]"
                print(f"    {marker} {m['slug']} ({m['name']})")
        return

    if args.slug:
        generate_one(args.slug)
        return

    # Batch or all
    if args.batch:
        if args.batch not in ALL_MODULES:
            print(f"Unknown category: {args.batch}")
            print(f"Available: {', '.join(ALL_MODULES.keys())}")
            return
        targets = [
            {**m, "category": args.batch}
            for m in ALL_MODULES[args.batch]
        ]
    elif args.all:
        targets = get_pending_modules()
    else:
        return

    existing = get_existing_specs()
    if not args.force:
        targets = [t for t in targets if t["slug"] not in existing]

    print(f"\nGenerating {len(targets)} module specs...")
    success = 0
    failed = 0

    for i, t in enumerate(targets):
        print(f"\n[{i + 1}/{len(targets)}] {t['name']}")
        try:
            content = generate_spec(t["slug"], t["name"], t["category"], t["status"])
            if validate_spec(content, t["slug"]):
                save_spec(content, t["slug"])
                success += 1
            else:
                draft_path = SPECS_DIR / f"{t['slug']}.yaml.draft"
                draft_path.write_text(content, encoding="utf-8")
                print(f"  Saved draft: {draft_path}")
                failed += 1
        except Exception as e:
            print(f"  Error: {e}")
            failed += 1

        if i < len(targets) - 1:
            time.sleep(args.delay)

    print(f"\nDone! Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    main()
