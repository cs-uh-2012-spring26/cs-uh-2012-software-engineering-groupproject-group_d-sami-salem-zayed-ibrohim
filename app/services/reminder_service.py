from app.db.classes import ClassResource, TRAINER_ID, TITLE, START_DATE, END_DATE
from app.db.bookings import BookingResource, USER_EMAIL, USER_NAME

class ReminderService:

    def __init__(self, email_service):
        self.email_service = email_service
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

        # Get all bookings for the class
        bookings = self.booking_resource.get_bookings_by_class(class_id)

        # No members booked this class
        if not bookings:
            return {"message": "No registered members for this class"}, 400

        # Send email to each booked member. Note that trainers cannot be added to the class booking anyways, so no checking is needed.
        for booking in bookings:

            email = booking.get(USER_EMAIL)
            name = booking.get(USER_NAME)

            # The email mentions all the class details
            subject = f"NYUAD GYM Reminder: {fitness_class.get(TITLE)}"
            body = (
                f"Hi {name},\n\n"
                f"This is a reminder for your upcoming class at NYUAD GYM:\n\n"
                f"Class: {fitness_class.get(TITLE)}\n"
                f"Date & Time: {fitness_class.get(START_DATE)} to {fitness_class.get(END_DATE)}\n"
                f"Location: {fitness_class.get('location', 'TBD')}\n"
                f"Instructor: {fitness_class.get('trainer_name', 'TBD')}\n\n"
                "We look forward to seeing you there!\n\n"
                "Best regards,\n"
                "NYUAD GYM Team"
            )

            self.email_service.send_email(email, subject, body)

        return {"message": "Reminders sent successfully"}, 200