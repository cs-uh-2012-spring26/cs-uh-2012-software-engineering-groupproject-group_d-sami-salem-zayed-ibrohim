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
        # Get the class
        fitness_class = self.class_resource.get_class_by_id(class_id)
        if not fitness_class:
            return {"message": "Class not found"}, 404

        # Ensure the trainer made this class
        if fitness_class.get(TRAINER_ID) != trainer_id:
            return {"message": "Forbidden: Not the trainer of this class"}, 403

        # Check if the class has already ended
        end_date = fitness_class.get(END_DATE)
        try:
            end_date_dt = ClassSchedule.parse_datetime(end_date)
            if end_date_dt < datetime.now():
                return {"message": "Cannot send reminders for a class that has already ended"}, 400
        except (ValueError, TypeError):
            # If date parsing fails, continue with reminder sending
            pass

        # Get all bookings for the class
        bookings = self.booking_resource.get_bookings_by_class(class_id)

        # No members booked this class
        if not bookings:
            return {"message": "No registered members for this class"}, 400

        # Send a notification to each booked member. Trainers cannot be added to class bookings.
        for booking in bookings:

            email = booking.get(USER_EMAIL)
            name = booking.get(USER_NAME)

            # The notification body includes the core class details.
            subject = f"NYUAD GYM Reminder: {fitness_class.get(TITLE)}"
            body = (
                f"Hi {name},\n\n"
                f"This is a reminder for your upcoming class at NYUAD GYM:\n\n"
                f"Class: {fitness_class.get(TITLE)}\n"
                f"Date & Time: {fitness_class.get(START_DATE)} to {fitness_class.get(END_DATE)}\n"
                f"Location: {fitness_class.get(LOCATION, 'TBD')}\n"
                f"Instructor: {fitness_class.get(TRAINER_NAME, 'TBD')}\n\n"
                "We look forward to seeing you there!\n\n"
                "Best regards,\n"
                "NYUAD GYM Team"
            )

            self.notification_service.send_notification(email, subject, body)

        return {"message": "Reminders sent successfully"}, 200