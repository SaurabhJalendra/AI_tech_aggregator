"""Module service — CRUD and search operations for technology modules."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.embeddings import generate_embedding
from src.models.module import Module, ModuleCategory, ModuleKnowledge


class ModuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_modules(
        self,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Module], int]:
        """List modules with filtering and pagination."""
        query = select(Module).options(selectinload(Module.category))

        if category:
            query = query.join(ModuleCategory).where(ModuleCategory.slug == category)
        if status:
            query = query.where(Module.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                Module.name.ilike(search_term)
                | Module.tagline.ilike(search_term)
                | Module.description.ilike(search_term)
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        modules = list(result.scalars().all())

        return modules, total

    async def get_by_slug(self, slug: str) -> Module | None:
        """Get a single module with all related data."""
        result = await self.db.execute(
            select(Module)
            .options(
                selectinload(Module.category),
                selectinload(Module.knowledge_entries),
                selectinload(Module.integrations),
                selectinload(Module.benchmarks),
            )
            .where(Module.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_categories(self) -> list[dict]:
        """List all categories with module counts."""
        result = await self.db.execute(
            select(
                ModuleCategory,
                func.count(Module.id).label("module_count"),
            )
            .outerjoin(Module)
            .group_by(ModuleCategory.id)
            .order_by(ModuleCategory.display_order)
        )

        categories = []
        for row in result.all():
            cat = row[0]
            count = row[1]
            categories.append({
                "slug": cat.slug,
                "name": cat.name,
                "description": cat.description,
                "icon": cat.icon,
                "module_count": count,
            })
        return categories

    async def list_categories_with_slugs(self) -> list[dict]:
        """Return categories with their module slugs for prompt injection."""
        result = await self.db.execute(
            select(ModuleCategory)
            .options(selectinload(ModuleCategory.modules))
            .order_by(ModuleCategory.display_order)
        )
        categories = result.scalars().all()
        return [
            {
                "slug": cat.slug,
                "name": cat.name,
                "module_slugs": [m.slug for m in cat.modules],
            }
            for cat in categories
        ]

    async def search_knowledge(
        self,
        query: str,
        module_slugs: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Search knowledge entries — uses vector search if embeddings available, falls back to ILIKE."""
        # Try vector search first
        query_embedding = await generate_embedding(query)
        if query_embedding is not None:
            return await self._vector_search_knowledge(
                query_embedding, module_slugs, tags, limit
            )

        # Fallback to text search
        return await self._text_search_knowledge(query, module_slugs, tags, limit)

    async def _vector_search_knowledge(
        self,
        query_embedding: list[float],
        module_slugs: list[str] | None,
        tags: list[str] | None,
        limit: int,
    ) -> list[dict]:
        """Vector similarity search using pgvector cosine distance."""
        # Build base query with cosine distance
        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
        stmt = (
            select(
                ModuleKnowledge,
                Module.slug,
                Module.name,
                ModuleKnowledge.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .join(Module)
            .where(ModuleKnowledge.embedding.is_not(None))
        )

        if module_slugs:
            stmt = stmt.where(Module.slug.in_(module_slugs))
        if tags:
            stmt = stmt.where(ModuleKnowledge.tags.overlap(tags))

        stmt = stmt.order_by("distance").limit(limit)

        result = await self.db.execute(stmt)
        entries = []
        for row in result.all():
            knowledge = row[0]
            entries.append({
                "module_slug": row[1],
                "module_name": row[2],
                "topic": knowledge.topic,
                "content": knowledge.content,
                "tags": knowledge.tags,
                "similarity": round(1 - row[3], 3),
            })
        return entries

    async def _text_search_knowledge(
        self,
        query: str,
        module_slugs: list[str] | None,
        tags: list[str] | None,
        limit: int,
    ) -> list[dict]:
        """Fallback text-based search using ILIKE."""
        stmt = (
            select(ModuleKnowledge, Module.slug, Module.name)
            .join(Module)
        )

        if module_slugs:
            stmt = stmt.where(Module.slug.in_(module_slugs))
        if tags:
            stmt = stmt.where(ModuleKnowledge.tags.overlap(tags))

        search_term = f"%{query}%"
        stmt = stmt.where(
            ModuleKnowledge.topic.ilike(search_term)
            | ModuleKnowledge.content.ilike(search_term)
        )
        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        entries = []
        for row in result.all():
            knowledge = row[0]
            entries.append({
                "module_slug": row[1],
                "module_name": row[2],
                "topic": knowledge.topic,
                "content": knowledge.content,
                "tags": knowledge.tags,
            })
        return entries
