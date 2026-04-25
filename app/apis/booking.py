from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required
from http import HTTPStatus
from app.db.bookings import (
    BOOKING_TIME,
    CHANNELS,
    CLASS_ID,
    IS_TRAINER,
    NOTIFICATION_PREFERENCES,
    TELEGRAM_CHAT_ID,
    USER_EMAIL,
    USER_ID,
    USER_NAME,
)
from app.db.constants import ID
from app.services.auth_context import get_authenticated_user
from app.services.booking_service import BookingService

api = Namespace("bookings", description="Booking management endpoints")

# Models
create_booking_model = api.model("CreateBooking", {
    CLASS_ID: fields.String(required=True, description="Class ID to book", example="507f1f77bcf86cd799439011")
})

notification_preferences_model = api.model("NotificationPreferences", {
    CHANNELS: fields.List(
        fields.String(enum=["email", "telegram"]),
        required=True,
        description="Notification channels selected for this booking",
        example=["email", "telegram"],
    ),
    TELEGRAM_CHAT_ID: fields.String(
        required=False,
        description="Telegram chat id required when telegram is selected",
        example="123456789",
    ),
})

booking_response = api.model("BookingResponse", {
    ID: fields.String(description="Booking ID"),
    CLASS_ID: fields.String(description="Class ID"),
    USER_ID: fields.String(description="User ID"),
    USER_EMAIL: fields.String(description="User email"),
    USER_NAME: fields.String(description="User name"),
    BOOKING_TIME: fields.String(description="Booking timestamp"),
    IS_TRAINER: fields.Boolean(description="Whether the user is a trainer"),
    NOTIFICATION_PREFERENCES: fields.Nested(notification_preferences_model),
})

notification_preferences_response = api.model("NotificationPreferencesResponse", {
    "message": fields.String(description="Result message"),
    "booking_id": fields.String(description="Booking ID"),
    NOTIFICATION_PREFERENCES: fields.Nested(notification_preferences_model),
})


@api.route("")
class Bookings(Resource):
    @api.expect(create_booking_model)
    @api.response(HTTPStatus.CREATED, "Booking created successfully", booking_response)
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid input or class not found")
    @api.response(HTTPStatus.CONFLICT, "Booking already exists or class is full")
    @api.response(HTTPStatus.FORBIDDEN, "Trainers cannot book classes")
    @api.response(HTTPStatus.UNAUTHORIZED, "Authentication required")
    @api.doc(security='Bearer')
    @jwt_required()
    def post(self):
        """Create a new booking for a class (members only)"""
        auth_user = get_authenticated_user()
        return BookingService().create_booking(
            user_id=auth_user.user_id,
            user_email=auth_user.email,
            role=auth_user.role,
            data=request.json
        )



# For Feature 2: Allows Members to access their booked classes.
@api.route("/my-classes")
class MyBookedClasses(Resource):

    @api.doc(security='Bearer')
    @api.response(HTTPStatus.OK, "Booked classes retrieved successfully")
    @api.response(HTTPStatus.UNAUTHORIZED, "Authentication required or invalid token")
    @api.response(HTTPStatus.FORBIDDEN, "Access restricted to members only")
    @api.response(HTTPStatus.NOT_FOUND, "No bookings found for this member")
    @jwt_required()
    def get(self):
        """Retrieve all classes booked by the currently logged-in member."""
        auth_user = get_authenticated_user()
        return BookingService().get_member_bookings(
            user_id=auth_user.user_id,
            role=auth_user.role
        )


@api.route("/<string:booking_id>/notifications")
class BookingNotifications(Resource):
    @api.expect(notification_preferences_model)
    @api.response(HTTPStatus.OK, "Notification preferences updated", notification_preferences_response)
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid notification preferences")
    @api.response(HTTPStatus.UNAUTHORIZED, "Authentication required or invalid token")
    @api.response(HTTPStatus.FORBIDDEN, "Only the booking owner member can update preferences")
    @api.response(HTTPStatus.NOT_FOUND, "Booking not found")
    @api.doc(security='Bearer')
    @jwt_required()
    def patch(self, booking_id):
        """Configure email and telegram reminders for a booked class"""
        auth_user = get_authenticated_user()
        return BookingService().update_notification_preferences(
            booking_id=booking_id,
            user_id=auth_user.user_id,
            role=auth_user.role,
            data=request.json,
        )
