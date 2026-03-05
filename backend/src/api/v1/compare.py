from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.modules.comparison_engine import ComparisonEngine
from src.schemas.compare import CompareRequest

router = APIRouter(tags=["compare"])


@router.post("/compare")
async def compare_modules(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compare 2-5 modules across dimensions."""
    engine = ComparisonEngine(db)

    try:
        result = await engine.compare(
            slugs=request.slugs,
            dimensions=request.dimensions,
            weights=request.weights,
        )
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
