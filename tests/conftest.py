import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

# Set test environment
os.environ["ENVIRONMENT"] = "test"
# Use DATABASE_URL if already set (e.g., in CI), otherwise use default
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "mysql+pymysql://root:root@localhost/numbr_billing_test")
# Only set test API keys if not already set
if "ASAAS_API_KEY" not in os.environ:
    os.environ["ASAAS_API_KEY"] = "test_api_key"
if "ASAAS_WEBHOOK_TOKEN" not in os.environ:
    os.environ["ASAAS_WEBHOOK_TOKEN"] = "test_webhook_token"
if "JWT_SECRET_KEY" not in os.environ:
    os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_jwt_authentication"

from src.database import Base
from src.main import app
from src.database import get_db


# Remove custom event_loop fixture to avoid conflicts with pytest-asyncio
# pytest-asyncio will provide the event loop automatically


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create test database engine."""
    test_db_url = os.environ["DATABASE_URL"].replace("mysql+pymysql://", "mysql+aiomysql://")
    engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_pre_ping=True
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    async def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()