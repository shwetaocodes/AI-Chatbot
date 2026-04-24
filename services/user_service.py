from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models.user import User
from models.refresh_token import RefreshToken
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    make_refresh_token_expiry,
)


async def create_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == data.email))
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
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, data: LoginRequest) -> TokenResponse:

    user = await db.scalar(select(User).where(User.email == data.email))


    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )


    access_token = create_access_token(user_id=str(user.id))
    raw_refresh = generate_refresh_token()


    refresh_token_obj = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=make_refresh_token_expiry(),
    )
    db.add(refresh_token_obj)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
    )


async def refresh_access_token(db: AsyncSession, data: RefreshRequest) -> TokenResponse:
    """
    Validate refresh token, revoke it, issue new access + refresh token pair.
    Rotation: old token revoked, new token issued atomically.
    """
    hashed = hash_refresh_token(data.refresh_token)

    token_obj = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hashed)
    )

    now = datetime.now(timezone.utc)
    if (
        not token_obj
        or token_obj.revoked
        or token_obj.expires_at.replace(tzinfo=timezone.utc) < now
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    token_obj.revoked = True
    await db.flush()   # write revocation before issuing new token

    access_token = create_access_token(user_id=str(token_obj.user_id))
    raw_refresh = generate_refresh_token()

    new_refresh = RefreshToken(
        user_id=token_obj.user_id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=make_refresh_token_expiry(),
    )
    db.add(new_refresh)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
    )


async def logout_user(db: AsyncSession, data: RefreshRequest) -> None:
    """Revoke the refresh token. Access token expires naturally."""
    hashed = hash_refresh_token(data.refresh_token)

    token_obj = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hashed)
    )

    if not token_obj or token_obj.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or already revoked token",
        )

    token_obj.revoked = True
    await db.commit()