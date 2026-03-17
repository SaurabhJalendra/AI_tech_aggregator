"""
Seed Database Script
Loads all module spec YAML files into the database.

Usage:
    cd backend
    python -m scripts.seed_db

Or from project root:
    cd backend && source .venv/Scripts/activate && python ../scripts/seed_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from src.core.config import settings  # noqa: E402
from src.db.session import async_session_factory, engine  # noqa: E402
from sqlalchemy import text  # noqa: E402
from src.db.base import Base  # noqa: E402
from src.models import *  # noqa: E402, F401, F403
from src.modules.loader import load_all_specs  # noqa: E402


# Category definitions with display order and icons
CATEGORIES = [
    {"slug": "data_ingestion", "name": "Data Ingestion & Preparation", "display_order": 1, "icon": "upload"},
    {"slug": "chunking", "name": "Chunking & Segmentation", "display_order": 2, "icon": "scissors"},
    {"slug": "embeddings", "name": "Embeddings & Representation", "display_order": 3, "icon": "layers"},
    {"slug": "vector_databases", "name": "Vector Storage & Indexing", "display_order": 4, "icon": "database"},
    {"slug": "retrieval", "name": "Retrieval & Search", "display_order": 5, "icon": "search"},
    {"slug": "rag_architectures", "name": "RAG Architectures", "display_order": 6, "icon": "git-branch"},
    {"slug": "llm_layer", "name": "LLM Layer", "display_order": 7, "icon": "brain"},
    {"slug": "agent_systems", "name": "Agent Systems", "display_order": 8, "icon": "bot"},
    {"slug": "evaluation", "name": "Evaluation & Quality", "display_order": 9, "icon": "check-circle"},
    {"slug": "caching", "name": "Caching & Optimization", "display_order": 10, "icon": "zap"},
    {"slug": "fine_tuning", "name": "Fine-Tuning & Customization", "display_order": 11, "icon": "sliders"},
    {"slug": "deployment", "name": "Deployment & Operations", "display_order": 12, "icon": "cloud"},
    {"slug": "voice_conversational", "name": "Voice & Conversational", "display_order": 13, "icon": "mic"},
    {"slug": "workflow_orchestration", "name": "Workflow & Orchestration", "display_order": 14, "icon": "workflow"},
    {"slug": "security_compliance", "name": "Security & Compliance", "display_order": 15, "icon": "shield"},
    {"slug": "search_discovery", "name": "Search & Discovery", "display_order": 16, "icon": "compass"},
    {"slug": "specialized_applications", "name": "Specialized Applications", "display_order": 17, "icon": "box"},
    {"slug": "infrastructure_comparison", "name": "Infrastructure Comparison", "display_order": 18, "icon": "bar-chart"},
]


async def seed_categories(session):
    """Seed the module categories."""
    from sqlalchemy import select
    from src.models.module import ModuleCategory

    print("Seeding categories...")
    for cat_data in CATEGORIES:
        result = await session.execute(
            select(ModuleCategory).where(ModuleCategory.slug == cat_data["slug"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = cat_data["name"]
            existing.display_order = cat_data["display_order"]
            existing.icon = cat_data["icon"]
        else:
            category = ModuleCategory(**cat_data)
            session.add(category)

    await session.commit()
    print(f"  Seeded {len(CATEGORIES)} categories")


async def main():
    print("=" * 60)
    print("AI Infrastructure Advisor - Database Seed")
    print("=" * 60)
    # Mask password in database URL for safe logging
    import re
    masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', settings.database_url)
    print(f"Database: {masked_url}")
    print()

    # Create tables if they don't exist
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    print("  Tables created/verified")
    print()

    async with async_session_factory() as session:
        # Seed categories
        await seed_categories(session)
        print()

        # Load module specs
        print("Loading module specs...")
        modules = await load_all_specs(session)
        await session.commit()
        print(f"\n  Loaded {len(modules)} modules total")

    print()
    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
