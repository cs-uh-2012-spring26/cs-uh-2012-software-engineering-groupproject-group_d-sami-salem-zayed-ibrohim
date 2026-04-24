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

        class_records = class_request.to_records(trainer_id=trainer_id, trainer_name=trainer_name)

        for record in class_records:
            if self.class_resource.check_trainer_overlap(
                trainer_id,
                record.start_date,
                record.end_date,
            ):
                return {"message": "Trainer has overlapping classes at this time"}, HTTPStatus.CONFLICT

        created_classes = []
        for record in class_records:
            class_id = self.class_resource.create_class(record)
            created_classes.append(self.class_resource.get_class_by_id(str(class_id)))

        if len(created_classes) == 1:
            return created_classes[0], HTTPStatus.CREATED

        return created_classes, HTTPStatus.CREATED

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
