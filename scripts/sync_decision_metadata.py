"""
Backfill technical_specs.decision for all modules (overlays + comparison_dimensions fallback).

Usage:
    cd backend
    .venv\\Scripts\\activate
    python ..\\scripts\\sync_decision_metadata.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import func, select

from src.db.session import async_session_factory
from src.models.module import Module
from src.modules.loader import SPECS_DIR, load_spec_file
from src.services.decision_metadata import apply_decision_metadata_to_module, overlay_slugs
import yaml


async def main() -> None:
    spec_by_slug: dict[str, dict] = {}
    for path in sorted(SPECS_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        slug = (raw.get("meta") or {}).get("slug")
        if slug:
            spec_by_slug[str(slug)] = raw

    updated = 0
    with_overlay = 0
    with_decision = 0

    async with async_session_factory() as session:
        result = await session.execute(select(Module))
        modules = list(result.scalars().all())

        for module in modules:
            spec = spec_by_slug.get(module.slug)
            if apply_decision_metadata_to_module(module, spec):
                updated += 1
            specs = module.technical_specs if isinstance(module.technical_specs, dict) else {}
            decision = specs.get("decision")
            if isinstance(decision, dict) and decision:
                with_decision += 1
                if module.slug in overlay_slugs():
                    with_overlay += 1

        await session.commit()

        total = len(modules)
        print(f"Modules total: {total}")
        print(f"Updated this run: {updated}")
        print(f"With technical_specs.decision: {with_decision}")
        print(f"With advisor YAML overlay: {with_overlay}")

        for slug in ("qdrant", "pinecone", "chromadb"):
            row = await session.execute(select(Module).where(Module.slug == slug))
            mod = row.scalar_one_or_none()
            if mod:
                d = (mod.technical_specs or {}).get("decision")
                print(f"  {slug}: {'ok' if d else 'MISSING'} — keys={list(d.keys())[:6] if isinstance(d, dict) else []}")


if __name__ == "__main__":
    asyncio.run(main())
