from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from http import HTTPStatus
from app.db.bookings import CLASS_ID
from app.services.booking_service import BookingService

api = Namespace("bookings", description="Booking management endpoints")

# Models
create_booking_model = api.model("CreateBooking", {
    CLASS_ID: fields.String(required=True, description="Class ID to book", example="507f1f77bcf86cd799439011")
})

booking_response = api.model("BookingResponse", {
    "_id": fields.String(description="Booking ID"),
    CLASS_ID: fields.String(description="Class ID"),
    "user_id": fields.String(description="User ID"),
    "user_email": fields.String(description="User email"),
    "user_name": fields.String(description="User name"),
    "booking_time": fields.String(description="Booking timestamp"),
    "is_trainer": fields.Boolean(description="Whether the user is a trainer")
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
        claims = get_jwt()
        user_email = get_jwt_identity()
        return BookingService().create_booking(
            user_id=claims.get("user_id"),
            user_email=user_email,
            role=claims.get("role"),
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
        claims = get_jwt()
        return BookingService().get_member_bookings(
            user_id=claims.get("user_id"),
            role=claims.get("role")
        )