from app.apis.auth import api as auth_ns
from app.apis.classes import api as class_ns
from app.config import Config
from app.db import DB

from http import HTTPStatus
from flask import Flask
from flask_restx import Api
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    DB.init_app(app)
    jwt = JWTManager(app)

    authorizations = {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
        }
    }

    api = Api(
        title="Fitness Class Management System",
        version="1.0",
        description="API for managing fitness classes, bookings, and members",
        authorizations=authorizations,
        security='Bearer'
    )

    api.init_app(app)
    api.add_namespace(auth_ns)
    api.add_namespace(class_ns)

    @api.errorhandler(NoAuthorizationError)
    def handle_no_auth(error):
        return {"message": "Missing Authorization Header. Please log in first."}, HTTPStatus.UNAUTHORIZED

    @api.errorhandler(ExpiredSignatureError)
    def handle_expired_token(error):
        return {"message": "Token has expired. Please log in again."}, HTTPStatus.UNAUTHORIZED

    @api.errorhandler(InvalidTokenError)
    def handle_invalid_token(error):
        return {"message": "Invalid token. Please log in again."}, HTTPStatus.UNAUTHORIZED

    @api.errorhandler(Exception)
    def handle_generic_error(error):
        return {"message": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
