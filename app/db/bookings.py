from app.db.utils import serialize_item, serialize_items
from app.db import DB
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId


# Booking Collection Name
BOOKING_COLLECTION = "bookings"

# Booking fields
CLASS_ID = "class_id"
USER_ID = "user_id"
USER_EMAIL = "user_email"
USER_NAME = "user_name"
BOOKING_TIME = "booking_time"
IS_TRAINER = "is_trainer"
NOTIFICATION_PREFERENCES = "notification_preferences"
CHANNELS = "channels"
TELEGRAM_CHAT_ID = "telegram_chat_id"
CHANNEL_EMAIL = "email"
CHANNEL_TELEGRAM = "telegram"

DEFAULT_NOTIFICATION_PREFERENCES = {
    CHANNELS: [CHANNEL_EMAIL],
    TELEGRAM_CHAT_ID: None,
}


class BookingResource:

    def __init__(self):
        self.collection = DB.get_collection(BOOKING_COLLECTION)

    def create_booking(self, class_id: str, user_id: str, user_email: str,
                       user_name: str, is_trainer: bool = False,
                       notification_preferences: dict = None):
        """Create a new booking"""
        booking = {
            CLASS_ID: class_id,
            USER_ID: user_id,
            USER_EMAIL: user_email,
            USER_NAME: user_name,
            BOOKING_TIME: datetime.now(),
            IS_TRAINER: is_trainer,
            NOTIFICATION_PREFERENCES: notification_preferences or dict(DEFAULT_NOTIFICATION_PREFERENCES),
        }
        result = self.collection.insert_one(booking)
        return result.inserted_id

    def get_booking_by_id(self, booking_id: str):
        """Get booking by ID"""
        try:
            object_id = ObjectId(booking_id)
        except (InvalidId, TypeError):
            return None

        booking = self.collection.find_one({"_id": object_id})
        return serialize_item(booking)

    def get_bookings_by_class(self, class_id: str):
        """Get all bookings for a specific class"""
        bookings = self.collection.find({CLASS_ID: class_id}).sort(BOOKING_TIME, 1)
        return serialize_items(list(bookings))

    def get_bookings_by_user(self, user_id: str):
        """Get all bookings for a specific user"""
        bookings = self.collection.find({USER_ID: user_id}).sort(BOOKING_TIME, -1)
        return serialize_items(list(bookings))

    def update_notification_preferences(self, booking_id: str, preferences: dict):
        """Update notification preferences for a booking"""
        try:
            object_id = ObjectId(booking_id)
        except (InvalidId, TypeError):
            return False

        result = self.collection.update_one(
            {"_id": object_id},
            {"$set": {NOTIFICATION_PREFERENCES: preferences}},
        )
        return result.modified_count == 1

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
