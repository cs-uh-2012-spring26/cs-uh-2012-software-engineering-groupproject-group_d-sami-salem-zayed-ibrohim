from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from http import HTTPStatus
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION
from app.db.bookings import BookingResource
from app.services.class_service import ClassService

api = Namespace("classes", description="Class management endpoints")

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
        trainer_email = get_jwt_identity()
        role = get_jwt().get("role")
        data = request.json
        return ClassService().create_class(trainer_email, role, data)

    @api.response(HTTPStatus.OK, "Upcoming classes retrieved successfully", [class_response])
    def get(self):
        """Get all upcoming classes (any user)"""
        class_resource = ClassResource()
        booking_resource = BookingResource()
        upcoming_classes = class_resource.get_upcoming_classes()
        result = []
        for cls in upcoming_classes:
            class_id = str(cls.get("_id"))
            capacity = cls.get(CAPACITY, 0)
            booked_count = booking_resource.count_member_bookings(class_id)
            remaining_spots = max(capacity - booked_count, 0)
            result.append(class_resource.to_dict(cls, remaining_spots))
        return result, HTTPStatus.OK
