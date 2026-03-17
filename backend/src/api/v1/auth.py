from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import get_current_user, _get_or_create_dev_user
from src.db.session import get_db
from src.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    user: dict


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Dev-only login endpoint. In production, auth goes through NextAuth directly.
    Accepts any email/password combination and creates/returns the user.
    """
    if settings.environment != "development":
        raise HTTPException(403, "Login disabled in production")
    user = await _get_or_create_dev_user(db, request.email)
    return LoginResponse(
        user={
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "image": user.image_url,
        }
    )


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "tier": user.tier,
    }
