from http import HTTPStatus
from app.db.bookings import (
    BookingResource,
    CHANNEL_EMAIL,
    CHANNEL_TELEGRAM,
    CHANNELS,
    CLASS_ID,
    NOTIFICATION_PREFERENCES,
    TELEGRAM_CHAT_ID,
    USER_EMAIL,
    USER_ID,
)
from app.db.classes import ClassResource, CAPACITY
from app.db.users import UserResource, ROLE_MEMBER, ROLE_TRAINER, NAME


class BookingService:

    def __init__(self):
        self.booking_resource = BookingResource()
        self.class_resource = ClassResource()
        self.user_resource = UserResource()

    def create_booking(self, user_id: str, user_email: str, role: str, data: dict):
        """Validate and create a new class booking for a member."""
        error = self._validate_booking_actor(user_id, role)
        if error:
            return error

        class_id, error = self._get_requested_class_id(data)
        if error:
            return error

        fitness_class, error = self._get_bookable_class(class_id, user_id)
        if error:
            return error

        user, error = self._get_booking_user(user_email)
        if error:
            return error

        booking_id = self._create_booking(class_id, user_id, user_email, user)
        return self._booking_created_response(booking_id, class_id, user_email)

    def _validate_booking_actor(self, user_id: str, role: str):
        if not user_id:
            return {"message": "Invalid token: user_id not found"}, HTTPStatus.UNAUTHORIZED

        if role == ROLE_TRAINER:
            return {"message": "Trainers cannot book classes"}, HTTPStatus.FORBIDDEN

        return None

    def _get_requested_class_id(self, data: dict):
        if not data:
            return None, ({"message": "Request body is required"}, HTTPStatus.BAD_REQUEST)

        class_id = data.get(CLASS_ID)
        if not class_id:
            return None, ({"message": "class_id is required"}, HTTPStatus.BAD_REQUEST)

        return class_id, None

    def _get_bookable_class(self, class_id: str, user_id: str):
        fitness_class = self.class_resource.get_class_by_id(class_id)
        if not fitness_class:
            return None, ({"message": "Class not found"}, HTTPStatus.BAD_REQUEST)

        if self.booking_resource.check_existing_booking(class_id, user_id):
            return None, ({"message": "You have already booked this class"}, HTTPStatus.CONFLICT)

        member_count = self.booking_resource.count_member_bookings(class_id)
        if member_count >= fitness_class.get(CAPACITY, 0):
            return None, ({"message": "Class is full"}, HTTPStatus.CONFLICT)

        return fitness_class, None

    def _get_booking_user(self, user_email: str):
        user = self.user_resource.get_user_by_email(user_email)
        if not user:
            return None, ({"message": "User not found"}, HTTPStatus.BAD_REQUEST)

        return user, None

    def _create_booking(self, class_id: str, user_id: str, user_email: str, user: dict):
        return self.booking_resource.create_booking(
            class_id=class_id,
            user_id=user_id,
            user_email=user_email,
            user_name=user.get(NAME),
            is_trainer=False
        )

    def _booking_created_response(self, booking_id, class_id: str, user_email: str):
        return {
            "message": "Booking created successfully",
            "booking_id": str(booking_id),
            CLASS_ID: class_id,
            USER_EMAIL: user_email,
            NOTIFICATION_PREFERENCES: {
                CHANNELS: [CHANNEL_EMAIL],
                TELEGRAM_CHAT_ID: None,
            },
        }, HTTPStatus.CREATED

    def update_notification_preferences(self, booking_id: str, user_id: str, role: str, data: dict):
        """Update notification preferences for a member's booking."""
        if role != ROLE_MEMBER:
            return {"message": "Only members can configure booking notifications"}, HTTPStatus.FORBIDDEN

        if not user_id:
            return {"message": "Invalid authentication token"}, HTTPStatus.UNAUTHORIZED

        booking = self.booking_resource.get_booking_by_id(booking_id)
        if not booking:
            return {"message": "Booking not found"}, HTTPStatus.NOT_FOUND

        if booking.get(USER_ID) != user_id:
            return {"message": "Forbidden: Cannot update another member's booking"}, HTTPStatus.FORBIDDEN

        preferences, error = self._build_notification_preferences(data)
        if error:
            return error

        self.booking_resource.update_notification_preferences(booking_id, preferences)
        return {
            "message": "Notification preferences updated successfully",
            "booking_id": booking_id,
            NOTIFICATION_PREFERENCES: preferences,
        }, HTTPStatus.OK

    def _build_notification_preferences(self, data: dict):
        if not data:
            return None, ({"message": "Request body is required"}, HTTPStatus.BAD_REQUEST)

        channels = data.get(CHANNELS)
        if not isinstance(channels, list) or not channels:
            return None, ({"message": "channels must be a non-empty list"}, HTTPStatus.BAD_REQUEST)

        normalized_channels = []
        allowed_channels = {CHANNEL_EMAIL, CHANNEL_TELEGRAM}
        for channel in channels:
            if channel not in allowed_channels:
                return None, ({"message": f"Unsupported notification channel: {channel}"}, HTTPStatus.BAD_REQUEST)
            if channel not in normalized_channels:
                normalized_channels.append(channel)

        telegram_chat_id = data.get(TELEGRAM_CHAT_ID)
        if CHANNEL_TELEGRAM in normalized_channels and not telegram_chat_id:
            return None, ({"message": "telegram_chat_id is required when telegram is selected"}, HTTPStatus.BAD_REQUEST)

        return {
            CHANNELS: normalized_channels,
            TELEGRAM_CHAT_ID: telegram_chat_id,
        }, None

    def get_member_bookings(self, user_id: str, role: str):
        """Retrieve all booked classes for a member."""
        if role != ROLE_MEMBER:
            return {
                "error": "FORBIDDEN",
                "message": "Only members can view their bookings"
            }, HTTPStatus.FORBIDDEN

        if not user_id:
            return {
                "error": "UNAUTHORIZED",
                "message": "Invalid authentication token"
            }, HTTPStatus.UNAUTHORIZED

        bookings = self.booking_resource.get_bookings_by_user(user_id)
        if not bookings:
            return {
                "error": "NOT_FOUND",
                "message": "No booked classes found for this member"
            }, HTTPStatus.NOT_FOUND

        result = []
        for booking in bookings:
            class_id = booking.get(CLASS_ID)
            fitness_class = self.class_resource.get_class_by_id(class_id)
            if fitness_class:
                entry = self.class_resource.to_dict(fitness_class)
                entry[CLASS_ID] = class_id
                result.append(entry)

        return result, HTTPStatus.OK
