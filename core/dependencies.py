import uuid
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from core.database import get_db
from core.security import decode_access_token
from core.exceptions import InvalidTokenError, AccountDisabledError
from models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)

        if payload.get("type") != "access":
            raise InvalidTokenError()

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenError()

        user_id = uuid.UUID(user_id_str)

    except (JWTError, ValueError):
        raise InvalidTokenError()

    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise InvalidTokenError()

    if not user.is_active:
        raise AccountDisabledError()

    return user