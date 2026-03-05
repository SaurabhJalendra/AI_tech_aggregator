from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db


async def get_current_user_optional(db: AsyncSession = Depends(get_db)):
    """Placeholder: returns None until auth is implemented."""
    return None
