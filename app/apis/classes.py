from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from http import HTTPStatus
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION
from app.db.users import UserResource, ROLE_TRAINER, NAME
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
