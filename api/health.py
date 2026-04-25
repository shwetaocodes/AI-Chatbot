import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    # API
    api_status = "ok"

    # Database
    db_status = "ok"
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
    except Exception:
        db_status = "error"

    # Redis
    redis_status = "ok"
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
    except Exception:
        redis_status = "error"

    return {
        "api": api_status,
        "database": db_status,
        "redis": redis_status
    }
