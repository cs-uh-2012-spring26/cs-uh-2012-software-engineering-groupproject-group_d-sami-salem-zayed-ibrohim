from app.apis.auth import api as auth_ns
from app.apis.class_resource import api as class_ns
import app.apis.class_members_resource  # noqa: registers ClassMembers routes to class_ns
import app.apis.class_reminder_resource  # noqa: registers ClassReminder routes to class_ns
from app.apis.booking import api as booking_ns
from app.apis.notifications import api as notifications_ns
from app.db import DB
from app.services.user_notification_service import UserNotificationService
from app.services.telegram_bot_polling_service import start_telegram_bot_polling
from app.swagger_ui import render_swagger_ui

from http import HTTPStatus
from flask import Flask, request
from flask_restx import Api
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

def create_app():
    from app.config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    DB.init_app(app)
    JWTManager(app)

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
    api.add_namespace(booking_ns)
    api.add_namespace(notifications_ns)

    @api.documentation
    def custom_swagger_ui():
        return render_swagger_ui(api)

    @app.route("/telegram/webhook", methods=["POST"])
    def telegram_webhook():
        return UserNotificationService().connect_telegram_from_webhook(request.get_json(silent=True))

    start_telegram_bot_polling(app)

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
