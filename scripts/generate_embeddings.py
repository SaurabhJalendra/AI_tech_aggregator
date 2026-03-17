"""Generate vector embeddings for all knowledge entries that don't have them yet.

Usage:
    cd backend
    python ../scripts/generate_embeddings.py

Requires OPENAI_API_KEY in .env
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.core.embeddings import generate_embeddings_batch
from src.models.module import ModuleKnowledge


BATCH_SIZE = 50


async def main():
    if not settings.openai_api_key:
        print("ERROR: OPENAI_API_KEY not set in .env")
        print("Embeddings require an OpenAI API key for text-embedding-3-small.")
        sys.exit(1)

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Count entries without embeddings
        total = (await session.execute(
            select(func.count(ModuleKnowledge.id)).where(
                ModuleKnowledge.embedding.is_(None)
            )
        )).scalar() or 0

        if total == 0:
            print("All knowledge entries already have embeddings.")
            return

        print(f"Generating embeddings for {total} knowledge entries...")

        offset = 0
        processed = 0

        while offset < total:
            # Fetch batch
            result = await session.execute(
                select(ModuleKnowledge)
                .where(ModuleKnowledge.embedding.is_(None))
                .limit(BATCH_SIZE)
            )
            entries = list(result.scalars().all())

            if not entries:
                break

            # Prepare texts
            texts = [
                f"{entry.topic}\n\n{entry.content}" for entry in entries
            ]

            # Generate embeddings
            embeddings = await generate_embeddings_batch(texts)
            if embeddings is None:
                print("ERROR: Failed to generate embeddings")
                break

            # Update entries
            for entry, embedding in zip(entries, embeddings):
                entry.embedding = embedding

            await session.commit()

            processed += len(entries)
            print(f"  Processed {processed}/{total}")
            offset += BATCH_SIZE

        print(f"Done. Generated embeddings for {processed} entries.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
