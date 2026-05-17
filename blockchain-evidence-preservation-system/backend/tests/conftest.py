"""
Test Configuration - Fixtures and test database setup for pytest.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from core.infrastructure.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Create and tear down all tables for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with test DB injected."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    return {
        "email": "officer@beps.test",
        "full_name": "Test Officer",
        "password": "SecurePassword123!",
        "badge_number": "B-001",
        "department": "Digital Forensics",
        "role_name": "officer",
    }


@pytest.fixture
def sample_case_data():
    return {
        "title": "Digital Fraud Investigation 2024",
        "description": "Investigation of suspected financial fraud.",
        "priority": "high",
        "jurisdiction": "Federal",
    }
