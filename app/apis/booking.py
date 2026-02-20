from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from http import HTTPStatus
from app.db.bookings import BookingResource, CLASS_ID
from app.db.classes import ClassResource, CAPACITY
from app.db.users import UserResource, ROLE_TRAINER, NAME

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
        # Extract user info from JWT
        claims = get_jwt()
        role = claims.get("role")
        user_id = claims.get("user_id")
        user_email = get_jwt_identity()

        # Validate user_id from JWT
        if not user_id:
            return {"message": "Invalid token: user_id not found"}, HTTPStatus.UNAUTHORIZED

        # Check if user is a trainer - trainers cannot book classes
        if role == ROLE_TRAINER:
            return {"message": "Trainers cannot book classes"}, HTTPStatus.FORBIDDEN
        
        # Parse request body
        data = request.json
        if not data:
            return {"message": "Request body is required"}, HTTPStatus.BAD_REQUEST
            
        class_id = data.get(CLASS_ID)

        # Validate required fields
        if not class_id:
            return {"message": "class_id is required"}, HTTPStatus.BAD_REQUEST

        # Get class by ID
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id)
        
        if not fitness_class:
            return {"message": "Class not found"}, HTTPStatus.BAD_REQUEST

        # Check if booking already exists
        booking_resource = BookingResource()
        if booking_resource.check_existing_booking(class_id, user_id):
            return {"message": "You have already booked this class"}, HTTPStatus.CONFLICT

        # Count member bookings and check if class is full
        member_count = booking_resource.count_member_bookings(class_id)
        class_capacity = fitness_class.get(CAPACITY, 0)
        
        if member_count >= class_capacity:
            return {"message": "Class is full"}, HTTPStatus.CONFLICT

        # Get user info from database
        user_resource = UserResource()
        user = user_resource.get_user_by_email(user_email)
        
        if not user:
            return {"message": "User not found"}, HTTPStatus.BAD_REQUEST
        
        user_name = user.get(NAME)

        # Create booking
        is_trainer = (role == ROLE_TRAINER)
        booking_id = booking_resource.create_booking(
            class_id=class_id,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            is_trainer=is_trainer
        )

        return {
            "message": "Booking created successfully",
            "booking_id": str(booking_id),
            "class_id": class_id,
            "user_email": user_email
        }, HTTPStatus.CREATED



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
        """
        Retrieve all classes booked by the currently logged-in member.
        """

        # Extract JWT claims
        claims = get_jwt()
        role = claims.get("role")
        user_id = claims.get("user_id")

        # Token exists but role is not member
        if role != "member":
            return {
                "error": "FORBIDDEN",
                "message": "Only members can view their bookings"
            }, HTTPStatus.FORBIDDEN  # 403

        # Token missing user_id (corrupted token case)
        if not user_id:
            return {
                "error": "UNAUTHORIZED",
                "message": "Invalid authentication token"
            }, HTTPStatus.UNAUTHORIZED  # 401

        # Create database resource instances
        booking_resource = BookingResource()
        class_resource = ClassResource()

        # Retrieve all bookings made by this user
        bookings = booking_resource.get_bookings_by_user(user_id)

        # Member has no bookings
        if not bookings:
            return {
                "error": "NOT_FOUND",
                "message": "No booked classes found for this member"
            }, HTTPStatus.NOT_FOUND  # 404


        # This list will store full class details
        result = []

        # Loop through each booking record
        for booking in bookings:

            # Extract class ID from booking
            class_id = booking.get(CLASS_ID)

            # Retrieve full class details from classes collection
            fitness_class = class_resource.get_class_by_id(class_id)

            # If class exists, append formatted response
            if fitness_class:
                result.append({
                    "class_id": class_id,
                    "title": fitness_class.get("title"),
                    "start_date": fitness_class.get("start_date"),
                    "end_date": fitness_class.get("end_date"),
                    "location": fitness_class.get("location"),
                    "description": fitness_class.get("description")
                })

        # Return list of booked classes
        return result, HTTPStatus.OK