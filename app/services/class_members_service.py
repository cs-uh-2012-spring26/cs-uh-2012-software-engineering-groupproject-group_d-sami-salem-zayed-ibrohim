from http import HTTPStatus
from app.db.classes import ClassResource, TRAINER_ID
from app.db.bookings import BookingResource, USER_NAME, USER_EMAIL, BOOKING_TIME, IS_TRAINER
from app.db.users import ROLE_TRAINER


class ClassMembersService:

    def __init__(self):
        self.class_resource = ClassResource()
        self.booking_resource = BookingResource()

    def get_class_members(self, class_id: str, user_id: str, role: str):
        """Return the list of members booked in a class (trainer of the class only)."""
        if role != ROLE_TRAINER:
            return {"message": "Only trainers can view class members"}, HTTPStatus.UNAUTHORIZED

        if not user_id:
            return {"message": "Invalid token: user_id not found"}, HTTPStatus.UNAUTHORIZED

        fitness_class = self.class_resource.get_class_by_id(class_id)
        if not fitness_class:
            return {"message": "Class not found"}, HTTPStatus.NOT_FOUND

        if fitness_class.get(TRAINER_ID) != user_id:
            return {"message": "You are not authorized to view members of this class"}, HTTPStatus.UNAUTHORIZED

        bookings = self.booking_resource.get_bookings_by_class(class_id)
        members = []
        for booking in bookings:
            if not booking.get(IS_TRAINER, False):
                members.append({
                    USER_NAME: booking.get(USER_NAME),
                    USER_EMAIL: booking.get(USER_EMAIL),
                    BOOKING_TIME: booking.get(BOOKING_TIME)
                })

        return members, HTTPStatus.OK
