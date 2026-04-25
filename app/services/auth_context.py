from dataclasses import dataclass

from flask_jwt_extended import get_jwt, get_jwt_identity


USER_ID_CLAIM = "user_id"
ROLE_CLAIM = "role"


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str = None
    role: str = None
    email: str = None


def get_authenticated_user():
    claims = get_jwt()
    return AuthenticatedUser(
        user_id=claims.get(USER_ID_CLAIM),
        role=claims.get(ROLE_CLAIM),
        email=get_jwt_identity(),
    )
