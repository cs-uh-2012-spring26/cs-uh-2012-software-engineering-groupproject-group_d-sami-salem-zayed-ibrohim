from app.db.utils import serialize_item, serialize_items
from app.db import DB
import bcrypt

# User Collection Name
USER_COLLECTION = "users"

# User fields
EMAIL = "email"
PASSWORD = "password"
BIRTHDAY = "birthday"
NAME = "name"
ROLE = "role"

# Roles
ROLE_MEMBER = "member"
ROLE_TRAINER = "trainer"


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
            ROLE: role
        }
        result = self.collection.insert_one(user)
        return result.inserted_id

    def get_user_by_email(self, email: str):
        """Get user by email"""
        user = self.collection.find_one({EMAIL: email})
        user.pop(PASSWORD, None)  # Remove password from returned data (security)
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

    def delete_all_users(self):
        """Delete all users (for testing)"""
        self.collection.delete_many({})
