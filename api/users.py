from fastapi import APIRouter, Depends
from core.dependencies import get_current_user
from schemas.auth import UserResponse
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user