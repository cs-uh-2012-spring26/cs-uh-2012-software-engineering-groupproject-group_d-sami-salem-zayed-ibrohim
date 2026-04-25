from http import HTTPStatus
from datetime import datetime
from app.db.classes import ClassResource, TRAINER_ID, TITLE, START_DATE, END_DATE, LOCATION, TRAINER_NAME
from app.db.bookings import BookingResource, USER_EMAIL, USER_NAME
from app.services.class_models import ClassSchedule

class ReminderService:

    def __init__(self, notification_service):
        self.notification_service = notification_service
        self.class_resource = ClassResource()
        self.booking_resource = BookingResource()

    def send_reminder(self, class_id: str, trainer_id: str):
        fitness_class, error = self._get_reminder_class(class_id, trainer_id)
        if error:
            return error

        error = self._validate_reminder_date(fitness_class)
        if error:
            return error

        bookings, error = self._get_reminder_recipients(class_id)
        if error:
            return error

        self._send_reminders(fitness_class, bookings)
        return {"message": "Reminders sent successfully"}, HTTPStatus.OK

    def _get_reminder_class(self, class_id: str, trainer_id: str):
        fitness_class = self.class_resource.get_class_by_id(class_id)
        if not fitness_class:
            return None, ({"message": "Class not found"}, HTTPStatus.NOT_FOUND)

        if fitness_class.get(TRAINER_ID) != trainer_id:
            return None, ({"message": "Forbidden: Not the trainer of this class"}, HTTPStatus.FORBIDDEN)

        return fitness_class, None

    def _validate_reminder_date(self, fitness_class: dict):
        try:
            end_date_dt = ClassSchedule.parse_datetime(fitness_class.get(END_DATE))
            if end_date_dt < datetime.now():
                return {"message": "Cannot send reminders for a class that has already ended"}, HTTPStatus.BAD_REQUEST
        except (ValueError, TypeError):
            return {"message": "Cannot send reminders because the class end date is invalid"}, HTTPStatus.BAD_REQUEST

        return None

    def _get_reminder_recipients(self, class_id: str):
        bookings = self.booking_resource.get_bookings_by_class(class_id)
        if not bookings:
            return None, ({"message": "No registered members for this class"}, HTTPStatus.BAD_REQUEST)

        return bookings, None

    def _send_reminders(self, fitness_class: dict, bookings: list):
        for booking in bookings:
            email = booking.get(USER_EMAIL)
            subject, body = self._build_reminder_message(fitness_class, booking)
            self.notification_service.send_notification(email, subject, body)

    def _build_reminder_message(self, fitness_class: dict, booking: dict):
        subject = f"NYUAD GYM Reminder: {fitness_class.get(TITLE)}"
        body = (
            f"Hi {booking.get(USER_NAME)},\n\n"
            f"This is a reminder for your upcoming class at NYUAD GYM:\n\n"
            f"Class: {fitness_class.get(TITLE)}\n"
            f"Date & Time: {fitness_class.get(START_DATE)} to {fitness_class.get(END_DATE)}\n"
            f"Location: {fitness_class.get(LOCATION, 'TBD')}\n"
            f"Instructor: {fitness_class.get(TRAINER_NAME, 'TBD')}\n\n"
            "We look forward to seeing you there!\n\n"
            "Best regards,\n"
            "NYUAD GYM Team"
        )
        return subject, body
