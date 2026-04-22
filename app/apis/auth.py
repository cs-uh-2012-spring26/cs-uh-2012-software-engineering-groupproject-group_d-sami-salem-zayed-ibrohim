from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import create_access_token
from http import HTTPStatus
from app.db.users import BIRTHDAY, UserResource, EMAIL, PASSWORD, NAME, ROLE, ROLE_MEMBER, ROLE_TRAINER
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
        data = request.json
        email = data.get(EMAIL)
        password = data.get(PASSWORD)

        if not all([email, password]):
            return {"message": "Email and password are required"}, HTTPStatus.BAD_REQUEST

        user_resource = UserResource()
        user = user_resource.verify_password(email, password)

        if not user:
            return {"message": "Invalid email or password"}, HTTPStatus.UNAUTHORIZED

        # Create access token
        access_token = create_access_token(
            identity=email, 
            additional_claims={"role": user[ROLE], "user_id": user["_id"]}
        )
        
        # Remove password from response
        user.pop(PASSWORD, None)
        
        return {
            "access_token": access_token,
            "user": user
        }, HTTPStatus.OK
