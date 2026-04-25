from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from services.user_service import (
    create_user,
    login_user,
    logout_user,
    refresh_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    return await create_user(db, body)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login — returns access + refresh token",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await login_user(db, body)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange refresh token for new token pair",
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await refresh_access_token(db, body)


@router.post(
    "/logout",
    status_code=204,
    summary="Revoke refresh token",
)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await logout_user(db, body)
