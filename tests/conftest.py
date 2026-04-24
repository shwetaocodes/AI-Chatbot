import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings
from core.database import Base, get_db
from core.security import hash_password
from main import app
from models.user import User
import models 


@pytest.fixture(scope="session")
def engine():
    _engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        poolclass=NullPool,
    )
    yield _engine


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(engine):
    async with engine.connect() as conn:
        await conn.begin()                          
        savepoint = await conn.begin_nested()       

        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        yield session

        await session.close()
        await savepoint.rollback()                  
        await conn.rollback()                       


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(db):
    _user = User(
        email="fixture@example.com",
        hashed_password=hash_password("fixturepass123"),
        is_active=True,
    )
    db.add(_user)
    await db.flush()        
    await db.refresh(_user)
    return _user


@pytest_asyncio.fixture
async def auth_client(client, user):
    response = await client.post(
        "/auth/login",
        json={
            "email": "fixture@example.com",
            "password": "fixturepass123",
        },
    )
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client