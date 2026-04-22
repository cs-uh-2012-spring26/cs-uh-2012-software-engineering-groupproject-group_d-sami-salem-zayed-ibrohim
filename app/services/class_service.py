from http import HTTPStatus
from app.db.classes import ClassResource
from app.db.bookings import BookingResource
from app.db.users import UserResource, ROLE_TRAINER, NAME
from app.services.class_models import CreateClassRequest


class ClassService:

    def __init__(self):
        self.class_resource = ClassResource()
        self.booking_resource = BookingResource()
        self.user_resource = UserResource()

    def create_class(self, trainer_email: str, role: str, data: dict):
        """Create a new fitness class after validating role, input, and scheduling."""

        if role != ROLE_TRAINER:
            return {"message": "Only trainers can create classes"}, HTTPStatus.UNAUTHORIZED

        try:
            class_request = CreateClassRequest.from_payload(data)
        except ValueError as error:
            return {"message": str(error)}, HTTPStatus.BAD_REQUEST

        trainer = self.user_resource.get_user_by_email(trainer_email)
        if not trainer:
            return {"message": "Trainer not found"}, HTTPStatus.BAD_REQUEST

        trainer_id = trainer.get("_id")
        trainer_name = trainer.get(NAME)

        if self.class_resource.check_trainer_overlap(
            trainer_id,
            class_request.schedule.start_date,
            class_request.schedule.end_date,
        ):
            return {"message": "Trainer has overlapping classes at this time"}, HTTPStatus.CONFLICT

        class_record = class_request.to_record(trainer_id=trainer_id, trainer_name=trainer_name)
        class_id = self.class_resource.create_class(class_record)

        created_class = self.class_resource.get_class_by_id(str(class_id))
        return created_class, HTTPStatus.CREATED

    def get_upcoming_classes(self):
        """Return upcoming classes with remaining spots for the list endpoint."""
        upcoming_classes = self.class_resource.get_upcoming_classes()
        result = []

        for fitness_class in upcoming_classes:
            class_id = self.class_resource.get_class_id(fitness_class)
            capacity = self.class_resource.get_capacity(fitness_class)
            booked_count = self.booking_resource.count_member_bookings(class_id)
            remaining_spots = max(capacity - booked_count, 0)
            result.append(self.class_resource.to_dict(fitness_class, remaining_spots))

        return result, HTTPStatus.OK
