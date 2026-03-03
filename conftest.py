"""
Shared test configuration and fixtures for all test files.
Uses mongomock (in-memory mock DB) so no real database is touched.
"""

import sys
import os
import pytest
from flask_jwt_extended import create_access_token

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture
def app():
    """Create a Flask app with mock database for testing."""
    os.environ["MONGO_URI"] = "mongodb://localhost:27017"
    os.environ["DB_NAME"] = "test_db"
    os.environ["MOCK_DB"] = "true"
    os.environ["DEBUG"] = "true"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"

    from importlib import reload
    import app.config
    reload(app.config)

    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    application.config["PROPAGATE_EXCEPTIONS"] = True
    yield application


@pytest.fixture
def client(app):
    """Create a test client to make HTTP requests."""
    return app.test_client()


@pytest.fixture
def trainer_token(app):
    """JWT token for a trainer (user_id: trainer_id_123)."""
    with app.app_context():
        return create_access_token(
            identity="trainer@test.com",
            additional_claims={"role": "trainer", "user_id": "trainer_id_123"}
        )


@pytest.fixture
def member_token(app):
    """JWT token for a regular member (not a trainer)."""
    with app.app_context():
        return create_access_token(
            identity="member@test.com",
            additional_claims={"role": "member", "user_id": "member_id_456"}
        )