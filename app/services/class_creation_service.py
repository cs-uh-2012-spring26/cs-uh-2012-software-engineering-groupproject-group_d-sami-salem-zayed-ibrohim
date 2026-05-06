from datetime import datetime, timedelta
from app.db.classes import ClassResource, TITLE, START_DATE, END_DATE, CAPACITY, LOCATION, DESCRIPTION
from app.db.users import UserResource, ROLE_TRAINER, NAME

class ValidationError(ValueError):
    pass

class OverlapError(ValueError):
    pass

class ClassCreationService:
    def __init__(self):
        self.class_resource = ClassResource()
        self.user_resource = UserResource()

    def create_class(self, trainer_email: str, class_data: dict):
        """
        Create a class or recurring classes based on the provided data.
        Returns a list of created class IDs.
        """
        # Validate trainer
        trainer = self.user_resource.get_user_by_email(trainer_email)
        if not trainer:
            raise ValueError("Trainer not found")
        
        trainer_id = trainer.get("_id")
        trainer_name = trainer.get(NAME)

        # Parse and validate dates
        start_date = self._parse_datetime(class_data[START_DATE])
        end_date = self._parse_datetime(class_data[END_DATE])
        self._validate_dates(start_date, end_date)

        # Get recurrence info
        recurrence_type = class_data.get("recurrence_type", "none")
        recurrence_end_date_str = class_data.get("recurrence_end_date")

        if recurrence_type != "none" and not recurrence_end_date_str:
            raise ValueError("Recurrence end date is required for recurring classes")

        recurrence_end_date = None
        if recurrence_end_date_str:
            recurrence_end_date = self._parse_date(recurrence_end_date_str)
            if recurrence_end_date < start_date.date():
                raise ValueError("Recurrence end date cannot be before start date")

        # Generate class dates
        class_dates = self._generate_class_dates(start_date, end_date, recurrence_type, recurrence_end_date)

        # Check for overlaps
        for sd, ed in class_dates:
            if self.class_resource.check_trainer_overlap(trainer_id, sd, ed):
                raise OverlapError("Trainer has overlapping classes")

        # Create classes
        created_ids = []
        for sd, ed in class_dates:
            class_id = self.class_resource.create_class(
                title=class_data[TITLE],
                trainer_id=trainer_id,
                trainer_name=trainer_name,
                start_date=sd,
                end_date=ed,
                capacity=class_data[CAPACITY],
                location=class_data[LOCATION],
                description=class_data[DESCRIPTION]
            )
            created_ids.append(class_id)

        return created_ids

    def _parse_datetime(self, date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD HH:MM:SS")

    def _parse_date(self, date_str: str) -> datetime.date:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

    def _validate_dates(self, start_date: datetime, end_date: datetime):
        now = datetime.now()
        if start_date < now:
            raise ValueError("Start date cannot be in the past")
        if end_date <= start_date:
            raise ValueError("End date must be after start date")

    def _generate_class_dates(self, start_date: datetime, end_date: datetime, recurrence_type: str, recurrence_end_date):
        """
        Generate list of (start_date, end_date) tuples for the classes.
        """
        dates = [(start_date, end_date)]
        
        if recurrence_type == "none":
            return dates
        
        current_start = start_date
        current_end = end_date
        
        while True:
            if recurrence_type == "daily":
                current_start += timedelta(days=1)
                current_end += timedelta(days=1)
            elif recurrence_type == "weekly":
                current_start += timedelta(weeks=1)
                current_end += timedelta(weeks=1)
            elif recurrence_type == "monthly":
                # Add one month
                if current_start.month == 12:
                    current_start = current_start.replace(year=current_start.year + 1, month=1)
                    current_end = current_end.replace(year=current_end.year + 1, month=1)
                else:
                    current_start = current_start.replace(month=current_start.month + 1)
                    current_end = current_end.replace(month=current_end.month + 1)
            else:
                raise ValueError("Invalid recurrence type")
            
            if current_start.date() > recurrence_end_date:
                break
            
            dates.append((current_start, current_end))
        
        return dates