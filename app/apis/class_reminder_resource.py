from flask_restx import Resource
from flask_jwt_extended import jwt_required, get_jwt
from app.db.users import ROLE_TRAINER
from app.services.reminder_service import ReminderService
from app.services.ses_email_service import SESEmailService
from app.config import Config
from app.apis.class_resource import api


@api.route("/<string:class_id>/reminder")
class ClassReminder(Resource):
    @api.doc(security="Bearer")
    @api.response(200, "Reminder emails sent successfully")
    @api.response(404, "Class not found")
    @api.response(403, "Only the assigned trainer of this class can send reminders")
    @api.response(400, "No registered members for this class")
    @api.response(500, "Failed to send one or more emails")
    @jwt_required()
    def post(self, class_id):
        """Send reminder emails to all members of a class (trainer only)"""
        claims = get_jwt()
        trainer_id = claims.get("user_id")
        role = claims.get("role")

        if role != ROLE_TRAINER:
            return {"message": "Access denied. Only trainers can send class reminders."}, 403

        reminder_service = ReminderService(SESEmailService(Config.SES_SENDER_EMAIL))
        return reminder_service.send_reminder(class_id, trainer_id)
