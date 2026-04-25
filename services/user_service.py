from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    AccountDisabledError,
    EmailTakenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    TokenRevokedError,
)
from core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    make_refresh_token_expiry,
    verify_password,
)
from models.refresh_token import RefreshToken
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse


async def create_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise EmailTakenError()

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
        raise InvalidCredentialsError()

    if not user.is_active:
        raise AccountDisabledError()

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


async def refresh_access_token(
    db: AsyncSession, data: RefreshRequest
) -> TokenResponse:
    hashed = hash_refresh_token(data.refresh_token)
    token_obj = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hashed)
    )

    now = datetime.now(timezone.utc)
    if not token_obj or token_obj.expires_at.replace(tzinfo=timezone.utc) < now:
        raise InvalidRefreshTokenError()

    if token_obj.revoked:
        raise TokenRevokedError()

    token_obj.revoked = True
    await db.flush()

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
    hashed = hash_refresh_token(data.refresh_token)
    token_obj = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hashed)
    )

    if not token_obj:
        raise InvalidRefreshTokenError()

    if token_obj.revoked:
        raise TokenRevokedError()

    token_obj.revoked = True
    await db.commit()
