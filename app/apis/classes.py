from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from http import HTTPStatus
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION, TRAINER_ID
from app.db.users import UserResource, ROLE_TRAINER, NAME
from app.db.bookings import BookingResource, USER_NAME, USER_EMAIL, BOOKING_TIME, CLASS_ID
from datetime import datetime
from app.config import Config
from app.services.class_creation_service import ClassCreationService, OverlapError

api = Namespace("classes", description="Class management endpoints")

# Models
create_class_model = api.model("CreateClass", {
    TITLE: fields.String(required=True, description="Class title", example="Yoga for Beginners"),
    START_DATE: fields.String(required=True, description="Class start date (YYYY-MM-DD HH:MM:SS)", example="2026-03-01 10:00:00"),
    END_DATE: fields.String(required=True, description="Class end date (YYYY-MM-DD HH:MM:SS)", example="2026-03-01 11:00:00"),
    CAPACITY: fields.Integer(required=True, description="Class capacity", example=20),
    LOCATION: fields.String(required=True, description="Class location", example="Studio A"),
    DESCRIPTION: fields.String(required=True, description="Class description", example="A beginner-friendly yoga class"),
    "recurrence_type": fields.String(required=False, description="Recurrence type: none, daily, weekly, monthly", example="daily"),
    "recurrence_end_date": fields.String(required=False, description="End date for recurrence (YYYY-MM-DD)", example="2026-03-31")
})

class_response = api.model("ClassResponse", {
    "_id": fields.String(description="Class ID"),
    TITLE: fields.String(description="Class title"),
    "trainer_id": fields.String(description="Trainer ID"),
    "trainer_name": fields.String(description="Trainer name"),
    START_DATE: fields.String(description="Class start date"),
    END_DATE: fields.String(description="Class end date"),
    CAPACITY: fields.Integer(description="Class capacity"),
    LOCATION: fields.String(description="Class location"),
    DESCRIPTION: fields.String(description="Class description"),
    "created_at": fields.String(description="Creation timestamp")
})

created_classes_response = api.model("CreatedClassesResponse", {
    "created_classes": fields.List(fields.Nested(class_response), description="List of created classes"),
    "message": fields.String(description="Success message")
})

member_response = api.model("MemberResponse", {
    USER_NAME: fields.String(description="Member name"),
    USER_EMAIL: fields.String(description="Member email"),
    BOOKING_TIME: fields.String(description="Booking timestamp")
})


@api.route("")
class Classes(Resource):
    @api.expect(create_class_model)
    @api.response(HTTPStatus.CREATED, "Class(es) created successfully", created_classes_response)
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid input or validation error")
    @api.response(HTTPStatus.UNAUTHORIZED, "Unauthorized - Trainer role required")
    @api.response(HTTPStatus.CONFLICT, "Trainer has overlapping classes")
    @api.doc(security='Bearer')
    @jwt_required()
    def post(self):
        """Create a new fitness class or recurring classes (trainer only)"""
        # Get JWT claims
        claims = get_jwt()
        role = claims.get("role")
        trainer_email = get_jwt_identity()

        # Check if user is a trainer
        if role != ROLE_TRAINER:
            return {"message": "Only trainers can create classes"}, HTTPStatus.UNAUTHORIZED

        # Parse request body
        data = request.json

        # Validate required fields
        required_fields = [TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION]
        if not all(data.get(field) is not None for field in required_fields):
            return {"message": "All fields are required: title, start_date, end_date, capacity, location, description"}, HTTPStatus.BAD_REQUEST

        # Validate capacity
        if data[CAPACITY] <= 0:
            return {"message": "Capacity must be greater than 0"}, HTTPStatus.BAD_REQUEST

        # Set default recurrence_type if not provided
        if "recurrence_type" not in data:
            data["recurrence_type"] = "none"

        # Use the service to create classes
        service = ClassCreationService()
        try:
            created_ids = service.create_class(trainer_email, data)
        except OverlapError as e:
            return {"message": str(e)}, HTTPStatus.CONFLICT
        except ValueError as e:
            return {"message": str(e)}, HTTPStatus.BAD_REQUEST

        # Get the created classes
        class_resource = ClassResource()
        created_classes = [class_resource.get_class_by_id(str(cid)) for cid in created_ids]

        return {
            "created_classes": created_classes,
            "message": f"{'Class' if len(created_classes) == 1 else 'Classes'} created successfully"
        }, HTTPStatus.CREATED


    # Implementing Feature 2
    @api.response(HTTPStatus.OK, "Upcoming classes retrieved successfully", [class_response])
    def get(self):
        """Get all upcoming classes (any user)"""

        # Initialize Database resource heandles
        class_resource = ClassResource()
        booking_resource = BookingResource()

        # Fetch all upcoming classes from the database
        upcoming_classes = class_resource.get_upcoming_classes()
        
        # This list will store the final formatted response
        result = []

        # Loop through each class and determine the remaining spots
        for cls in upcoming_classes:

            # Get class ID used to count the bookings
            class_id = str(cls.get("_id"))

            # The class activity (default is zero if missing)
            capacity = cls.get(CAPACITY, 0)

            # Count how many members booked this class, and use it to determine the remaining spots (class capacity - number of booked members)
            booked_count = booking_resource.count_member_bookings(class_id)
            remaining_spots = max(capacity - booked_count, 0)

            # Print Class Contents for Each Class, including the Class ID and Name, Trainer Name, Start and End Date, Location, Description, and remaining spots
            result.append({
                "_id": cls.get("_id"),
                TITLE: cls.get(TITLE),
                "trainer_name": cls.get("trainer_name"),
                START_DATE: cls.get(START_DATE),
                END_DATE: cls.get(END_DATE),
                LOCATION: cls.get(LOCATION),
                DESCRIPTION: cls.get(DESCRIPTION),
                "remaining_spots": remaining_spots
            })

        # Return the final list of incoming classes and HTTP status: OK
        return result, HTTPStatus.OK




@api.route("/<string:class_id>/members")
class ClassMembers(Resource):
    @api.response(HTTPStatus.OK, "Class members retrieved successfully", [member_response])
    @api.response(HTTPStatus.NOT_FOUND, "Class not found")
    @api.response(HTTPStatus.UNAUTHORIZED, "Unauthorized - Trainer role required or not the class trainer")
    @api.doc(security='Bearer')
    @jwt_required()
    def get(self, class_id):
        """Get members who booked a class (trainer of the class only)"""
        # Get JWT claims
        claims = get_jwt()
        role = claims.get("role")
        user_id = claims.get("user_id")

        # Check if user is a trainer
        if role != ROLE_TRAINER:
            return {"message": "Only trainers can view class members"}, HTTPStatus.UNAUTHORIZED

        # Validate user_id from JWT
        if not user_id:
            return {"message": "Invalid token: user_id not found"}, HTTPStatus.UNAUTHORIZED

        # Get class by ID
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id)

        if not fitness_class:
            return {"message": "Class not found"}, HTTPStatus.NOT_FOUND

        # Check if the trainer trains this class
        class_trainer_id = fitness_class.get(TRAINER_ID)
        if class_trainer_id != user_id:
            return {"message": "You are not authorized to view members of this class"}, HTTPStatus.UNAUTHORIZED

        # Get bookings for this class
        booking_resource = BookingResource()
        bookings = booking_resource.get_bookings_by_class(class_id)

        # Format response with only required fields
        members = []
        for booking in bookings:
            # Skip trainer bookings if any
            if not booking.get("is_trainer", False):
                members.append({
                    USER_NAME: booking.get(USER_NAME),
                    USER_EMAIL: booking.get(USER_EMAIL),
                    BOOKING_TIME: booking.get(BOOKING_TIME)
                })

        return members, HTTPStatus.OK




from app.services.reminder_service import ReminderService
from app.services.ses_email_service import SESEmailService

# Endpoint for sending reminder emails to members of a specific fitness class. Accessible only by the trainer assigned to the class.
@api.route("/<string:class_id>/reminder")
class ClassReminder(Resource):
    @api.doc(security="Bearer")
    @api.response(200, "Reminder emails sent successfully")
    @api.response(404, "Class not found")
    @api.response(403, "Only the assigned trainer of this class can send reminders")
    @api.response(400, "No registered members for this class")
    @api.response(500, "Failed to send one or more emails")
    @jwt_required()

    # Triggers reminder emails for a class. Validates the trainer role and uses ReminderService to send emails to all registered members.
    def post(self, class_id):
        claims = get_jwt()
        trainer_id = claims.get("user_id")
        role = claims.get("role")

        # Check trainer role
        if role != ROLE_TRAINER:
            return {
                "message": "Access denied. Only trainers can send class reminders."
            }, 403
        

        reminder_service = ReminderService(
            SESEmailService(Config.SES_SENDER_EMAIL)
        )

        return reminder_service.send_reminder(class_id, trainer_id)
