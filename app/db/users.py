import bcrypt
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from secrets import token_urlsafe

from app.db.utils import serialize_item, serialize_items
from app.db import DB

# User Collection Name
USER_COLLECTION = "users"

# User fields
EMAIL = "email"
PASSWORD = "password"
BIRTHDAY = "birthday"
NAME = "name"
ROLE = "role"
NOTIFICATION_PREFERENCES = "notification_preferences"
CHANNELS = "channels"
TELEGRAM_CHAT_ID = "telegram_chat_id"
TELEGRAM_LINK_TOKEN = "telegram_link_token"
TELEGRAM_CONNECTED_AT = "telegram_connected_at"

# Roles
ROLE_MEMBER = "member"
ROLE_TRAINER = "trainer"

# Notification channels
CHANNEL_EMAIL = "email"
CHANNEL_TELEGRAM = "telegram"

DEFAULT_NOTIFICATION_PREFERENCES = {
    CHANNELS: [CHANNEL_EMAIL],
}


class UserResource:

    def __init__(self):
        self.collection = DB.get_collection(USER_COLLECTION)
        # Ensure email is unique at database level
        self.collection.create_index(EMAIL, unique=True)

    def create_user(self, email: str, password: str, name: str, birthday: str, role: str = ROLE_MEMBER):
        """Create a new user with hashed password"""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = {
            EMAIL: email,
            PASSWORD: hashed_password,
            NAME: name,
            BIRTHDAY: birthday,
            ROLE: role,
            NOTIFICATION_PREFERENCES: dict(DEFAULT_NOTIFICATION_PREFERENCES),
            TELEGRAM_CHAT_ID: None,
            TELEGRAM_LINK_TOKEN: token_urlsafe(24),
            TELEGRAM_CONNECTED_AT: None,
        }
        result = self.collection.insert_one(user)
        return result.inserted_id

    def get_user_by_email(self, email: str):
        """Get user by email"""
        user = self.collection.find_one({EMAIL: email})
        if user and PASSWORD in user:
            user.pop(PASSWORD, None)  # Remove password from returned data (security)
        return serialize_item(user)

    def get_user_by_id(self, user_id: str):
        """Get user by ID."""
        object_id = self._to_object_id(user_id)
        if not object_id:
            return None

        user = self.collection.find_one({"_id": object_id})
        if user and PASSWORD in user:
            user.pop(PASSWORD, None)
        return serialize_item(user)

    def verify_password(self, email: str, password: str):
        """Verify user password"""
        user = self.collection.find_one({EMAIL: email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user[PASSWORD]):
            user.pop(PASSWORD, None)  # Remove password from returned data (security)
            return serialize_item(user)
        return None

    def get_all_members(self):
        """Get all members"""
        members = self.collection.find(
            {ROLE: ROLE_MEMBER},
            {"password": 0}  # Remove password from returned data (security)
        )
        return serialize_items(list(members))

    def ensure_telegram_link_token(self, user_id: str):
        """Create and return a Telegram link token for users missing one."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        existing_token = user.get(TELEGRAM_LINK_TOKEN)
        if existing_token:
            return existing_token

        object_id = self._to_object_id(user_id)
        link_token = token_urlsafe(24)
        self.collection.update_one(
            {"_id": object_id},
            {"$set": {TELEGRAM_LINK_TOKEN: link_token}},
        )
        return link_token

    def update_notification_preferences(self, user_id: str, preferences: dict):
        """Update global notification preferences for a user."""
        object_id = self._to_object_id(user_id)
        if not object_id:
            return False

        result = self.collection.update_one(
            {"_id": object_id},
            {"$set": {NOTIFICATION_PREFERENCES: preferences}},
        )
        return result.matched_count == 1

    def connect_telegram(self, link_token: str, chat_id: str):
        """Attach a Telegram chat id to the user matching a launch token."""
        if not link_token or chat_id is None:
            return None

        result = self.collection.find_one_and_update(
            {TELEGRAM_LINK_TOKEN: link_token},
            {"$set": {
                TELEGRAM_CHAT_ID: str(chat_id),
                TELEGRAM_CONNECTED_AT: datetime.now(),
            }},
            return_document=True,
            projection={PASSWORD: 0},
        )
        return serialize_item(result)

    def delete_all_users(self):
        """Delete all users (for testing)"""
        self.collection.delete_many({})

    def _to_object_id(self, value: str):
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None
