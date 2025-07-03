"""
Test configuration and fixtures for pytest.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/test_app_db"

from main import app
from database import Base, get_db
from auth.token_manager import token_manager


# Test database setup
TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_app_db"
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database schema."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with database session override."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "sub": "test-user-123",
        "email": "test@example.com", 
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg"
    }


@pytest.fixture
def auth_token(mock_user_data):
    """Create a valid auth token for testing."""
    return token_manager.create_access_token(data=mock_user_data)


@pytest.fixture 
def auth_headers(auth_token):
    """Create authorization headers for API requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def authenticated_user(db_session, mock_user_data):
    """Create a user in the database and return it."""
    from models.user import User
    from datetime import datetime
    
    user = User(
        auth0_id=mock_user_data["sub"],
        email=mock_user_data["email"],
        name=mock_user_data["name"],
        picture=mock_user_data["picture"],
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for testing purposes"
    }


@pytest.fixture
def mock_oauth_settings():
    """Mock OAuth settings for testing."""
    with patch("config.settings") as mock_settings:
        mock_settings.oauth_client_id = "test-client-id"
        mock_settings.oauth_client_secret = "test-client-secret"  # nosec B105
        mock_settings.oauth_domain = "test.auth0.com"
        mock_settings.jwt_secret_key = "test-secret-key"  # nosec B105
        mock_settings.gemini_api_key = "test-gemini-key"
        yield mock_settings