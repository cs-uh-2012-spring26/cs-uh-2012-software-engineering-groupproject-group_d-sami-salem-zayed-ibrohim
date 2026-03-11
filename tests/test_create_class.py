"""
Tests for Feature 1 (Sprint 1): Create Class.
Endpoint: POST /classes
Only trainers can create classes.
"""

import pytest
from http import HTTPStatus
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION


@pytest.fixture
def valid_class_data():
    """Valid class creation payload."""
    start_time = datetime.now() + timedelta(days=2)
    end_time = start_time + timedelta(hours=1)
    return {
        TITLE: "Yoga",
        START_DATE: start_time.strftime("%Y-%m-%d %H:%M:%S"),
        END_DATE: end_time.strftime("%Y-%m-%d %H:%M:%S"),
        CAPACITY: 20,
        LOCATION: "Studio A",
        DESCRIPTION: "A beginner-friendly yoga class"
    }


@pytest.fixture
def invalid_token():
    """Invalid JWT token."""
    return "invalid.token.here"

# Tests for POST /classes

def test_create_class_success(client, trainer_token, valid_class_data):
    """Trainer successfully creates a class with all valid fields."""
    resp = client.post(
        "/classes",
        json=valid_class_data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.get_json()
    
    # Verify response contains all expected fields
    assert "_id" in data
    assert data[TITLE] == valid_class_data[TITLE]
    assert data[CAPACITY] == valid_class_data[CAPACITY]
    assert data[LOCATION] == valid_class_data[LOCATION]
    assert data[DESCRIPTION] == valid_class_data[DESCRIPTION]
    assert "trainer_id" in data
    assert "trainer_name" in data


def test_create_class_appears_in_upcoming_list(client, trainer_token, valid_class_data):
    """Created class appears when listing upcoming classes."""
    # Create a class
    create_resp = client.post(
        "/classes",
        json=valid_class_data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert create_resp.status_code == HTTPStatus.CREATED
    created_class = create_resp.get_json()
    
    # List upcoming classes
    list_resp = client.get("/classes")
    assert list_resp.status_code == HTTPStatus.OK
    classes = list_resp.get_json()
    
    # Verify created class is in the list
    class_ids = [str(c["_id"]) for c in classes]
    assert str(created_class["_id"]) in class_ids


def test_create_multiple_non_overlapping_classes(client, trainer_token):
    """Trainer can create multiple classes without time conflicts."""
    # Create first class
    start_time_1 = datetime.now() + timedelta(days=2, hours=10)
    end_time_1 = start_time_1 + timedelta(hours=1)
    
    class_data_1 = {
        TITLE: "Morning Yoga",
        START_DATE: start_time_1.strftime("%Y-%m-%d %H:%M:%S"),
        END_DATE: end_time_1.strftime("%Y-%m-%d %H:%M:%S"),
        CAPACITY: 15,
        LOCATION: "Studio A",
        DESCRIPTION: "Morning session"
    }
    
    resp1 = client.post(
        "/classes",
        json=class_data_1,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp1.status_code == HTTPStatus.CREATED
    
    # Create second class
    start_time_2 = datetime.now() + timedelta(days=2, hours=14)
    end_time_2 = start_time_2 + timedelta(hours=1)
    
    class_data_2 = {
        TITLE: "Afternoon Pilates",
        START_DATE: start_time_2.strftime("%Y-%m-%d %H:%M:%S"),
        END_DATE: end_time_2.strftime("%Y-%m-%d %H:%M:%S"),
        CAPACITY: 12,
        LOCATION: "Studio B",
        DESCRIPTION: "Afternoon session"
    }
    
    resp2 = client.post(
        "/classes",
        json=class_data_2,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp2.status_code == HTTPStatus.CREATED


def test_create_class_no_auth_header(client, valid_class_data):
    """Request without JWT token returns 401."""
    resp = client.post("/classes", json=valid_class_data)
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_create_class_member_role_denied(client, member_token, valid_class_data):
    """Member role cannot create classes (returns 401/403)."""
    resp = client.post(
        "/classes",
        json=valid_class_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    data = resp.get_json()
    assert "trainers" in data["message"].lower()


def test_create_class_invalid_token(client, valid_class_data, invalid_token):
    """Invalid/malformed JWT token returns 401."""
    resp = client.post(
        "/classes",
        json=valid_class_data,
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_create_class_trainer_not_in_database(client, app, valid_class_data):
    """Trainer token valid but user not in DB returns 400."""
    # Create token for non-existent trainer
    with app.app_context():
        fake_token = create_access_token(
            identity="nonexistent@test.com",
            additional_claims={"role": "trainer", "user_id": "fake_trainer_id"}
        )
    
    resp = client.post(
        "/classes",
        json=valid_class_data,
        headers={"Authorization": f"Bearer {fake_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "trainer not found" in data["message"].lower()


def test_create_class_missing_title(client, trainer_token, valid_class_data):
    """Missing title field returns 400."""
    data = valid_class_data.copy()
    del data[TITLE]
    
    resp = client.post(
        "/classes",
        json=data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    response_data = resp.get_json()
    assert "required" in response_data["message"].lower()


def test_create_class_missing_capacity(client, trainer_token, valid_class_data):
    """Missing capacity field returns 400."""
    data = valid_class_data.copy()
    del data[CAPACITY]
    
    resp = client.post(
        "/classes",
        json=data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    response_data = resp.get_json()
    assert "required" in response_data["message"].lower()


def test_create_class_zero_capacity(client, trainer_token, valid_class_data):
    """Capacity = 0 returns 400."""
    data = valid_class_data.copy()
    data[CAPACITY] = 0
    
    resp = client.post(
        "/classes",
        json=data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    response_data = resp.get_json()
    assert "capacity" in response_data["message"].lower()
    assert "greater than 0" in response_data["message"].lower()


def test_create_class_negative_capacity(client, trainer_token, valid_class_data):
    """Capacity < 0 returns 400."""
    data = valid_class_data.copy()
    data[CAPACITY] = -5
    
    resp = client.post(
        "/classes",
        json=data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    response_data = resp.get_json()
    assert "capacity" in response_data["message"].lower()


def test_create_class_invalid_date_format(client, trainer_token, valid_class_data):
    """Invalid date format returns 400."""
    data = valid_class_data.copy()
    data[START_DATE] = "invalid-date-format"
    
    resp = client.post(
        "/classes",
        json=data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    response_data = resp.get_json()
    assert "date format" in response_data["message"].lower()


def test_create_class_end_before_start(client, trainer_token):
    """End date before start date returns 400."""
    start_time = datetime.now() + timedelta(days=2)
    end_time = start_time - timedelta(hours=1)  # End before start
    
    data = {
        TITLE: "Invalid Time Class",
        START_DATE: start_time.strftime("%Y-%m-%d %H:%M:%S"),
        END_DATE: end_time.strftime("%Y-%m-%d %H:%M:%S"),
        CAPACITY: 10,
        LOCATION: "Studio A",
        DESCRIPTION: "This should fail"
    }
    
    resp = client.post(
        "/classes",
        json=data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    response_data = resp.get_json()
    assert "after start date" in response_data["message"].lower()


def test_create_class_start_date_in_past(client, trainer_token):
    """Start date in the past returns 400."""
    start_time = datetime.now() - timedelta(days=1)  # Yesterday
    end_time = start_time + timedelta(hours=1)
    
    data = {
        TITLE: "Past Class",
        START_DATE: start_time.strftime("%Y-%m-%d %H:%M:%S"),
        END_DATE: end_time.strftime("%Y-%m-%d %H:%M:%S"),
        CAPACITY: 10,
        LOCATION: "Studio A",
        DESCRIPTION: "This should fail"
    }
    
    resp = client.post(
        "/classes",
        json=data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    response_data = resp.get_json()
    assert "past" in response_data["message"].lower()


def test_create_class_trainer_overlap(client, trainer_token):
    """Overlapping classes for same trainer returns 409."""
    # Create first class
    start_time_1 = datetime.now() + timedelta(days=2, hours=10)
    end_time_1 = start_time_1 + timedelta(hours=2)
    
    class_data_1 = {
        TITLE: "First Class",
        START_DATE: start_time_1.strftime("%Y-%m-%d %H:%M:%S"),
        END_DATE: end_time_1.strftime("%Y-%m-%d %H:%M:%S"),
        CAPACITY: 15,
        LOCATION: "Studio A",
        DESCRIPTION: "First session"
    }
    
    resp1 = client.post(
        "/classes",
        json=class_data_1,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp1.status_code == HTTPStatus.CREATED
    
    # Try overlapping class
    start_time_2 = start_time_1 + timedelta(minutes=30)
    end_time_2 = start_time_2 + timedelta(hours=1)
    
    class_data_2 = {
        TITLE: "Overlapping Class",
        START_DATE: start_time_2.strftime("%Y-%m-%d %H:%M:%S"),
        END_DATE: end_time_2.strftime("%Y-%m-%d %H:%M:%S"),
        CAPACITY: 10,
        LOCATION: "Studio B",
        DESCRIPTION: "This should fail"
    }
    
    resp2 = client.post(
        "/classes",
        json=class_data_2,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp2.status_code == HTTPStatus.CONFLICT
    response_data = resp2.get_json()
    assert "overlap" in response_data["message"].lower()
