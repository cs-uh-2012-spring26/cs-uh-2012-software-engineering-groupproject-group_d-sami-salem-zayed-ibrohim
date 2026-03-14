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

    from app.db import DB
    db = DB._get()
    for collection_name in db.list_collection_names():
        db.drop_collection(collection_name)


@pytest.fixture
def client(app):
    """Create a test client to make HTTP requests."""
    return app.test_client()


@pytest.fixture
def trainer_token(app):
    """JWT token for a trainer. Also creates the user in DB and uses actual user_id."""
    with app.app_context():
        from app.db.users import UserResource
        user_resource = UserResource()
        
        # Try to get existing user or create new one
        trainer = user_resource.get_user_by_email("trainer@test.com")
        if not trainer:
            user_id = user_resource.create_user(
                email="trainer@test.com",
                password="password123",
                name="Test Trainer",
                birthday="1990-01-01",
                role="trainer"
            )
            trainer_user_id = str(user_id)
        else:
            trainer_user_id = str(trainer["_id"])
        
        return create_access_token(
            identity="trainer@test.com",
            additional_claims={"role": "trainer", "user_id": trainer_user_id}
        )


@pytest.fixture
def member_token(app):
    """JWT token for a regular member. Also creates the user in DB and uses actual user_id."""
    with app.app_context():
        from app.db.users import UserResource
        user_resource = UserResource()
        
        # Try to get existing user or create new one
        member = user_resource.get_user_by_email("member@test.com")
        if not member:
            user_id = user_resource.create_user(
                email="member@test.com",
                password="password123",
                name="Test Member",
                birthday="1995-05-15",
                role="member"
            )
            member_user_id = str(user_id)
        else:
            member_user_id = str(member["_id"])
        
        return create_access_token(
            identity="member@test.com",
            additional_claims={"role": "member", "user_id": member_user_id}
        )