from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models.user import User
from schemas.auth import RegisterRequest
from core.security import hash_password


async def create_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.scalar(
        select(User).where(User.email == data.email)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)  # loads DB-generated id, created_at, updated_at

    return user