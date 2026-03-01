from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from http import HTTPStatus
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION, TRAINER_ID
from app.db.users import UserResource, ROLE_TRAINER, NAME
from app.db.bookings import BookingResource, USER_NAME, USER_EMAIL, BOOKING_TIME, CLASS_ID
from datetime import datetime

api = Namespace("classes", description="Class management endpoints")

# Models
create_class_model = api.model("CreateClass", {
    TITLE: fields.String(required=True, description="Class title", example="Yoga for Beginners"),
    START_DATE: fields.String(required=True, description="Class start date (YYYY-MM-DD HH:MM:SS)", example="2026-03-01 10:00:00"),
    END_DATE: fields.String(required=True, description="Class end date (YYYY-MM-DD HH:MM:SS)", example="2026-03-01 11:00:00"),
    CAPACITY: fields.Integer(required=True, description="Class capacity", example=20),
    LOCATION: fields.String(required=True, description="Class location", example="Studio A"),
    DESCRIPTION: fields.String(required=True, description="Class description", example="A beginner-friendly yoga class")
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

member_response = api.model("MemberResponse", {
    USER_NAME: fields.String(description="Member name"),
    USER_EMAIL: fields.String(description="Member email"),
    BOOKING_TIME: fields.String(description="Booking timestamp")
})


@api.route("")
class Classes(Resource):
    @api.expect(create_class_model)
    @api.response(HTTPStatus.CREATED, "Class created successfully", class_response)
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid input or validation error")
    @api.response(HTTPStatus.UNAUTHORIZED, "Unauthorized - Trainer role required")
    @api.response(HTTPStatus.CONFLICT, "Trainer has overlapping classes")
    @api.doc(security='Bearer')
    @jwt_required()
    def post(self):
        """Create a new fitness class (trainer only)"""
        # Get JWT claims
        claims = get_jwt()
        role = claims.get("role")
        trainer_email = get_jwt_identity()

        # Check if user is a trainer
        if role != ROLE_TRAINER:
            return {"message": "Only trainers can create classes"}, HTTPStatus.UNAUTHORIZED

        # Parse request body
        data = request.json
        title = data.get(TITLE)
        start_date_str = data.get(START_DATE)
        end_date_str = data.get(END_DATE)
        capacity = data.get(CAPACITY)
        location = data.get(LOCATION)
        description = data.get(DESCRIPTION)

        # Validate required fields
        if not all([title, start_date_str, end_date_str, capacity is not None, location, description]):
            return {"message": "All fields are required: title, start_date, end_date, capacity, location, description"}, HTTPStatus.BAD_REQUEST

        # Validate capacity
        if capacity <= 0:
            return {"message": "Capacity must be greater than 0"}, HTTPStatus.BAD_REQUEST

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {"message": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"}, HTTPStatus.BAD_REQUEST

        # Validate dates
        now = datetime.now()
        if start_date < now:
            return {"message": "Start date cannot be in the past"}, HTTPStatus.BAD_REQUEST
        if end_date < now:
            return {"message": "End date cannot be in the past"}, HTTPStatus.BAD_REQUEST
        if end_date <= start_date:
            return {"message": "End date must be after start date"}, HTTPStatus.BAD_REQUEST

        # Get trainer info from database using email
        user_resource = UserResource()
        trainer = user_resource.get_user_by_email(trainer_email)
        
        if not trainer:
            return {"message": "Trainer not found"}, HTTPStatus.BAD_REQUEST
        
        trainer_id = trainer.get("_id")
        trainer_name = trainer.get(NAME)

        # Check for overlapping classes
        class_resource = ClassResource()
        if class_resource.check_trainer_overlap(trainer_id, start_date, end_date):
            return {"message": "Trainer has overlapping classes at this time"}, HTTPStatus.CONFLICT

        # Create class
        class_id = class_resource.create_class(
            title=title,
            trainer_id=trainer_id,
            trainer_name=trainer_name,
            start_date=start_date,
            end_date=end_date,
            capacity=capacity,
            location=location,
            description=description
        )

        # Get created class
        created_class = class_resource.get_class_by_id(str(class_id))
        
        return created_class, HTTPStatus.CREATED


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
            SESEmailService("NYUAD.GYM@gmail.com")
        )

        return reminder_service.send_reminder(class_id, trainer_id)