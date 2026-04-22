from dataclasses import dataclass

from flask_jwt_extended import get_jwt, get_jwt_identity


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str = None
    role: str = None
    email: str = None


def get_authenticated_user():
    claims = get_jwt()
    return AuthenticatedUser(
        user_id=claims.get("user_id"),
        role=claims.get("role"),
        email=get_jwt_identity(),
    )
