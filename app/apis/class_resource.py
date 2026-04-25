from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required
from http import HTTPStatus
from app.db.classes import (
    CAPACITY,
    CREATED_AT,
    DESCRIPTION,
    END_DATE,
    LOCATION,
    REMAINING_SPOTS,
    START_DATE,
    TITLE,
    TRAINER_ID,
    TRAINER_NAME,
)
from app.db.constants import ID
from app.services.auth_context import get_authenticated_user
from app.services.class_service import ClassService

api = Namespace("classes", description="Class management endpoints")

recurrence_model = api.model("ClassRecurrence", {
    "frequency": fields.String(
        required=True,
        description="Recurrence frequency",
        example="daily",
        enum=["daily", "weekly", "monthly"],
    ),
    "occurrences": fields.Integer(
        required=True,
        description="Total number of class occurrences including the first",
        example=5,
    ),
})

create_class_model = api.model("CreateClass", {
    TITLE: fields.String(required=True, description="Class title", example="Yoga for Beginners"),
    START_DATE: fields.String(required=True, description="Class start date (YYYY-MM-DD HH:MM:SS)", example="2026-03-01 10:00:00"),
    END_DATE: fields.String(required=True, description="Class end date (YYYY-MM-DD HH:MM:SS)", example="2026-03-01 11:00:00"),
    CAPACITY: fields.Integer(required=True, description="Class capacity", example=20),
    LOCATION: fields.String(required=True, description="Class location", example="Studio A"),
    DESCRIPTION: fields.String(required=True, description="Class description", example="A beginner-friendly yoga class"),
    "recurrence": fields.Nested(recurrence_model, required=False, description="Optional recurrence rules for repeated classes")
})

class_response = api.model("ClassResponse", {
    ID: fields.String(description="Class ID"),
    TITLE: fields.String(description="Class title"),
    TRAINER_ID: fields.String(description="Trainer ID"),
    TRAINER_NAME: fields.String(description="Trainer name"),
    START_DATE: fields.String(description="Class start date"),
    END_DATE: fields.String(description="Class end date"),
    CAPACITY: fields.Integer(description="Class capacity"),
    LOCATION: fields.String(description="Class location"),
    DESCRIPTION: fields.String(description="Class description"),
    CREATED_AT: fields.String(description="Creation timestamp"),
    REMAINING_SPOTS: fields.Integer(description="Open spots remaining for booking")
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
        auth_user = get_authenticated_user()
        data = request.json
        return ClassService().create_class(auth_user.email, auth_user.role, data)

    @api.response(HTTPStatus.OK, "Upcoming classes retrieved successfully", [class_response])
    def get(self):
        """Get all upcoming classes (any user)"""
        return ClassService().get_upcoming_classes()
