from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.auth import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from services.user_service import create_user, login_user

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
    summary="Login and get access token",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await login_user(db, body)