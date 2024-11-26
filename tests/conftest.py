import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
import aiohttp
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models import Thing, Story, Relationship
from app.dev.tools import DevTools

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://thingdata:thingdata@db/thingdata_test"
)

# Create async engine for tests
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create test database engine."""
    try:
        # Create database
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        yield engine
    finally:
        await engine.dispose()

@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest.fixture
def client(db_session: AsyncSession) -> Generator:
    """Create FastAPI test client."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def test_data(db_session: AsyncSession):
    """Generate test data for tests."""
    dev_tools = DevTools()
    data = await dev_tools.generate_test_data(
        num_things=5,
        num_stories_per_thing=2,
        num_relationships=3
    )
    
    # Add to database
    for thing in data["things"]:
        db_session.add(thing)
    for story in data["stories"]:
        db_session.add(story)
    for relationship in data["relationships"]:
        db_session.add(relationship)
        
    await db_session.commit()
    
    return data

@pytest.fixture
async def mock_federation(db_session: AsyncSession):
    """Create mock federation network for tests."""
    dev_tools = DevTools()
    return await dev_tools.mock_