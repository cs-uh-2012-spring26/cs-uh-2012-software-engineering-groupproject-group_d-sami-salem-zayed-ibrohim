from flask_restx import Namespace, Resource, fields
from flask import request
from http import HTTPStatus
from app.db.users import BIRTHDAY, EMAIL, PASSWORD, NAME, ROLE, ROLE_MEMBER, ROLE_TRAINER
from app.services.auth_service import AuthService

api = Namespace("auth", description="Authentication endpoints")

# Models
register_model = api.model("Register", {
    EMAIL: fields.String(required=True, description="User email", example="user@example.com"),
    PASSWORD: fields.String(required=True, description="User password", example="password123"),
    NAME: fields.String(required=True, description="User name", example="John Doe"),
    BIRTHDAY: fields.String(required=True, description="User birthday (YYYY-MM-DD)", example="1990-01-01"),
    ROLE: fields.String(required=True, description="User role", 
                        enum=[ROLE_MEMBER, ROLE_TRAINER], example=ROLE_MEMBER)
})

login_model = api.model("Login", {
    EMAIL: fields.String(required=True, description="User email", example="user@example.com"),
    PASSWORD: fields.String(required=True, description="User password", example="password123")
})

token_response = api.model("TokenResponse", {
    "access_token": fields.String(description="JWT access token"),
    "user": fields.Raw(description="User information")
})


@api.route("/register")
class Register(Resource):
    @api.expect(register_model)
    @api.response(HTTPStatus.CREATED, "User registered successfully", token_response)
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid input or user already exists")
    def post(self):
        """Register a new user (member or trainer)"""
        data = request.json
        return AuthService().register_user(data)


@api.route("/login")
class Login(Resource):
    @api.expect(login_model)
    @api.response(HTTPStatus.OK, "Login successful", token_response)
    @api.response(HTTPStatus.UNAUTHORIZED, "Invalid credentials")
    def post(self):
        """Login and receive JWT token"""
        return AuthService().login_user(request.json)
