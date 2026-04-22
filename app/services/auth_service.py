from http import HTTPStatus
from flask_jwt_extended import create_access_token
from app.db.users import UserResource, EMAIL, PASSWORD, NAME, BIRTHDAY, ROLE, ROLE_MEMBER, ROLE_TRAINER


class AuthService:

    def __init__(self):
        self.user_resource = UserResource()

    def register_user(self, data: dict):
        """Validate, create a new user, and return a JWT token."""
        email = data.get(EMAIL)
        password = data.get(PASSWORD)
        name = data.get(NAME)
        birthday = data.get(BIRTHDAY)
        role = data.get(ROLE, ROLE_MEMBER)

        if not all([email, password, name, birthday]):
            return {"message": "Email, password, name, and birthday are required"}, HTTPStatus.BAD_REQUEST

        if role not in [ROLE_MEMBER, ROLE_TRAINER]:
            return {"message": "Invalid role. Must be 'member' or 'trainer'"}, HTTPStatus.BAD_REQUEST

        if self.user_resource.get_user_by_email(email):
            return {"message": "User already exists"}, HTTPStatus.BAD_REQUEST

        try:
            user_id = self.user_resource.create_user(email, password, name, birthday, role)
        except Exception as e:
            if "duplicate key" in str(e).lower() or "E11000" in str(e):
                return {"message": "User already exists"}, HTTPStatus.BAD_REQUEST
            raise

        access_token = create_access_token(
            identity=email,
            additional_claims={"role": role, "user_id": str(user_id)}
        )

        return {
            "access_token": access_token,
            "user": {"email": email, "name": name, "role": role, "_id": str(user_id)}
        }, HTTPStatus.CREATED

    def login_user(self, data: dict):
        """Validate credentials and return a JWT token for an existing user."""
        email = data.get(EMAIL)
        password = data.get(PASSWORD)

        if not all([email, password]):
            return {"message": "Email and password are required"}, HTTPStatus.BAD_REQUEST

        user = self.user_resource.verify_password(email, password)
        if not user:
            return {"message": "Invalid email or password"}, HTTPStatus.UNAUTHORIZED

        access_token = create_access_token(
            identity=email,
            additional_claims={"role": user[ROLE], "user_id": user["_id"]}
        )

        user.pop(PASSWORD, None)
        return {
            "access_token": access_token,
            "user": user
        }, HTTPStatus.OK
