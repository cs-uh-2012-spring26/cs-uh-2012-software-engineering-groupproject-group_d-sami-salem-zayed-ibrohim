from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource, fields
from http import HTTPStatus

from app.db.users import CHANNELS, NOTIFICATION_PREFERENCES
from app.services.auth_context import get_authenticated_user
from app.services.user_notification_service import UserNotificationService


api = Namespace("notifications", description="User notification preference endpoints")

notification_preferences_model = api.model("UserNotificationPreferences", {
    CHANNELS: fields.List(
        fields.String(enum=["email", "telegram"]),
        required=True,
        description="Notification channels selected for the current user",
        example=["email", "telegram"],
    ),
})

notification_settings_response = api.model("UserNotificationSettingsResponse", {
    "message": fields.String(description="Result message"),
    NOTIFICATION_PREFERENCES: fields.Nested(notification_preferences_model),
    "telegram_connected": fields.Boolean(description="Whether Telegram has been linked"),
    "telegram_launch_url": fields.String(description="User-specific Telegram bot launch URL"),
})


@api.route("")
class NotificationSettings(Resource):
    @api.response(HTTPStatus.OK, "Notification settings retrieved", notification_settings_response)
    @api.response(HTTPStatus.UNAUTHORIZED, "Authentication required or invalid token")
    @api.response(HTTPStatus.FORBIDDEN, "Only members can configure notification preferences")
    @api.doc(security="Bearer")
    @jwt_required()
    def get(self):
        """Get notification preferences and Telegram bot launch URL."""
        auth_user = get_authenticated_user()
        return UserNotificationService().get_notification_settings(
            user_id=auth_user.user_id,
            role=auth_user.role,
        )

    @api.expect(notification_preferences_model)
    @api.response(HTTPStatus.OK, "Notification preferences updated", notification_settings_response)
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid notification preferences")
    @api.response(HTTPStatus.UNAUTHORIZED, "Authentication required or invalid token")
    @api.response(HTTPStatus.FORBIDDEN, "Only members can configure notification preferences")
    @api.doc(security="Bearer")
    @jwt_required()
    def patch(self):
        """Configure email and Telegram reminders for the current user."""
        auth_user = get_authenticated_user()
        return UserNotificationService().update_notification_settings(
            user_id=auth_user.user_id,
            role=auth_user.role,
            data=request.json,
        )
