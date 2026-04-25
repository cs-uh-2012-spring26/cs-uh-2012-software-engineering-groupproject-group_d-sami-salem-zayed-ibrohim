import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, decode_token
from app.db.bookings import BookingResource, CHANNEL_EMAIL, CHANNEL_TELEGRAM, CHANNELS, TELEGRAM_CHAT_ID
from app.db.classes import ClassResource

# Global test configuration and shared fixtures for the test suite.
# Includes authentication tokens and database record setup.

# Token for a trainer who doesn't own the class (for permission testing)
@pytest.fixture
def other_trainer_token(app):
    with app.app_context():
        return create_access_token(
            identity="other_trainer@test.com",
            additional_claims={"role": "trainer", "user_id": "other_trainer_id_789"}
        )

# Token for a different member (for authorization testing)
@pytest.fixture
def other_member_token(app):
    with app.app_context():
        return create_access_token(
            identity="other@test.com",
            additional_claims={"role": "member", "user_id": "other_member_id_2"}
        )

# Creates a real class in the DB linked to the trainer_token identity
@pytest.fixture
def sample_class(app, trainer_token):
    with app.app_context():
        from app.db.users import UserResource
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        
        class_resource = ClassResource()
        class_id = class_resource.create_class(
            title="Yoga Basics",
            trainer_id=str(trainer["_id"]),
            trainer_name="Test Trainer",
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1, hours=1),
            capacity=20,
            location="Studio A",
            description="A beginner yoga class"
        )
        return str(class_id)

# Creates a booking synced to the user_id inside member_token
@pytest.fixture
def sample_booking(app, member_token):
    with app.app_context():
        token_data = decode_token(member_token)
        real_user_id = token_data.get("user_id") or token_data.get("sub")
        
        booking_resource = BookingResource()
        booking_id = booking_resource.create_booking(
            class_id="c1",
            user_id=real_user_id,
            user_email="member@test.com",
            user_name="member_name"
        )
        return str(booking_id)

# Multi-user setup: Alice (Default) and Bob (Email + Telegram)
@pytest.fixture
def sample_bookings_with_prefs(app, sample_class):
    with app.app_context():
        booking_resource = BookingResource()
        
        alice_id = booking_resource.create_booking(
            class_id=sample_class,
            user_id="member_id_alice",
            user_email="alice@test.com",
            user_name="Alice"
        )
        
        bob_id = booking_resource.create_booking(
            class_id=sample_class,
            user_id="member_id_bob",
            user_email="bob@test.com",
            user_name="Bob"
        )
        booking_resource.update_notification_preferences(str(bob_id), {
            CHANNELS: [CHANNEL_EMAIL, CHANNEL_TELEGRAM],
            TELEGRAM_CHAT_ID: "12345"
        })
        
        return {"class_id": sample_class, "bob_booking": str(bob_id)}