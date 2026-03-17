from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.redis import cache_get, cache_set
from src.db.session import get_db
from src.services.module_service import ModuleService

router = APIRouter(prefix="/modules", tags=["modules"])


def get_module_service(db: AsyncSession = Depends(get_db)) -> ModuleService:
    return ModuleService(db)


@router.get("")
async def list_modules(
    category: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="per_page"),
    page_size: int | None = Query(None, ge=1, le=100),
    service: ModuleService = Depends(get_module_service),
):
    """List all modules with optional filtering."""
    effective_per_page = page_size if page_size is not None else per_page
    cache_key = f"modules:list:{category}:{status}:{search}:{page}:{effective_per_page}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    modules, total = await service.list_modules(
        category=category, status=status, search=search, page=page, per_page=effective_per_page
    )

    result = {
        "modules": [
            {
                "slug": m.slug,
                "name": m.name,
                "category": m.category.slug if m.category else None,
                "subcategory": m.subcategory,
                "tagline": m.tagline,
                "status": m.status,
                "logo_url": m.logo_url,
                "pricing_model": m.pricing_model,
            }
            for m in modules
        ],
        "total": total,
        "page": page,
        "per_page": effective_per_page,
        "pages": (total + effective_per_page - 1) // effective_per_page if effective_per_page > 0 else 0,
    }
    await cache_set(cache_key, result, ttl=300)
    return result


@router.get("/categories")
async def list_categories(service: ModuleService = Depends(get_module_service)):
    """List all module categories with counts."""
    cache_key = "modules:categories"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    result = await service.list_categories()
    await cache_set(cache_key, result, ttl=3600)
    return result


@router.get("/{slug}")
async def get_module(
    slug: str,
    service: ModuleService = Depends(get_module_service),
):
    """Get detailed info about a single module."""
    cache_key = f"modules:detail:{slug}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    module = await service.get_by_slug(slug)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{slug}' not found")

    result = {
        "slug": module.slug,
        "name": module.name,
        "category": module.category.slug if module.category else None,
        "subcategory": module.subcategory,
        "status": module.status,
        "version": module.version,
        "tagline": module.tagline,
        "description": module.description,
        "logo_url": module.logo_url,
        "website": module.website,
        "documentation": module.documentation,
        "github_url": module.github_url,
        "license": module.license,
        "pricing_model": module.pricing_model,
        "technical_specs": module.technical_specs,
        "primary_use_cases": module.primary_use_cases,
        "supported_operations": module.supported_operations,
        "comparison_scores": module.comparison_scores,
        "code_examples": module.code_examples,
        "alternatives": module.alternatives,
        "complements": module.complements,
        "pipeline_position": module.pipeline_position,
        "knowledge_entries": [
            {
                "topic": k.topic,
                "content": k.content,
                "tags": k.tags,
            }
            for k in module.knowledge_entries
        ],
        "benchmarks": [
            {
                "name": b.name,
                "value": float(b.value),
                "unit": b.unit,
                "context": b.context,
            }
            for b in module.benchmarks
        ],
    }
    await cache_set(cache_key, result, ttl=600)
    return result


@router.get("/{slug}/knowledge")
async def get_module_knowledge(
    slug: str,
    tags: str | None = Query(None, description="Comma-separated tags to filter"),
    service: ModuleService = Depends(get_module_service),
):
    """Get knowledge entries for a module."""
    module = await service.get_by_slug(slug)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{slug}' not found")

    entries = module.knowledge_entries
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        entries = [e for e in entries if any(t in e.tags for t in tag_list)]

    return [
        {"topic": e.topic, "content": e.content, "tags": e.tags}
        for e in entries
    ]
