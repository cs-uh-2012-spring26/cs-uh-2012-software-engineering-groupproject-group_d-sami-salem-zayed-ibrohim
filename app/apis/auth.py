from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import create_access_token
from http import HTTPStatus
from app.db.users import BIRTHDAY, UserResource, EMAIL, PASSWORD, NAME, ROLE, ROLE_MEMBER, ROLE_TRAINER

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
        email = data.get(EMAIL)
        password = data.get(PASSWORD)
        name = data.get(NAME)
        birthday = data.get(BIRTHDAY)
        role = data.get(ROLE, ROLE_MEMBER)

        print(f"Received registration data: {data}")  # Debugging log

        if not all([email, password, name, birthday]):
            return {"message": "Email, password, name, and birthday are required"}, HTTPStatus.BAD_REQUEST
        if role not in [ROLE_MEMBER, ROLE_TRAINER]:
            return {"message": "Invalid role. Must be 'member' or 'trainer'"}, HTTPStatus.BAD_REQUEST

        user_resource = UserResource()
        
        # Check if user already exists
        existing_user = user_resource.get_user_by_email(email)
        if existing_user:
            return {"message": "User already exists"}, HTTPStatus.BAD_REQUEST

        # Create user
        try:
            user_id = user_resource.create_user(email, password, name, birthday, role)
        except Exception as e:
            # Handle duplicate key error from MongoDB unique index
            if "duplicate key" in str(e).lower() or "E11000" in str(e):
                return {"message": "User already exists"}, HTTPStatus.BAD_REQUEST
            raise
        
        # Create access token
        access_token = create_access_token(identity=email, additional_claims={"role": role, "user_id": str(user_id)})
        
        return {
            "access_token": access_token,
            "user": {"email": email, "name": name, "role": role, "_id": str(user_id)}
        }, HTTPStatus.CREATED


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
