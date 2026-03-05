import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_db
from src.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the current user from the request.

    In development: accepts a simple Bearer token that is the user's email.
    In production: decrypts NextAuth JWT using fastapi-nextauth-jwt.
    """
    auth_header = request.headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header[7:]

    if settings.environment == "development":
        # Dev mode: token is just the user email for simplicity
        return await _get_or_create_dev_user(db, token)

    # Production: decrypt NextAuth JWT
    try:
        from fastapi_nextauth_jwt import NextAuthJWT

        jwt = NextAuthJWT(secret=settings.nextauth_secret)
        payload = jwt(request)
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token: no email")
        return await _get_or_create_user(db, email, payload.get("name"))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Same as get_current_user but returns None instead of raising."""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


async def _get_or_create_dev_user(db: AsyncSession, email: str) -> User:
    """In dev mode, auto-create users by email."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=email.split("@")[0],
            tier="pro",  # Dev users get pro tier
        )
        db.add(user)
        await db.flush()

    return user


async def _get_or_create_user(
    db: AsyncSession, email: str, name: str | None = None
) -> User:
    """Get or create a user from NextAuth token data."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            tier="free",
        )
        db.add(user)
        await db.flush()

    return user
