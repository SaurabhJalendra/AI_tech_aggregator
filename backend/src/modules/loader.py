"""
Module Spec Loader
Reads YAML spec files from modules_registry/specs/ and loads them into PostgreSQL.
"""

import hashlib
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.module import Module, ModuleCategory, ModuleIntegration, ModuleKnowledge
from src.models.benchmark import Benchmark


SPECS_DIR = Path(__file__).parent.parent.parent.parent / "modules_registry" / "specs"


def compute_spec_hash(spec_data: dict) -> str:
    """SHA256 hash of spec content for change detection."""
    raw = yaml.dump(spec_data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_or_create_category(
    db: AsyncSession, category_slug: str
) -> ModuleCategory:
    """Get existing category or create a placeholder."""
    result = await db.execute(
        select(ModuleCategory).where(ModuleCategory.slug == category_slug)
    )
    category = result.scalar_one_or_none()

    if not category:
        category = ModuleCategory(
            slug=category_slug,
            name=category_slug.replace("_", " ").title(),
        )
        db.add(category)
        await db.flush()

    return category


async def load_spec_file(db: AsyncSession, spec_path: Path) -> Module:
    """Load a single YAML spec file into the database."""
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    meta = spec["meta"]
    identity = spec.get("identity", {})
    capabilities = spec.get("capabilities", {})
    technical_specs = spec.get("technical_specs", {})
    comparison_dims = spec.get("comparison_dimensions", {})
    knowledge = spec.get("knowledge", {})
    code_examples = spec.get("code_examples", [])
    benchmarks_data = spec.get("benchmarks", {})
    relationships = spec.get("relationships", {})

    spec_hash = compute_spec_hash(spec)

    # Get or create category
    category = await get_or_create_category(db, meta["category"])

    # Check if module already exists
    result = await db.execute(
        select(Module).where(Module.slug == meta["slug"])
    )
    module = result.scalar_one_or_none()

    if module:
        # Skip if spec hasn't changed
        if module.spec_hash == spec_hash:
            return module
        # Update existing module
        _update_module_fields(module, meta, identity, capabilities, technical_specs,
                              comparison_dims, code_examples, relationships, category, spec_hash)
    else:
        # Create new module
        module = Module(
            slug=meta["slug"],
            name=meta["name"],
            category_id=category.id,
            subcategory=meta.get("subcategory"),
            status=meta.get("status", "stable"),
            version=meta.get("version", "1.0.0"),
            tagline=identity.get("tagline"),
            description=identity.get("description", ""),
            logo_url=identity.get("logo_url"),
            website=identity.get("website"),
            documentation=identity.get("documentation"),
            github_url=identity.get("github"),
            license=identity.get("license"),
            pricing_model=identity.get("pricing_model"),
            technical_specs=technical_specs,
            primary_use_cases=capabilities.get("primary_use_cases", []),
            supported_operations=capabilities.get("supported_operations", []),
            comparison_scores=_normalize_comparison_scores(comparison_dims),
            code_examples=code_examples,
            alternatives=relationships.get("alternatives", []),
            complements=relationships.get("complements", []),
            pipeline_position=relationships.get("typical_pipeline_position"),
            pipeline_predecessors=relationships.get("pipeline_predecessors", []),
            pipeline_successors=relationships.get("pipeline_successors", []),
            spec_hash=spec_hash,
        )
        db.add(module)
        await db.flush()

    # Sync knowledge entries
    await _sync_knowledge_entries(db, module, knowledge.get("entries", []))

    # Sync integrations
    await _sync_integrations(db, module, capabilities.get("integrations", []))

    # Sync benchmarks
    await _sync_benchmarks(db, module, benchmarks_data.get("results", []),
                           benchmarks_data.get("last_run"))

    return module


def _update_module_fields(module, meta, identity, capabilities, technical_specs,
                          comparison_dims, code_examples, relationships, category, spec_hash):
    """Update an existing module's fields from spec data."""
    module.name = meta["name"]
    module.category_id = category.id
    module.subcategory = meta.get("subcategory")
    module.status = meta.get("status", "stable")
    module.version = meta.get("version", "1.0.0")
    module.tagline = identity.get("tagline")
    module.description = identity.get("description", "")
    module.logo_url = identity.get("logo_url")
    module.website = identity.get("website")
    module.documentation = identity.get("documentation")
    module.github_url = identity.get("github")
    module.license = identity.get("license")
    module.pricing_model = identity.get("pricing_model")
    module.technical_specs = technical_specs
    module.primary_use_cases = capabilities.get("primary_use_cases", [])
    module.supported_operations = capabilities.get("supported_operations", [])
    module.comparison_scores = _normalize_comparison_scores(comparison_dims)
    module.code_examples = code_examples
    module.alternatives = relationships.get("alternatives", [])
    module.complements = relationships.get("complements", [])
    module.pipeline_position = relationships.get("typical_pipeline_position")
    module.pipeline_predecessors = relationships.get("pipeline_predecessors", [])
    module.pipeline_successors = relationships.get("pipeline_successors", [])
    module.spec_hash = spec_hash


def _normalize_comparison_scores(comparison_dims: dict) -> dict:
    """Convert comparison dimensions to the DB storage format."""
    scores = {}
    for dim, data in comparison_dims.items():
        if isinstance(data, dict):
            scores[dim] = {
                "score": data.get("score", 5),
                "justification": data.get("justification", ""),
                "normalized": data.get("score", 5) / 10.0,
            }
    return scores


async def _sync_knowledge_entries(
    db: AsyncSession, module: Module, entries: list[dict]
):
    """Replace all knowledge entries for a module."""
    # Delete existing entries
    result = await db.execute(
        select(ModuleKnowledge).where(ModuleKnowledge.module_id == module.id)
    )
    for existing in result.scalars().all():
        await db.delete(existing)
    await db.flush()

    # Create new entries
    for entry in entries:
        knowledge = ModuleKnowledge(
            module_id=module.id,
            topic=entry["topic"],
            content=entry["content"],
            tags=entry.get("tags", []),
        )
        db.add(knowledge)


async def _sync_integrations(
    db: AsyncSession, module: Module, integrations: list[dict]
):
    """Replace all integration records for a module."""
    result = await db.execute(
        select(ModuleIntegration).where(ModuleIntegration.module_id == module.id)
    )
    for existing in result.scalars().all():
        await db.delete(existing)
    await db.flush()

    for integration in integrations:
        record = ModuleIntegration(
            module_id=module.id,
            target_slug=integration["slug"],
            integration_type=integration.get("type", "compatible"),
        )
        db.add(record)


async def _sync_benchmarks(
    db: AsyncSession, module: Module, results: list[dict], last_run: str | None
):
    """Replace all benchmark records for a module."""
    from datetime import datetime

    result = await db.execute(
        select(Benchmark).where(Benchmark.module_id == module.id)
    )
    for existing in result.scalars().all():
        await db.delete(existing)
    await db.flush()

    run_date = datetime.fromisoformat(last_run) if last_run else datetime.utcnow()

    for bench in results:
        record = Benchmark(
            module_id=module.id,
            name=bench["name"],
            value=bench["value"],
            unit=bench["unit"],
            context=bench.get("context"),
            run_date=run_date,
        )
        db.add(record)


async def load_all_specs(db: AsyncSession) -> list[Module]:
    """Load all spec files from the modules_registry/specs/ directory."""
    modules = []

    if not SPECS_DIR.exists():
        return modules

    for spec_file in sorted(SPECS_DIR.glob("*.yaml")):
        try:
            module = await load_spec_file(db, spec_file)
            modules.append(module)
            print(f"  Loaded: {module.slug}")
        except Exception as e:
            print(f"  ERROR loading {spec_file.name}: {e}")

    return modules
