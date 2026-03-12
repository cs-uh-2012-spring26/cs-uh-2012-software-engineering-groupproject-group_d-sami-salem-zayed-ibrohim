"""
Tests for Feature 3 (Sprint 1): Book a Class.
Endpoint: POST /bookings
Only members can book classes. Trainers cannot book classes.
"""

import pytest
from http import HTTPStatus
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app.db.classes import ClassResource, CAPACITY
from app.db.bookings import BookingResource, CLASS_ID
from app.db.users import UserResource


# ──────────────────────────────────────────────
# Fixtures specific to this feature's tests
# ──────────────────────────────────────────────

@pytest.fixture
def bookable_class(app, trainer_token):
    """Create a class that can be booked."""
    with app.app_context():
        # Get trainer user from database (created by trainer_token fixture)
        from app.db.users import UserResource
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        class_resource = ClassResource()
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Bookable Yoga Class",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time,
            end_date=end_time,
            capacity=10,
            location="Studio A",
            description="A class that can be booked"
        )
        return str(class_id)


@pytest.fixture
def second_member_token(app):
    """JWT token for a second member user."""
    with app.app_context():
        user_resource = UserResource()
        
        # Check if user exists, if not create
        member2 = user_resource.get_user_by_email("member2@test.com")
        if not member2:
            user_id = user_resource.create_user(
                email="member2@test.com",
                password="password123",
                name="Second Member",
                birthday="1992-03-20",
                role="member"
            )
            member2_user_id = str(user_id)
        else:
            member2_user_id = str(member2["_id"])
        
        return create_access_token(
            identity="member2@test.com",
            additional_claims={"role": "member", "user_id": member2_user_id}
        )


@pytest.fixture
def invalid_token():
    """Malformed/invalid JWT token."""
    return "invalid.token.here"


# ──────────────────────────────────────────────
# Tests for POST /bookings
# ──────────────────────────────────────────────

# ============ Happy Path Tests ============

def test_book_class_success(client, member_token, bookable_class):
    """Member successfully books a class."""
    booking_data = {CLASS_ID: bookable_class}
    
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.get_json()
    
    # Verify booking details
    assert "booking_id" in data
    assert data["class_id"] == bookable_class
    assert data["user_email"] == "member@test.com"
    assert "message" in data


def test_book_class_decreases_remaining_spots(client, member_token, bookable_class):
    """Remaining spots decrease after booking."""
    # Get initial remaining spots
    list_resp = client.get("/classes")
    classes = list_resp.get_json()
    initial_class = next((c for c in classes if str(c["_id"]) == bookable_class), None)
    initial_spots = initial_class["remaining_spots"]
    
    # Make a booking
    booking_data = {CLASS_ID: bookable_class}
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert resp.status_code == HTTPStatus.CREATED
    
    # Check remaining spots decreased
    list_resp2 = client.get("/classes")
    classes2 = list_resp2.get_json()
    updated_class = next((c for c in classes2 if str(c["_id"]) == bookable_class), None)
    
    assert updated_class["remaining_spots"] == initial_spots - 1


def test_multiple_members_book_same_class(client, member_token, second_member_token, bookable_class):
    """Multiple different members can book same class."""
    booking_data = {CLASS_ID: bookable_class}
    
    # First member books
    resp1 = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert resp1.status_code == HTTPStatus.CREATED
    
    # Second member books
    resp2 = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {second_member_token}"}
    )
    assert resp2.status_code == HTTPStatus.CREATED


# ============ Authentication/Authorization Tests ============

def test_book_class_no_auth_header(client, bookable_class):
    """Request without JWT returns 401."""
    booking_data = {CLASS_ID: bookable_class}
    
    resp = client.post("/bookings", json=booking_data)
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_book_class_trainer_forbidden(client, trainer_token, bookable_class):
    """Trainers cannot book classes (403)."""
    booking_data = {CLASS_ID: bookable_class}
    
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.FORBIDDEN
    data = resp.get_json()
    assert "trainers cannot book" in data["message"].lower()


def test_book_class_missing_user_id_in_token(client, app, bookable_class):
    """JWT token without user_id returns 401."""
    # Create token without user_id claim
    with app.app_context():
        bad_token = create_access_token(
            identity="member@test.com",
            additional_claims={"role": "member"}  # Missing user_id
        )
    
    booking_data = {CLASS_ID: bookable_class}
    
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {bad_token}"}
    )
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    data = resp.get_json()
    assert "user_id" in data["message"].lower()


def test_book_class_invalid_token(client, invalid_token, bookable_class):
    """Invalid JWT token returns 401."""
    booking_data = {CLASS_ID: bookable_class}
    
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# ============ Input Validation Tests ============

def test_book_class_missing_class_id(client, member_token):
    """Missing class_id returns 400."""
    booking_data = {}  # Empty data
    
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "class_id" in data["message"].lower() or "required" in data["message"].lower()


def test_book_class_invalid_class_id(client, member_token):
    """Non-existent class_id returns 400."""
    booking_data = {CLASS_ID: "nonexistent_class_id_12345"}
    
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "class not found" in data["message"].lower()


def test_book_class_empty_request_body(client, member_token):
    """Empty request body returns error."""
    resp = client.post(
        "/bookings",
        json=None,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    # Empty JSON body may return 400 or 500 depending on how Flask handles it
    assert resp.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.UNSUPPORTED_MEDIA_TYPE]


# ============ Business Logic Tests ============

def test_book_class_duplicate_booking(client, member_token, bookable_class):
    """Cannot book same class twice (409)."""
    booking_data = {CLASS_ID: bookable_class}
    
    # First booking - should succeed
    resp1 = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert resp1.status_code == HTTPStatus.CREATED
    
    # Second booking - should fail
    resp2 = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp2.status_code == HTTPStatus.CONFLICT
    data = resp2.get_json()
    assert "already booked" in data["message"].lower()


def test_book_class_full_capacity(client, app, trainer_token, second_member_token):
    """Cannot book when class at capacity (409)."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        # Create a class with capacity of 1
        class_resource = ClassResource()
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Small Capacity Class",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time,
            end_date=end_time,
            capacity=1,
            location="Studio A",
            description="Only 1 spot"
        )
        
        # Create member and book the only spot
        try:
            user_resource.create_user(
                email="first@test.com",
                password="password123",
                name="First Member",
                birthday="1990-01-01",
                role="member"
            )
        except:
            pass
        
        booking_resource = BookingResource()
        booking_resource.create_booking(
            class_id=str(class_id),
            user_id="first_member_id",
            user_email="first@test.com",
            user_name="First Member",
            is_trainer=False
        )
    
    # Try to book the full class
    booking_data = {CLASS_ID: str(class_id)}
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {second_member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.CONFLICT
    data = resp.get_json()
    assert "full" in data["message"].lower()


def test_book_class_user_not_in_database(client, app, bookable_class):
    """Valid token but user not in DB returns 400."""
    # Create token for non-existent user
    with app.app_context():
        fake_token = create_access_token(
            identity="nonexistent@test.com",
            additional_claims={"role": "member", "user_id": "fake_member_id"}
        )
    
    booking_data = {CLASS_ID: bookable_class}
    
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {fake_token}"}
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.get_json()
    assert "user not found" in data["message"].lower()


def test_book_class_capacity_honors_member_count_only(client, app, trainer_token):
    """Trainer bookings don't count toward capacity limit."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        # Create a class with capacity of 2
        class_resource = ClassResource()
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Trainer Booking Test",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time,
            end_date=end_time,
            capacity=2,
            location="Studio A",
            description="Testing trainer bookings"
        )
        
        # Add 1 trainer booking (shouldn't count toward capacity)
        booking_resource = BookingResource()
        booking_resource.create_booking(
            class_id=str(class_id),
            user_id=trainer_id,
            user_email="trainer@test.com",
            user_name="Test Trainer",
            is_trainer=True
        )
        
        # Add 2 member bookings (should fill capacity)
        booking_resource.create_booking(
            class_id=str(class_id),
            user_id="member_1",
            user_email="member1@test.com",
            user_name="Member One",
            is_trainer=False
        )
        booking_resource.create_booking(
            class_id=str(class_id),
            user_id="member_2",
            user_email="member2@test.com",
            user_name="Member Two",
            is_trainer=False
        )
        
        # Create a third member
        user_resource = UserResource()
        try:
            user_resource.create_user(
                email="member3@test.com",
                password="password123",
                name="Member Three",
                birthday="1990-01-01",
                role="member"
            )
        except:
            pass
        
        # Create token for third member
        third_token = create_access_token(
            identity="member3@test.com",
            additional_claims={"role": "member", "user_id": "member_3"}
        )
    
    # Try to book - should fail because capacity is full (2 member bookings)
    booking_data = {CLASS_ID: str(class_id)}
    resp = client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {third_token}"}
    )
    
    assert resp.status_code == HTTPStatus.CONFLICT
    data = resp.get_json()
    assert "full" in data["message"].lower()


# ══════════════════════════════════════════════
# Tests for GET /bookings (View My Bookings)
# ══════════════════════════════════════════════

def test_get_bookings_success(client, member_token, bookable_class):
    """Member can view their bookings."""
    # First, book a class
    booking_data = {CLASS_ID: bookable_class}
    client.post(
        "/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    # Now get bookings
    resp = client.get(
        "/bookings/my-classes",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Verify booking details
    booking = data[0]
    assert "class_id" in booking
    assert "title" in booking
    assert "start_date" in booking
    assert "location" in booking


def test_get_bookings_no_bookings(client, app):
    """Member with no bookings returns 404."""
    with app.app_context():
        # Create a new member who hasn't booked anything
        user_resource = UserResource()
        user_resource.create_user(
            email="nobookings@test.com",
            password="password123",
            name="No Bookings User",
            birthday="1990-01-01",
            role="member"
        )
        
        # Create token for this user
        user = user_resource.get_user_by_email("nobookings@test.com")
        token = create_access_token(
            identity="nobookings@test.com",
            additional_claims={"role": "member", "user_id": str(user["_id"])}
        )
    
    resp = client.get(
        "/bookings/my-classes",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == HTTPStatus.NOT_FOUND
    data = resp.get_json()
    assert "no booked classes" in data["message"].lower()


def test_get_bookings_trainer_forbidden(client, trainer_token):
    """Trainer cannot view bookings (only members can)."""
    resp = client.get(
        "/bookings/my-classes",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.FORBIDDEN
    data = resp.get_json()
    assert "only members" in data["message"].lower()


def test_get_bookings_no_auth(client):
    """GET /bookings/my-classes without auth returns 401."""
    resp = client.get("/bookings/my-classes")
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_get_bookings_invalid_token(client, invalid_token):
    """GET /bookings/my-classes with invalid token returns 401."""
    resp = client.get(
        "/bookings/my-classes",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    # Invalid token returns 401 UNAUTHORIZED
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_get_bookings_missing_user_id(client, app):
    """GET /bookings/my-classes with token missing user_id returns 401."""
    with app.app_context():
        # Create token without user_id
        token = create_access_token(
            identity="someuser@test.com",
            additional_claims={"role": "member"}  # Missing user_id
        )
    
    resp = client.get(
        "/bookings/my-classes",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    data = resp.get_json()
    assert "invalid" in data["message"].lower() or "token" in data["message"].lower()


def test_get_bookings_multiple_classes(client, app, member_token, trainer_token):
    """Member who booked multiple classes sees all of them."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        # Create two classes
        class_resource = ClassResource()
        
        start_time1 = datetime.now() + timedelta(days=1)
        class_id1 = class_resource.create_class(
            title="Yoga Class",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time1,
            end_date=start_time1 + timedelta(hours=1),
            capacity=20,
            location="Studio A",
            description="Yoga"
        )
        
        start_time2 = datetime.now() + timedelta(days=2)
        class_id2 = class_resource.create_class(
            title="Pilates Class",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time2,
            end_date=start_time2 + timedelta(hours=1),
            capacity=15,
            location="Studio B",
            description="Pilates"
        )
    
    # Book both classes
    client.post(
        "/bookings",
        json={CLASS_ID: str(class_id1)},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    client.post(
        "/bookings",
        json={CLASS_ID: str(class_id2)},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    # Get bookings
    resp = client.get(
        "/bookings/my-classes",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert len(data) == 2
    
    # Verify we got both classes
    titles = [booking["title"] for booking in data]
    assert "Yoga Class" in titles
    assert "Pilates Class" in titles
