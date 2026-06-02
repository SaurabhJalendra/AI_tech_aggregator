"""Generate vector embeddings for all knowledge entries that don't have them yet.

Usage:
    cd backend
    alembic upgrade head   # if migrating from OpenAI 1536-d vectors
    pip install -r requirements.txt
    python ../scripts/generate_embeddings.py

Uses local BAAI/bge-large-en-v1.5 (1024 dimensions). First run downloads the model.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.core.embeddings import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, generate_embeddings_batch
from src.models.module import ModuleKnowledge


BATCH_SIZE = 32


async def main():
    if not settings.embeddings_enabled:
        print("ERROR: EMBEDDINGS_ENABLED=false in .env")
        sys.exit(1)

    print(f"Model: {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS} dimensions)")

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        total = (await session.execute(
            select(func.count(ModuleKnowledge.id)).where(
                ModuleKnowledge.embedding.is_(None)
            )
        )).scalar() or 0

        if total == 0:
            print("All knowledge entries already have embeddings.")
            return

        print(f"Generating embeddings for {total} knowledge entries...")

        processed = 0

        while processed < total:
            result = await session.execute(
                select(ModuleKnowledge)
                .where(ModuleKnowledge.embedding.is_(None))
                .limit(BATCH_SIZE)
            )
            entries = list(result.scalars().all())

            if not entries:
                break

            texts = [f"{entry.topic}\n\n{entry.content}" for entry in entries]

            embeddings = await generate_embeddings_batch(texts, for_query=False)
            if embeddings is None:
                print("ERROR: Failed to generate embeddings")
                break

            if len(embeddings) != len(entries):
                print(
                    f"ERROR: Expected {len(entries)} vectors, got {len(embeddings)}"
                )
                break

            for entry, embedding in zip(entries, embeddings, strict=True):
                if len(embedding) != EMBEDDING_DIMENSIONS:
                    print(
                        f"ERROR: Wrong dimension {len(embedding)} for entry {entry.id}"
                    )
                    sys.exit(1)
                entry.embedding = embedding

            await session.commit()

            processed += len(entries)
            print(f"  Processed {processed}/{total}")

        print(f"Done. Generated embeddings for {processed} entries.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
