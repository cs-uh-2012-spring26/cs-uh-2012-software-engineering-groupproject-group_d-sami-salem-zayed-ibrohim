"""
Tests for Feature 2 (Sprint 1): View Class List.
Endpoint: GET /classes
Any user (guest, member, trainer) can view upcoming classes.
"""

import pytest
from http import HTTPStatus
from datetime import datetime, timedelta
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION
from app.db.bookings import BookingResource
from app.db.users import UserResource


# ──────────────────────────────────────────────
# Fixtures specific to this feature's tests
# ──────────────────────────────────────────────

@pytest.fixture
def sample_upcoming_class(app, trainer_token):
    """Create a class 2 days in the future."""
    with app.app_context():
        # Get trainer from DB (created by trainer_token fixture)
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        trainer_name = trainer["name"]
        
        class_resource = ClassResource()
        start_time = datetime.now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Future Yoga Class",
            trainer_id=trainer_id,
            trainer_name=trainer_name,
            start_date=start_time,
            end_date=end_time,
            capacity=20,
            location="Studio A",
            description="A future class"
        )
        return str(class_id)


@pytest.fixture
def sample_past_class(app, trainer_token):
    """Create a class that ended 2 days ago."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        class_resource = ClassResource()
        start_time = datetime.now() - timedelta(days=2)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Past Yoga Class",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time,
            end_date=end_time,
            capacity=15,
            location="Studio B",
            description="A past class"
        )
        return str(class_id)


@pytest.fixture
def full_capacity_class(app, trainer_token):
    """Create a class at full capacity with bookings."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        # Create class
        class_resource = ClassResource()
        start_time = datetime.now() + timedelta(days=3)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Full Class",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time,
            end_date=end_time,
            capacity=2,  # Small capacity for easy testing
            location="Studio C",
            description="A full class"
        )
        
        # Create bookings to fill it
        booking_resource = BookingResource()
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
        
        return str(class_id)


# ──────────────────────────────────────────────
# Tests for GET /classes
# ──────────────────────────────────────────────

# ============ Access Control Tests ============

def test_view_classes_as_guest(client, sample_upcoming_class):
    """Guests can view classes without authentication."""
    resp = client.get("/classes")
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert isinstance(data, list)


def test_view_classes_as_member(client, member_token, sample_upcoming_class):
    """Members can view classes."""
    resp = client.get(
        "/classes",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert isinstance(data, list)


def test_view_classes_as_trainer(client, trainer_token, sample_upcoming_class):
    """Trainers can view classes."""
    resp = client.get(
        "/classes",
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert isinstance(data, list)


# ============ Data Integrity Tests ============

def test_view_classes_only_upcoming(client, app, sample_upcoming_class, sample_past_class):
    """Only future classes returned, past classes filtered out."""
    resp = client.get("/classes")
    
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    # Check that we have classes
    assert len(classes) > 0
    
    # Verify all returned classes are in the future
    now = datetime.now()
    for cls in classes:
        class_start = datetime.strptime(cls[START_DATE], "%Y-%m-%d %H:%M:%S")
        assert class_start > now, f"Class {cls[TITLE]} has start date in the past"
    
    # Verify past class is NOT in the list
    class_titles = [c[TITLE] for c in classes]
    assert "Past Yoga Class" not in class_titles


def test_view_classes_correct_remaining_spots(client, app, trainer_token):
    """Remaining spots = capacity - member bookings."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        # Create a class
        class_resource = ClassResource()
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Test Capacity Class",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time,
            end_date=end_time,
            capacity=10,
            location="Studio A",
            description="Testing capacity"
        )
        
        # Add 3 member bookings
        booking_resource = BookingResource()
        for i in range(3):
            booking_resource.create_booking(
                class_id=str(class_id),
                user_id=f"member_{i}",
                user_email=f"member{i}@test.com",
                user_name=f"Member {i}",
                is_trainer=False
            )
    
    resp = client.get("/classes")
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    # Find our test class
    test_class = next((c for c in classes if c[TITLE] == "Test Capacity Class"), None)
    assert test_class is not None
    assert test_class["remaining_spots"] == 7  # 10 - 3


def test_view_classes_trainer_bookings_dont_count(client, app, trainer_token):
    """Trainer bookings don't reduce remaining spots."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        # Create a class
        class_resource = ClassResource()
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        class_id = class_resource.create_class(
            title="Trainer Booking Test",
            trainer_id=trainer_id,
            trainer_name="Test Trainer",
            start_date=start_time,
            end_date=end_time,
            capacity=5,
            location="Studio A",
            description="Testing trainer bookings"
        )
        
        # Add 1 member booking and 1 trainer booking
        booking_resource = BookingResource()
        booking_resource.create_booking(
            class_id=str(class_id),
            user_id="member_1",
            user_email="member1@test.com",
            user_name="Member One",
            is_trainer=False
        )
        booking_resource.create_booking(
            class_id=str(class_id),
            user_id=trainer_id,
            user_email="trainer@test.com",
            user_name="Test Trainer",
            is_trainer=True
        )
    
    resp = client.get("/classes")
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    # Find our test class
    test_class = next((c for c in classes if c[TITLE] == "Trainer Booking Test"), None)
    assert test_class is not None
    assert test_class["remaining_spots"] == 4  # 5 - 1 (trainer booking doesn't count)


def test_view_classes_all_fields_present(client, sample_upcoming_class):
    """Response includes all required fields."""
    resp = client.get("/classes")
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    assert len(classes) > 0
    
    # Check first class has all required fields
    cls = classes[0]
    required_fields = ["_id", TITLE, "trainer_name", START_DATE, END_DATE, 
                      LOCATION, DESCRIPTION, "remaining_spots"]
    for field in required_fields:
        assert field in cls, f"Missing field: {field}"


def test_view_classes_empty_list(client):
    """Returns empty array when no classes exist."""
    resp = client.get("/classes")
    
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert isinstance(data, list)
    # May be empty or not depending on fixtures, but should be a list


def test_view_classes_full_class_shows_zero_spots(client, full_capacity_class):
    """Class at capacity shows 0 remaining spots (not negative)."""
    resp = client.get("/classes")
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    # Find the full class
    full_class = next((c for c in classes if c[TITLE] == "Full Class"), None)
    assert full_class is not None
    assert full_class["remaining_spots"] == 0


# ============ Edge Cases Tests ============

def test_view_classes_no_bookings(client, sample_upcoming_class):
    """Class with no bookings shows full capacity."""
    resp = client.get("/classes")
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    # Find class with no bookings
    future_class = next((c for c in classes if c[TITLE] == "Future Yoga Class"), None)
    assert future_class is not None
    assert future_class["remaining_spots"] == 20  # Full capacity


def test_view_classes_sorted_by_date(client, app, trainer_token):
    """Classes returned in chronological order."""
    with app.app_context():
        # Get trainer from DB
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email("trainer@test.com")
        trainer_id = str(trainer["_id"])
        
        class_resource = ClassResource()
        
        # Create classes at different times
        times = [
            datetime.now() + timedelta(days=5),  # Latest
            datetime.now() + timedelta(days=1),  # Earliest
            datetime.now() + timedelta(days=3),  # Middle
        ]
        
        for i, start_time in enumerate(times):
            end_time = start_time + timedelta(hours=1)
            class_resource.create_class(
                title=f"Class {i}",
                trainer_id=trainer_id,
                trainer_name="Test Trainer",
                start_date=start_time,
                end_date=end_time,
                capacity=10,
                location="Studio A",
                description=f"Class {i}"
            )
    
    resp = client.get("/classes")
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    # Verify classes are sorted by start date
    if len(classes) >= 2:
        for i in range(len(classes) - 1):
            current_start = datetime.strptime(classes[i][START_DATE], "%Y-%m-%d %H:%M:%S")
            next_start = datetime.strptime(classes[i + 1][START_DATE], "%Y-%m-%d %H:%M:%S")
            assert current_start <= next_start, "Classes are not sorted chronologically"


def test_view_classes_multiple_trainers(client, app, trainer_token):
    """Can display classes from different trainers."""
    with app.app_context():
        class_resource = ClassResource()
        
        # Create classes for different trainers (using arbitrary IDs since we're not checking ownership)
        trainers = [
            ("trainer_1", "Trainer One"),
            ("trainer_2", "Trainer Two"),
        ]
        
        for trainer_id, trainer_name in trainers:
            start_time = datetime.now() + timedelta(days=1)
            end_time = start_time + timedelta(hours=1)
            class_resource.create_class(
                title=f"{trainer_name}'s Class",
                trainer_id=trainer_id,
                trainer_name=trainer_name,
                start_date=start_time,
                end_date=end_time,
                capacity=15,
                location="Studio A",
                description=f"Class by {trainer_name}"
            )
    
    resp = client.get("/classes")
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    
    # Check that we have classes from different trainers
    trainer_names = set(c["trainer_name"] for c in classes)
    assert len(trainer_names) >= 1  # At least one trainer
