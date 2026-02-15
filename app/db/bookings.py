from app.db.utils import serialize_item, serialize_items
from app.db import DB
from datetime import datetime


# Booking Collection Name
BOOKING_COLLECTION = "bookings"

# Booking fields
CLASS_ID = "class_id"
USER_ID = "user_id"
USER_EMAIL = "user_email"
USER_NAME = "user_name"
BOOKING_TIME = "booking_time"
IS_TRAINER = "is_trainer"


class BookingResource:

    def __init__(self):
        self.collection = DB.get_collection(BOOKING_COLLECTION)

    def create_booking(self, class_id: str, user_id: str, user_email: str, 
                       user_name: str, is_trainer: bool = False):
        """Create a new booking"""
        booking = {
            CLASS_ID: class_id,
            USER_ID: user_id,
            USER_EMAIL: user_email,
            USER_NAME: user_name,
            BOOKING_TIME: datetime.now(),
            IS_TRAINER: is_trainer
        }
        result = self.collection.insert_one(booking)
        return result.inserted_id

    def get_bookings_by_class(self, class_id: str):
        """Get all bookings for a specific class"""
        bookings = self.collection.find({CLASS_ID: class_id}).sort(BOOKING_TIME, 1)
        return serialize_items(list(bookings))

    def get_bookings_by_user(self, user_id: str):
        """Get all bookings for a specific user"""
        bookings = self.collection.find({USER_ID: user_id}).sort(BOOKING_TIME, -1)
        return serialize_items(list(bookings))

    def check_existing_booking(self, class_id: str, user_id: str):
        """Check if user already has a booking for this class"""
        booking = self.collection.find_one({CLASS_ID: class_id, USER_ID: user_id})
        return booking is not None

    def count_member_bookings(self, class_id: str):
        """Count non-trainer bookings for a class"""
        count = self.collection.count_documents({CLASS_ID: class_id, IS_TRAINER: False})
        return count

    def delete_all_bookings(self):
        """Delete all bookings (for testing)"""
        self.collection.delete_many({})
