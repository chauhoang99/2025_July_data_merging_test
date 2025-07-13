import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api import app, get_session
from models import Base
from config import DATABASE_URL

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
def test_client(test_session):
    """Create a test client with the test database session."""
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# Sample test data
@pytest.fixture
def sample_hotel_data():
    return {
        "id": "test_hotel_1",
        "destination_id": 1,
        "name": "Test Hotel",
        "description": "A test hotel description",
        "location": {
            "lat": 1.0,
            "lng": 1.0,
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country"
        },
        "amenities": {
            "general": ["wifi", "parking"],
            "room": ["tv", "safe"]
        },
        "images": {
            "rooms": [{"link": "room.jpg", "description": "Room"}],
            "site": [{"link": "site.jpg", "description": "Site"}],
            "amenities": []
        },
        "booking_conditions": ["No smoking", "No pets"]
    }


@pytest.fixture(autouse=True)
async def cleanup_tables(test_engine):
    """Clean up tables before each test."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield