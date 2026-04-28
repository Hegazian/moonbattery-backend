"""pytest fixtures for async integration tests."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_session
from app.main import app
from app.models import SQLModel

# In-memory SQLite for fast isolated tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db() -> AsyncGenerator[None, None]:
    """Create all tables before the test session, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh database session for each test."""
    async with TestSessionLocal() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Return an HTTP client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
