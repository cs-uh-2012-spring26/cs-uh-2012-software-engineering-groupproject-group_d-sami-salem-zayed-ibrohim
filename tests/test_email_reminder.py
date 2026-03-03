"""
Tests for Feature: Send reminder emails to class members.
Endpoint: POST /classes/<class_id>/reminder
Only the trainer who owns the class can send reminders.
Emails are sent via AWS SES (mocked in tests).
"""

import pytest
from http import HTTPStatus
from datetime import datetime, timedelta
from unittest.mock import patch
from flask_jwt_extended import create_access_token
from app.db.bookings import BookingResource
from app.db.classes import ClassResource


# ──────────────────────────────────────────────
# Fixtures specific to this feature's tests
# ──────────────────────────────────────────────

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
    Create 2 member bookings for the sample class:
    - Alice
    - Bob
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
        return sample_class


# ──────────────────────────────────────────────
# Tests for POST /classes/<class_id>/reminder
# ──────────────────────────────────────────────

@patch("app.apis.classes.SESEmailService")
def test_non_trainer_cannot_send_reminder(mock_ses, client, member_token, sample_class):
    """A user with 'member' role should get 403 Forbidden."""
    resp = client.post(
        f"/classes/{sample_class}/reminder",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert resp.status_code == 403
    assert resp.json == {"message": "Access denied. Only trainers can send class reminders."}


@patch("app.apis.classes.SESEmailService")
def test_reminder_class_not_found(mock_ses, client, trainer_token):
    """Sending a reminder for a non-existent class should return 404."""
    resp = client.post(
        "/classes/000000000000000000000000/reminder",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp.status_code == 404
    assert resp.json == {"message": "Class not found"}


@patch("app.apis.classes.SESEmailService")
def test_reminder_trainer_not_owner(mock_ses, client, other_trainer_token, sample_class):
    """A trainer who doesn't own the class should get 403 Forbidden."""
    resp = client.post(
        f"/classes/{sample_class}/reminder",
        headers={"Authorization": f"Bearer {other_trainer_token}"}
    )
    assert resp.status_code == 403
    assert resp.json == {"message": "Forbidden: Not the trainer of this class"}


@patch("app.apis.classes.SESEmailService")
def test_reminder_no_bookings(mock_ses, client, trainer_token, sample_class):
    """A class with no bookings should return 400."""
    resp = client.post(
        f"/classes/{sample_class}/reminder",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp.status_code == 400
    assert resp.json == {"message": "No registered members for this class"}


@patch("app.apis.classes.SESEmailService")
def test_reminder_sends_to_all_members(mock_ses, client, trainer_token, sample_bookings):
    """Reminders should be sent to all booked members and return 200."""
    resp = client.post(
        f"/classes/{sample_bookings}/reminder",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp.status_code == 200
    assert resp.json == {"message": "Reminders sent successfully"}

    # Verify the email service was called once per member (Alice and Bob)
    mock_instance = mock_ses.return_value
    assert mock_instance.send_email.call_count == 2

    # Check that the correct recipient emails were used
    call_args = [call[0][0] for call in mock_instance.send_email.call_args_list]
    assert "alice@test.com" in call_args
    assert "bob@test.com" in call_args


@patch("app.apis.classes.SESEmailService")
def test_reminder_email_contains_class_details(mock_ses, client, trainer_token, sample_bookings):
    """The reminder email body should include the class title and location."""
    resp = client.post(
        f"/classes/{sample_bookings}/reminder",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert resp.status_code == 200

    # Check the email body of the first call
    mock_instance = mock_ses.return_value
    first_call_body = mock_instance.send_email.call_args_list[0][0][2]
    assert "Yoga Basics" in first_call_body
    assert "Studio A" in first_call_body


def test_reminder_no_auth_header(client, sample_class):
    """A request with no Authorization header should be rejected."""
    resp = client.post(f"/classes/{sample_class}/reminder")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED