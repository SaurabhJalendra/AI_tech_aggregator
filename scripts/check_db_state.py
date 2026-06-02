"""Quick DB checks (decision metadata + embedding column dims). Run from backend venv."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        rev = await conn.execute(text("SELECT version_num FROM alembic_version"))
        print("alembic_version:", rev.scalar_one_or_none())

        dim_row = await conn.execute(
            text(
                """
                SELECT atttypmod
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                WHERE c.relname = 'module_knowledge' AND a.attname = 'embedding'
                """
            )
        )
        # pgvector stores dimensions in typmod for vector type
        typmod = dim_row.scalar_one_or_none()
        print("module_knowledge.embedding typmod (1024 expected for BGE):", typmod)

        count = await conn.execute(
            text("SELECT COUNT(*) FROM module_knowledge WHERE embedding IS NOT NULL")
        )
        print("knowledge rows with embeddings:", count.scalar_one())

        coverage = await conn.execute(
            text(
                """
                SELECT
                  COUNT(*) AS total,
                  COUNT(*) FILTER (
                    WHERE (technical_specs::jsonb) ? 'decision'
                      AND (technical_specs::jsonb->'decision') IS NOT NULL
                  ) AS with_decision
                FROM modules
                """
            )
        )
        row = coverage.one()
        print(f"decision metadata coverage: {row.with_decision}/{row.total} modules")

        sample = await conn.execute(
            text(
                """
                SELECT slug, technical_specs->'decision' AS decision
                FROM modules
                WHERE slug IN ('qdrant', 'pinecone', 'chromadb')
                """
            )
        )
        print("\nSample decision metadata:")
        for sample_row in sample:
            d = sample_row.decision
            ok = d is not None and d != {} and d != "null"
            print(f"  {sample_row.slug}: {'ok' if ok else 'MISSING'}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
