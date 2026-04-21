from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt
from http import HTTPStatus
from app.db.bookings import USER_NAME, USER_EMAIL, BOOKING_TIME
from app.services.class_members_service import ClassMembersService
from app.apis.class_resource import api

member_response = api.model("MemberResponse", {
    USER_NAME: fields.String(description="Member name"),
    USER_EMAIL: fields.String(description="Member email"),
    BOOKING_TIME: fields.String(description="Booking timestamp")
})


@api.route("/<string:class_id>/members")
class ClassMembers(Resource):
    @api.response(HTTPStatus.OK, "Class members retrieved successfully", [member_response])
    @api.response(HTTPStatus.NOT_FOUND, "Class not found")
    @api.response(HTTPStatus.UNAUTHORIZED, "Unauthorized - Trainer role required or not the class trainer")
    @api.doc(security='Bearer')
    @jwt_required()
    def get(self, class_id):
        """Get members who booked a class (trainer of the class only)"""
        claims = get_jwt()
        return ClassMembersService().get_class_members(
            class_id=class_id,
            user_id=claims.get("user_id"),
            role=claims.get("role")
        )
