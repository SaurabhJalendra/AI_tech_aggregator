"""
Scaffold foundation_model YAML specs for llm_layer expansion.

Usage (from repo root):
    python scripts/scaffold_foundation_model_specs.py
    cd backend && python ../scripts/seed_db.py
"""

from __future__ import annotations

from pathlib import Path
import textwrap

import yaml

SPECS_DIR = Path(__file__).parent.parent / "modules_registry" / "specs"

# Scores: performance, scalability, ease_of_use, cost_efficiency, community, maturity, flexibility, data_privacy
FOUNDATION_MODELS: list[dict] = [
    # Frontier proprietary
    {
        "slug": "gpt4_1",
        "name": "OpenAI GPT-4.1",
        "tagline": "OpenAI's latest frontier GPT family tuned for coding, instruction following, and production agents",
        "pricing_model": "paid",
        "license": "Proprietary",
        "website": "https://openai.com",
        "docs": "https://platform.openai.com/docs",
        "github": "https://github.com/openai/openai-python",
        "family": "OpenAI",
        "scores": (10, 9, 9, 6, 10, 9, 9, 7),
        "use_cases": ["Agentic workflows", "Complex coding", "Multimodal apps", "Enterprise assistants"],
        "alternatives": ["claude_sonnet", "gemini_1_5_pro", "gpt4"],
        "strengths": ["Top-tier reasoning and coding", "Largest ecosystem", "Structured outputs and tools"],
        "weaknesses": ["Premium cost at full tier", "No self-hosted weights", "128K context vs some peers"],
    },
    {
        "slug": "claude_opus",
        "name": "Claude Opus",
        "tagline": "Anthropic's highest-capability Claude tier for deep reasoning and agentic work",
        "pricing_model": "paid",
        "license": "Proprietary",
        "website": "https://www.anthropic.com/claude",
        "docs": "https://docs.anthropic.com",
        "github": "https://github.com/anthropics/anthropic-sdk-python",
        "family": "Anthropic",
        "scores": (10, 8, 8, 5, 8, 8, 9, 8),
        "use_cases": ["Complex analysis", "Long-document review", "Multi-step agents", "High-stakes drafting"],
        "alternatives": ["gpt4_1", "gemini_1_5_pro", "claude_sonnet"],
        "strengths": ["Strong reasoning", "200K context", "Steerability and safety"],
        "weaknesses": ["Highest API cost in Claude lineup", "No fine-tuning", "Cloud-only"],
    },
    {
        "slug": "claude_sonnet",
        "name": "Claude Sonnet",
        "tagline": "Balanced Claude tier for production workloads — capability without Opus cost",
        "pricing_model": "paid",
        "license": "Proprietary",
        "website": "https://www.anthropic.com/claude",
        "docs": "https://docs.anthropic.com",
        "github": "https://github.com/anthropics/anthropic-sdk-python",
        "family": "Anthropic",
        "scores": (9, 8, 9, 7, 8, 8, 8, 8),
        "use_cases": ["Production chat", "RAG answering", "Code review", "Data extraction"],
        "alternatives": ["gpt4_1", "gemini_flash", "claude_opus"],
        "strengths": ["Cost-performance balance", "Reliable instruction following", "Prompt caching"],
        "weaknesses": ["Less peak reasoning than Opus", "No on-prem weights"],
    },
    {
        "slug": "gemini_1_5_pro",
        "name": "Gemini 1.5 Pro",
        "tagline": "Google's long-context Pro model — up to 2M tokens for massive documents and video",
        "pricing_model": "freemium",
        "license": "Proprietary",
        "website": "https://deepmind.google/technologies/gemini/",
        "docs": "https://ai.google.dev/docs",
        "github": "https://github.com/google-gemini/generative-ai-python",
        "family": "Google",
        "scores": (9, 9, 8, 7, 8, 8, 9, 7),
        "use_cases": ["Very long context RAG", "Video/audio understanding", "Codebase analysis", "Multimodal QA"],
        "alternatives": ["claude_opus", "gpt4_1", "gemini_flash"],
        "strengths": ["Industry-leading context window", "Native multimodal", "Vertex enterprise path"],
        "weaknesses": ["Variable latency at huge context", "Ecosystem smaller than OpenAI"],
    },
    {
        "slug": "gemini_flash",
        "name": "Gemini Flash",
        "tagline": "Fast, cost-efficient Gemini tier for high-throughput and latency-sensitive apps",
        "pricing_model": "freemium",
        "license": "Proprietary",
        "website": "https://deepmind.google/technologies/gemini/",
        "docs": "https://ai.google.dev/docs",
        "github": "https://github.com/google-gemini/generative-ai-python",
        "family": "Google",
        "scores": (8, 9, 9, 9, 8, 8, 8, 7),
        "use_cases": ["High-volume classification", "Routing", "Chat at scale", "Lightweight agents"],
        "alternatives": ["claude_sonnet", "gpt4_1", "gemini_1_5_pro"],
        "strengths": ["Low cost per token", "Large context at Flash pricing", "Strong speed"],
        "weaknesses": ["Less depth than Pro/Opus on hard reasoning"],
    },
    # Open-source / open-weight
    {
        "slug": "llama_3",
        "name": "Meta Llama 3",
        "tagline": "Meta's open-weight Llama 3 family for self-hosted and fine-tuned generation",
        "pricing_model": "open_source",
        "license": "Llama 3 Community License",
        "website": "https://llama.meta.com",
        "docs": "https://llama.meta.com/docs",
        "github": "https://github.com/meta-llama/llama3",
        "family": "Meta",
        "scores": (8, 8, 7, 9, 9, 8, 9, 9),
        "use_cases": ["On-prem LLM", "Fine-tuning", "Private RAG", "Cost-controlled inference"],
        "alternatives": ["mistral_large", "mixtral", "qwen"],
        "strengths": ["Open weights", "Strong community", "Runs on Ollama/vLLM"],
        "weaknesses": ["Ops burden for self-host", "License constraints at scale"],
    },
    {
        "slug": "mistral_large",
        "name": "Mistral Large",
        "tagline": "Mistral's flagship proprietary-class model with European hosting options",
        "pricing_model": "paid",
        "license": "Mistral AI License",
        "website": "https://mistral.ai",
        "docs": "https://docs.mistral.ai",
        "github": "https://github.com/mistralai/client-python",
        "family": "Mistral",
        "scores": (9, 8, 7, 7, 7, 7, 8, 7),
        "use_cases": ["EU data residency", "Multilingual apps", "Enterprise chat", "RAG in EU"],
        "alternatives": ["mixtral", "claude_sonnet", "gpt4_1"],
        "strengths": ["Strong multilingual", "EU provider", "Competitive reasoning"],
        "weaknesses": ["Smaller ecosystem than US hyperscalers"],
    },
    {
        "slug": "mixtral",
        "name": "Mixtral",
        "tagline": "Mistral's sparse MoE open-weight model — strong quality per dollar when self-hosted",
        "pricing_model": "open_source",
        "license": "Apache-2.0",
        "website": "https://mistral.ai",
        "docs": "https://docs.mistral.ai",
        "github": "https://github.com/mistralai/mistral-inference",
        "family": "Mistral",
        "scores": (8, 8, 7, 8, 7, 7, 9, 8),
        "use_cases": ["Self-hosted MoE", "High throughput inference", "Fine-tuning", "EU on-prem"],
        "alternatives": ["llama_3", "mistral_large", "qwen"],
        "strengths": ["MoE efficiency", "Open weights", "Good multilingual"],
        "weaknesses": ["MoE serving complexity", "Less turnkey than APIs"],
    },
    {
        "slug": "deepseek",
        "name": "DeepSeek",
        "tagline": "DeepSeek's general models — strong reasoning with aggressive open/API pricing",
        "pricing_model": "freemium",
        "license": "DeepSeek License",
        "website": "https://www.deepseek.com",
        "docs": "https://api-docs.deepseek.com",
        "github": "https://github.com/deepseek-ai",
        "family": "DeepSeek",
        "scores": (9, 8, 7, 9, 6, 6, 7, 6),
        "use_cases": ["Cost-sensitive reasoning", "Research prototypes", "Hybrid cloud/self-host"],
        "alternatives": ["qwen", "llama_3", "claude_sonnet"],
        "strengths": ["Strong math/reasoning per dollar", "Open-weight variants"],
        "weaknesses": ["Smaller Western enterprise support", "Data residency considerations"],
    },
    {
        "slug": "qwen",
        "name": "Qwen",
        "tagline": "Alibaba Qwen open-weight family — multilingual and strong coding variants",
        "pricing_model": "open_source",
        "license": "Apache-2.0",
        "website": "https://qwenlm.github.io",
        "docs": "https://github.com/QwenLM/Qwen",
        "github": "https://github.com/QwenLM/Qwen",
        "family": "Alibaba",
        "scores": (8, 8, 7, 9, 6, 7, 8, 7),
        "use_cases": ["Multilingual RAG", "Self-hosted inference", "Asian language apps", "Fine-tuning"],
        "alternatives": ["llama_3", "deepseek", "gemma"],
        "strengths": ["Many size tiers", "Strong multilingual", "Active releases"],
        "weaknesses": ["Less Western enterprise narrative"],
    },
    {
        "slug": "gemma",
        "name": "Gemma",
        "tagline": "Google's lightweight open models for edge, on-device, and cost-efficient RAG",
        "pricing_model": "open_source",
        "license": "Gemma License",
        "website": "https://ai.google.dev/gemma",
        "docs": "https://ai.google.dev/gemma/docs",
        "github": "https://github.com/google-gemma",
        "family": "Google",
        "scores": (7, 7, 8, 9, 7, 7, 8, 8),
        "use_cases": ["Edge inference", "Small GPU deployments", "Routing/classification", "Private assistants"],
        "alternatives": ["phi", "llama_3", "gemini_flash"],
        "strengths": ["Small footprint", "Google research lineage", "Good for SLMs"],
        "weaknesses": ["Not frontier-class on hard reasoning"],
    },
    {
        "slug": "phi",
        "name": "Microsoft Phi",
        "tagline": "Microsoft's small language models — high capability per parameter for local AI",
        "pricing_model": "open_source",
        "license": "MIT",
        "website": "https://azure.microsoft.com/en-us/products/phi",
        "docs": "https://learn.microsoft.com/en-us/azure/ai-studio/how-to-phi",
        "github": "https://github.com/microsoft/phi-3",
        "family": "Microsoft",
        "scores": (7, 6, 8, 10, 6, 6, 7, 9),
        "use_cases": ["Local AI", "Laptop inference", "Low-latency assistants", "Cost-minimal RAG"],
        "alternatives": ["gemma", "llama_3", "gemini_flash"],
        "strengths": ["Tiny VRAM footprint", "Fast on CPU/GPU", "Azure integration"],
        "weaknesses": ["Limited vs frontier on complex agents"],
    },
    # Coding-focused
    {
        "slug": "deepseek_coder",
        "name": "DeepSeek Coder",
        "tagline": "Code-specialized DeepSeek models for generation, completion, and repo-scale tasks",
        "pricing_model": "freemium",
        "license": "DeepSeek License",
        "website": "https://www.deepseek.com",
        "docs": "https://api-docs.deepseek.com",
        "github": "https://github.com/deepseek-ai",
        "family": "DeepSeek",
        "scores": (9, 7, 7, 9, 5, 5, 6, 6),
        "use_cases": ["IDE assistants", "Code review bots", "Test generation", "Migration tooling"],
        "alternatives": ["codestral", "code_llama", "gpt4_1"],
        "strengths": ["Strong benchmarks on code", "Low API cost"],
        "weaknesses": ["Narrower than general models for mixed tasks"],
    },
    {
        "slug": "codestral",
        "name": "Codestral",
        "tagline": "Mistral's code-first model for fill-in-the-middle, repo context, and IDE workflows",
        "pricing_model": "paid",
        "license": "Mistral AI License",
        "website": "https://mistral.ai",
        "docs": "https://docs.mistral.ai/capabilities/code_generation/",
        "github": "https://github.com/mistralai/client-python",
        "family": "Mistral",
        "scores": (9, 7, 8, 7, 6, 6, 7, 7),
        "use_cases": ["IDE copilots", "FIM completion", "Code translation", "Infra-as-code"],
        "alternatives": ["deepseek_coder", "gpt4_1", "code_llama"],
        "strengths": ["FIM support", "EU hosting", "Strong Python/TS"],
        "weaknesses": ["General chat weaker than Large/Opus"],
    },
    {
        "slug": "code_llama",
        "name": "Code Llama",
        "tagline": "Meta's open-weight code models derived from Llama for self-hosted dev tools",
        "pricing_model": "open_source",
        "license": "Llama 3 Community License",
        "website": "https://ai.meta.com/blog/code-llama-large-language-model-coding/",
        "docs": "https://github.com/meta-llama/codellama",
        "github": "https://github.com/meta-llama/codellama",
        "family": "Meta",
        "scores": (8, 7, 6, 10, 8, 7, 8, 10),
        "use_cases": ["Air-gapped coding", "Custom fine-tunes", "On-prem copilots", "Batch refactoring"],
        "alternatives": ["deepseek_coder", "codestral", "llama_3"],
        "strengths": ["Free weights", "Multiple sizes", "Proven self-host stack"],
        "weaknesses": ["Older vs latest API code models", "Ops overhead"],
    },
    # Enterprise / long context
    {
        "slug": "command_r_plus",
        "name": "Command R+",
        "tagline": "Cohere's enterprise RAG-optimized model with strong grounding and tool use",
        "pricing_model": "enterprise",
        "license": "Proprietary",
        "website": "https://cohere.com",
        "docs": "https://docs.cohere.com/docs/command-r-plus",
        "github": "https://github.com/cohere-ai/cohere-python",
        "family": "Cohere",
        "scores": (8, 8, 8, 6, 7, 7, 8, 8),
        "use_cases": ["Enterprise RAG", "Grounded Q&A", "Tool-using agents", "Multilingual search"],
        "alternatives": ["claude_sonnet", "gemini_1_5_pro", "mistral_large"],
        "strengths": ["Built for retrieval workflows", "Enterprise contracts", "Rerank pairing"],
        "weaknesses": ["Less general brand than hyperscalers", "Premium enterprise pricing"],
    },
]

DIMENSION_KEYS = [
    "performance",
    "scalability",
    "ease_of_use",
    "cost_efficiency",
    "community",
    "maturity",
    "flexibility",
    "data_privacy",
]

JUSTIFICATIONS = {
    "performance": "Benchmark-tier capability on reasoning, coding, and instruction following for this model class.",
    "scalability": "Throughput, hosting options, and enterprise scaling paths appropriate to the family.",
    "ease_of_use": "Developer experience via APIs, docs, and framework integrations.",
    "cost_efficiency": "Typical $/token or self-host TCO relative to peers in the same tier.",
    "community": "Ecosystem size, examples, and third-party tooling.",
    "maturity": "Production history, stability, and enterprise adoption.",
    "flexibility": "Modalities, fine-tuning, tool use, and deployment modes.",
    "data_privacy": "Self-host option, residency controls, and data handling policies.",
}


def _build_spec(entry: dict) -> dict:
    slug = entry["slug"]
    scores = dict(zip(DIMENSION_KEYS, entry["scores"]))
    comparison_dimensions = {
        dim: {"score": val, "justification": JUSTIFICATIONS[dim]} for dim, val in scores.items()
    }
    alts = [{"slug": a, "note": f"Alternative foundation model in the same comparison layer"} for a in entry["alternatives"]]

    description = textwrap.dedent(
        f"""
        {entry['name']} is a foundation model family in the {entry['family']} ecosystem, catalogued
        for architecture decisions at the generation step of AI pipelines. This module covers
        model capabilities, context, modalities, deployment fit, and trade-offs — not API vendor
        integration (see cloud_api modules such as openai or google_gemini for that layer).

        Strengths: {', '.join(entry['strengths'])}.
        Tradeoffs: {', '.join(entry['weaknesses'])}.
        """
    ).strip()

    return {
        "meta": {
            "slug": slug,
            "name": entry["name"],
            "version": "1.0.0",
            "category": "llm_layer",
            "subcategory": "foundation_model",
            "status": "stable",
            "last_updated": "2026-05-22",
            "maintainer": "system",
        },
        "identity": {
            "tagline": entry["tagline"],
            "description": description,
            "logo_url": f"/assets/modules/{slug}.svg",
            "website": entry["website"],
            "documentation": entry["docs"],
            "github": entry["github"],
            "license": entry["license"],
            "pricing_model": entry["pricing_model"],
        },
        "capabilities": {
            "primary_use_cases": entry["use_cases"],
            "supported_operations": [
                "text_generation",
                "chat_completion",
                "tool_use",
                "streaming",
                "json_mode",
            ],
            "integrations": [
                {"slug": "langchain", "type": "compatible"},
                {"slug": "llamaindex", "type": "compatible"},
            ],
        },
        "technical_specs": {
            "model_family": entry["family"],
            "foundation_model_layer": True,
            "supported_modalities": ["text"],
            "deployment_modes": ["cloud_api", "self_hosted", "hybrid"],
            "decision": {
                "latency_score": scores["performance"],
                "scalability_score": scores["scalability"],
                "ease_of_use_score": scores["ease_of_use"],
                "pricing_tier": "low" if entry["pricing_model"] == "open_source" else "medium",
            },
        },
        "comparison_dimensions": comparison_dimensions,
        "knowledge": {
            "entries": [
                {
                    "topic": f"When to choose {entry['name']}",
                    "content": textwrap.dedent(
                        f"""
                        Choose {entry['name']} when your architecture needs {entry['use_cases'][0].lower()}
                        and you can accept tradeoffs: {entry['weaknesses'][0]}.
                        Pair with retrieval and evaluation modules; use cloud_api entries only
                        when the decision is specifically about API routing, billing, or VPC — not
                        model family selection.
                        """
                    ).strip(),
                    "tags": ["model-selection", "architecture", "foundation_model"],
                },
                {
                    "topic": f"{entry['name']} vs alternatives",
                    "content": textwrap.dedent(
                        f"""
                        Compare against {', '.join(entry['alternatives'])} at the foundation_model layer only.
                        Do not compare to inference hosts (groq_inference), local runners (ollama), or
                        provider APIs (openai) in the same shortlist — the advisor enforces layer separation.
                        """
                    ).strip(),
                    "tags": ["comparison", "trade-offs"],
                },
            ]
        },
        "code_examples": [
            {
                "title": f"Reference architecture slot — {entry['name']}",
                "language": "python",
                "code": textwrap.dedent(
                    f"""
                    # Foundation model slot: {slug}
                    # Generation step follows retrieval; outputs go to evaluation.
                    PIPELINE_LLM = "{slug}"
                    """
                ).strip(),
            }
        ],
        "relationships": {
            "alternatives": alts,
            "complements": [
                {"slug": "langchain", "role": "Orchestration around the model"},
                {"slug": "hybrid_search", "role": "Retrieval feeding context"},
                {"slug": "langfuse", "role": "Observability for generations"},
            ],
            "typical_pipeline_position": "llm_generation",
            "pipeline_predecessors": ["retrieval", "reranking_models", "prompt_construction"],
            "pipeline_successors": ["evaluation", "deployment", "caching"],
        },
    }


def main() -> None:
    written = []
    for entry in FOUNDATION_MODELS:
        path = SPECS_DIR / f"{entry['slug']}.yaml"
        spec = _build_spec(entry)
        path.write_text(
            yaml.dump(spec, sort_keys=False, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )
        written.append(entry["slug"])
    print(f"Wrote {len(written)} foundation_model specs:")
    for s in written:
        print(f"  - {s}")


if __name__ == "__main__":
    main()
