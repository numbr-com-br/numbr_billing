import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
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
from src.main import create_app
from src.database import get_db


@pytest.fixture(scope="function")
def engine():
    """Create test database engine."""
    test_db_url = os.environ["DATABASE_URL"]
    engine = create_engine(
        test_db_url,
        echo=False,
        pool_pre_ping=True
    )
    # Create tables for this test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def app():
    """Create test Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture(scope="function")
def client(app, db: Session):
    """Create test client with database override."""
    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.config['get_db'] = override_get_db
    
    with app.test_client() as client:
        yield client