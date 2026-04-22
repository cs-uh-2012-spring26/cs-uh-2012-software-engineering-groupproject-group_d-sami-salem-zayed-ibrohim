from datetime import datetime
from http import HTTPStatus
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION
from app.db.users import UserResource, ROLE_TRAINER, NAME


class ClassService:

    def __init__(self):
        self.class_resource = ClassResource()
        self.user_resource = UserResource()

    def create_class(self, trainer_email: str, role: str, data: dict):
        """Create a new fitness class after validating role, input, and scheduling."""

        if role != ROLE_TRAINER:
            return {"message": "Only trainers can create classes"}, HTTPStatus.UNAUTHORIZED

        title = data.get(TITLE)
        start_date_str = data.get(START_DATE)
        end_date_str = data.get(END_DATE)
        capacity = data.get(CAPACITY)
        location = data.get(LOCATION)
        description = data.get(DESCRIPTION)

        if not all([title, start_date_str, end_date_str, capacity is not None, location, description]):
            return {
                "message": "All fields are required: title, start_date, end_date, capacity, location, description"
            }, HTTPStatus.BAD_REQUEST

        if capacity <= 0:
            return {"message": "Capacity must be greater than 0"}, HTTPStatus.BAD_REQUEST

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {"message": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"}, HTTPStatus.BAD_REQUEST

        now = datetime.now()
        if start_date < now:
            return {"message": "Start date cannot be in the past"}, HTTPStatus.BAD_REQUEST
        if end_date < now:
            return {"message": "End date cannot be in the past"}, HTTPStatus.BAD_REQUEST
        if end_date <= start_date:
            return {"message": "End date must be after start date"}, HTTPStatus.BAD_REQUEST

        trainer = self.user_resource.get_user_by_email(trainer_email)
        if not trainer:
            return {"message": "Trainer not found"}, HTTPStatus.BAD_REQUEST

        trainer_id = trainer.get("_id")
        trainer_name = trainer.get(NAME)

        if self.class_resource.check_trainer_overlap(trainer_id, start_date, end_date):
            return {"message": "Trainer has overlapping classes at this time"}, HTTPStatus.CONFLICT

        class_id = self.class_resource.create_class(
            title=title,
            trainer_id=trainer_id,
            trainer_name=trainer_name,
            start_date=start_date,
            end_date=end_date,
            capacity=capacity,
            location=location,
            description=description
        )

        created_class = self.class_resource.get_class_by_id(str(class_id))
        return created_class, HTTPStatus.CREATED
