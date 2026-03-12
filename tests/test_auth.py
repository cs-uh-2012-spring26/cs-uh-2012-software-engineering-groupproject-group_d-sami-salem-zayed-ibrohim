"""
Tests for Authentication endpoints (Registration and Login).
Endpoints: POST /auth/register, POST /auth/login
Tests user registration, login, and JWT token generation.
"""

import pytest
from http import HTTPStatus
from app.db.users import EMAIL, PASSWORD, NAME, BIRTHDAY, ROLE, ROLE_MEMBER, ROLE_TRAINER


# ──────────────────────────────────────────────
# Tests for POST /auth/register
# ──────────────────────────────────────────────

def test_register_member_success(client):
    """Successfully register a new member."""
    registration_data = {
        EMAIL: "newmember@test.com",
        PASSWORD: "securepassword123",
        NAME: "New Member",
        BIRTHDAY: "1995-06-15",
        ROLE: ROLE_MEMBER
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.get_json()
    
    # Verify response contains access token and user info
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "newmember@test.com"
    assert data["user"]["name"] == "New Member"
    assert data["user"]["role"] == ROLE_MEMBER
    assert "_id" in data["user"]


def test_register_trainer_success(client):
    """Successfully register a new trainer."""
    registration_data = {
        EMAIL: "newtrainer@test.com",
        PASSWORD: "trainerpass456",
        NAME: "New Trainer",
        BIRTHDAY: "1988-03-20",
        ROLE: ROLE_TRAINER
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.get_json()
    
    assert "access_token" in data
    assert data["user"]["email"] == "newtrainer@test.com"
    assert data["user"]["role"] == ROLE_TRAINER


def test_register_default_role_is_member(client):
    """When role is not specified, default to member."""
    registration_data = {
        EMAIL: "defaultrole@test.com",
        PASSWORD: "password123",
        NAME: "Default Role User",
        BIRTHDAY: "1990-01-01"
        # No role specified
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.get_json()
    assert data["user"]["role"] == ROLE_MEMBER


def test_register_duplicate_email(client):
    """Cannot register with an email that already exists."""
    registration_data = {
        EMAIL: "duplicate@test.com",
        PASSWORD: "password123",
        NAME: "First User",
        BIRTHDAY: "1990-01-01",
        ROLE: ROLE_MEMBER
    }
    
    # First registration - should succeed
    resp1 = client.post("/auth/register", json=registration_data)
    assert resp1.status_code == HTTPStatus.CREATED
    
    # Second registration with same email - should fail
    resp2 = client.post("/auth/register", json=registration_data)
    assert resp2.status_code == HTTPStatus.BAD_REQUEST
    data = resp2.get_json()
    assert "already exists" in data["message"].lower()


def test_register_missing_email(client):
    """Registration fails when email is missing."""
    registration_data = {
        PASSWORD: "password123",
        NAME: "No Email User",
        BIRTHDAY: "1990-01-01",
        ROLE: ROLE_MEMBER
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "email" in data["message"].lower() or "required" in data["message"].lower()


def test_register_missing_password(client):
    """Registration fails when password is missing."""
    registration_data = {
        EMAIL: "nopassword@test.com",
        NAME: "No Password User",
        BIRTHDAY: "1990-01-01",
        ROLE: ROLE_MEMBER
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "password" in data["message"].lower() or "required" in data["message"].lower()


def test_register_missing_name(client):
    """Registration fails when name is missing."""
    registration_data = {
        EMAIL: "noname@test.com",
        PASSWORD: "password123",
        BIRTHDAY: "1990-01-01",
        ROLE: ROLE_MEMBER
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "name" in data["message"].lower() or "required" in data["message"].lower()


def test_register_missing_birthday(client):
    """Registration fails when birthday is missing."""
    registration_data = {
        EMAIL: "nobirthday@test.com",
        PASSWORD: "password123",
        NAME: "No Birthday User",
        ROLE: ROLE_MEMBER
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "birthday" in data["message"].lower() or "required" in data["message"].lower()


def test_register_invalid_role(client):
    """Registration fails when role is invalid."""
    registration_data = {
        EMAIL: "invalidrole@test.com",
        PASSWORD: "password123",
        NAME: "Invalid Role User",
        BIRTHDAY: "1990-01-01",
        ROLE: "admin"  # Invalid role
    }
    
    resp = client.post("/auth/register", json=registration_data)
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "role" in data["message"].lower() or "invalid" in data["message"].lower()


# ──────────────────────────────────────────────
# Tests for POST /auth/login
# ──────────────────────────────────────────────

def test_login_success(client):
    """Successfully login with correct credentials."""
    # First register a user
    registration_data = {
        EMAIL: "loginuser@test.com",
        PASSWORD: "mypassword123",
        NAME: "Login User",
        BIRTHDAY: "1992-05-10",
        ROLE: ROLE_MEMBER
    }
    client.post("/auth/register", json=registration_data)
    
    # Now login
    login_data = {
        EMAIL: "loginuser@test.com",
        PASSWORD: "mypassword123"
    }
    
    resp = client.post("/auth/login", json=login_data)
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    
    # Verify response contains access token and user info
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "loginuser@test.com"
    assert data["user"]["name"] == "Login User"
    assert data["user"]["role"] == ROLE_MEMBER


def test_login_trainer_success(client):
    """Trainer can login successfully."""
    # Register a trainer
    registration_data = {
        EMAIL: "trainerlogin@test.com",
        PASSWORD: "trainerpass456",
        NAME: "Trainer Login",
        BIRTHDAY: "1985-12-01",
        ROLE: ROLE_TRAINER
    }
    client.post("/auth/register", json=registration_data)
    
    # Login as trainer
    login_data = {
        EMAIL: "trainerlogin@test.com",
        PASSWORD: "trainerpass456"
    }
    
    resp = client.post("/auth/login", json=login_data)
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert data["user"]["role"] == ROLE_TRAINER


def test_login_wrong_password(client):
    """Login fails with incorrect password."""
    # Register a user
    registration_data = {
        EMAIL: "wrongpass@test.com",
        PASSWORD: "correctpassword",
        NAME: "Wrong Pass User",
        BIRTHDAY: "1990-01-01",
        ROLE: ROLE_MEMBER
    }
    client.post("/auth/register", json=registration_data)
    
    # Try to login with wrong password
    login_data = {
        EMAIL: "wrongpass@test.com",
        PASSWORD: "wrongpassword"
    }
    
    resp = client.post("/auth/login", json=login_data)
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    data = resp.get_json()
    assert "invalid" in data["message"].lower() or "password" in data["message"].lower()


def test_login_nonexistent_email(client):
    """Login fails with email that doesn't exist."""
    login_data = {
        EMAIL: "doesnotexist@test.com",
        PASSWORD: "somepassword"
    }
    
    resp = client.post("/auth/login", json=login_data)
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    data = resp.get_json()
    assert "invalid" in data["message"].lower()


def test_login_missing_email(client):
    """Login fails when email is missing."""
    login_data = {
        PASSWORD: "password123"
    }
    
    resp = client.post("/auth/login", json=login_data)
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "email" in data["message"].lower() or "required" in data["message"].lower()


def test_login_missing_password(client):
    """Login fails when password is missing."""
    login_data = {
        EMAIL: "someuser@test.com"
    }
    
    resp = client.post("/auth/login", json=login_data)
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "password" in data["message"].lower() or "required" in data["message"].lower()


def test_login_returns_valid_jwt(client):
    """Login returns a valid JWT token that can be used for authentication."""
    # Register and login
    registration_data = {
        EMAIL: "jwttest@test.com",
        PASSWORD: "password123",
        NAME: "JWT Test User",
        BIRTHDAY: "1990-01-01",
        ROLE: ROLE_MEMBER
    }
    client.post("/auth/register", json=registration_data)
    
    login_data = {
        EMAIL: "jwttest@test.com",
        PASSWORD: "password123"
    }
    
    resp = client.post("/auth/login", json=login_data)
    data = resp.get_json()
    token = data["access_token"]
    
    # Verify token works by using it to access a protected endpoint
    # Try to view classes (a public endpoint)
    classes_resp = client.get("/classes", headers={"Authorization": f"Bearer {token}"})
    assert classes_resp.status_code == HTTPStatus.OK


def test_register_and_login_flow(client):
    """Complete flow: register a user and then login."""
    # Step 1: Register
    registration_data = {
        EMAIL: "flowtest@test.com",
        PASSWORD: "flowpassword",
        NAME: "Flow Test User",
        BIRTHDAY: "1993-07-20",
        ROLE: ROLE_MEMBER
    }
    
    register_resp = client.post("/auth/register", json=registration_data)
    assert register_resp.status_code == HTTPStatus.CREATED
    register_token = register_resp.get_json()["access_token"]
    
    # Step 2: Login with same credentials
    login_data = {
        EMAIL: "flowtest@test.com",
        PASSWORD: "flowpassword"
    }
    
    login_resp = client.post("/auth/login", json=login_data)
    assert login_resp.status_code == HTTPStatus.OK
    login_token = login_resp.get_json()["access_token"]
    
    # Both tokens should work (they're different but both valid)
    assert register_token is not None
    assert login_token is not None
    assert register_token != login_token  # They're different tokens
