"""
Tests for Feature 4 (Sprint 1): View member/guest list of a class.
Endpoint: GET /classes/<class_id>/members
Only the trainer who owns the class can view its member list.
"""

import pytest
from http import HTTPStatus
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app.db.bookings import BookingResource, USER_EMAIL, USER_NAME, BOOKING_TIME
from app.db.classes import ClassResource


# ──────────────────────────────────────────────
# Fixtures specific to this feature's tests
# ──────────────────────────────────────────────

@pytest.fixture
def token_no_user_id(app):
    """JWT token with trainer role but missing user_id claim."""
    with app.app_context():
        return create_access_token(
            identity="trainer@test.com",
            additional_claims={"role": "trainer"}
        )


@pytest.fixture
def other_trainer_token(app):
    """JWT token for a different trainer who does NOT own the sample class."""
    with app.app_context():
        return create_access_token(
            identity="other_trainer@test.com",
            additional_claims={"role": "trainer", "user_id": "other_trainer_id_789"}
        )


@pytest.fixture
def sample_class(app):
    """Create a fitness class owned by trainer_id_123 and return its ID."""
    with app.app_context():
        class_resource = ClassResource()
        class_id = class_resource.create_class(
            title="Yoga Basics",
            trainer_id="trainer_id_123",
            trainer_name="Test Trainer",
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1, hours=1),
            capacity=20,
            location="Studio A",
            description="A beginner yoga class"
        )
        return str(class_id)


@pytest.fixture
def sample_bookings(app, sample_class):
    """
    Create 3 bookings for the sample class:
    - Alice (member)
    - Bob (member)
    - Test Trainer (trainer booking, should be filtered out in responses)
    Returns the class ID.
    """
    with app.app_context():
        booking_resource = BookingResource()
        booking_resource.create_booking(
            class_id=sample_class,
            user_id="member_id_1",
            user_email="alice@test.com",
            user_name="Alice",
            is_trainer=False
        )
        booking_resource.create_booking(
            class_id=sample_class,
            user_id="member_id_2",
            user_email="bob@test.com",
            user_name="Bob",
            is_trainer=False
        )
        booking_resource.create_booking(
            class_id=sample_class,
            user_id="trainer_id_123",
            user_email="trainer@test.com",
            user_name="Test Trainer",
            is_trainer=True
        )
        return sample_class


# ──────────────────────────────────────────────
# Tests for GET /classes/<class_id>/members
# ──────────────────────────────────────────────

def test_member_cannot_view_class_members(client, member_token, sample_class):
    """A user with 'member' role should be denied access."""
    resp = client.get(
        f"/classes/{sample_class}/members",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.json == {"message": "Only trainers can view class members"}


def test_trainer_missing_user_id_in_token(client, token_no_user_id, sample_class):
    """A trainer token that is missing the user_id claim should be rejected."""
    resp = client.get(
        f"/classes/{sample_class}/members",
        headers={"Authorization": f"Bearer {token_no_user_id}"}
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.json == {"message": "Invalid token: user_id not found"}


def test_class_not_found(client, trainer_token):
    """Requesting members for a non-existent class should return 404."""
    resp = client.get(
        "/classes/000000000000000000000000/members",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.json == {"message": "Class not found"}


def test_trainer_not_owner_of_class(client, other_trainer_token, sample_class):
    """A trainer who does not own this class should be denied access."""
    resp = client.get(
        f"/classes/{sample_class}/members",
        headers={"Authorization": f"Bearer {other_trainer_token}"}
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.json == {"message": "You are not authorized to view members of this class"}


def test_view_members_success(client, trainer_token, sample_bookings):
    """The owning trainer should see the 2 member bookings with correct data."""
    resp = client.get(
        f"/classes/{sample_bookings}/members",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp.status_code == HTTPStatus.OK
    members = resp.json
    assert len(members) == 2

    # First member: Alice
    alice = members[0]
    assert alice[USER_NAME] == "Alice"
    assert alice[USER_EMAIL] == "alice@test.com"
    assert BOOKING_TIME in alice

    # Second member: Bob
    bob = members[1]
    assert bob[USER_NAME] == "Bob"
    assert bob[USER_EMAIL] == "bob@test.com"
    assert BOOKING_TIME in bob


def test_view_members_filters_trainer_bookings(client, trainer_token, sample_bookings):
    """Trainer bookings (is_trainer=True) should not appear in the member list."""
    resp = client.get(
        f"/classes/{sample_bookings}/members",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    members = resp.json
    assert members[0][USER_EMAIL] != "trainer@test.com"
    assert members[1][USER_EMAIL] != "trainer@test.com"
    assert members[0][USER_NAME] != "Test Trainer"
    assert members[1][USER_NAME] != "Test Trainer"


def test_view_members_empty_class(client, trainer_token, sample_class):
    """A class with no bookings should return an empty list."""
    resp = client.get(
        f"/classes/{sample_class}/members",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json == []


def test_no_auth_header(client, sample_class):
    """A request with no Authorization header should be rejected."""
    resp = client.get(f"/classes/{sample_class}/members")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED