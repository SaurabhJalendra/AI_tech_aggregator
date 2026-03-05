from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-advisor-backend"}


@router.get("/health/detailed")
async def health_check_detailed(db: AsyncSession = Depends(get_db)):
    checks = {"database": False, "pgvector": False}

    try:
        result = await db.execute(text("SELECT 1"))
        checks["database"] = result.scalar() == 1
    except Exception:
        pass

    try:
        await db.execute(text("SELECT 'test'::vector(3)"))
        checks["pgvector"] = True
    except Exception:
        pass

    all_healthy = all(checks.values())
    return {
        "status": "ok" if all_healthy else "degraded",
        "checks": checks,
    }
