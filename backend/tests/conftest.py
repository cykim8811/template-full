import os

import fakeredis
import pytest
from app.core.database import Base
from app.deps import get_db, get_redis
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://coders:coders@localhost:5432/coders_test",
)


@pytest.fixture(scope="session", autouse=True)
async def setup_schema():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(setup_schema):
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        yield session
        await session.close()
        await conn.rollback()
    await engine.dispose()


@pytest.fixture
async def fake_redis():
    r = fakeredis.FakeAsyncRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
async def client(db_session: AsyncSession, fake_redis):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
