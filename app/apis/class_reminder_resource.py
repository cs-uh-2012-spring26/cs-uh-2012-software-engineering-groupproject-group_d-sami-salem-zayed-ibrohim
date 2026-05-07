from flask_restx import Resource
from flask_jwt_extended import jwt_required
from flask import current_app
from app.db.users import CHANNEL_EMAIL, CHANNEL_TELEGRAM, ROLE_TRAINER
from app.services.auth_context import get_authenticated_user
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.reminder_service import ReminderService
from app.services.ses_email_service import SESEmailService
from app.services.telegram_notification_service import TelegramNotificationService
from app.apis.class_resource import api


@api.route("/<string:class_id>/reminder")
class ClassReminder(Resource):
    @api.doc(
        security="Bearer",
        params={"class_id": "ID of the class whose booked members should receive reminders"},
    )
    @api.response(200, "Class reminders sent successfully")
    @api.response(404, "Class not found")
    @api.response(403, "Only the assigned trainer of this class can send reminders")
    @api.response(400, "No registered members for this class")
    @api.response(500, "Failed to send one or more notifications")
    @jwt_required()
    def post(self, class_id):
        """Send reminders to members using their configured channels (trainer only)"""
        auth_user = get_authenticated_user()

        if auth_user.role != ROLE_TRAINER:
            return {"message": "Access denied. Only trainers can send class reminders."}, 403

        dispatcher = NotificationDispatcher({
            CHANNEL_EMAIL: SESEmailService(current_app.config.get("SES_SENDER_EMAIL")),
            CHANNEL_TELEGRAM: TelegramNotificationService(current_app.config.get("TELEGRAM_BOT_TOKEN")),
        })
        reminder_service = ReminderService(dispatcher)
        return reminder_service.send_reminder(class_id, auth_user.user_id)
