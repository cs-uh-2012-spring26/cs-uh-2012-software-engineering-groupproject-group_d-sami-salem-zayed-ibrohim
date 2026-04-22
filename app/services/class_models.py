from dataclasses import dataclass
from datetime import datetime


CLASS_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class ClassSchedule:
    start_date: datetime
    end_date: datetime

    @staticmethod
    def parse_datetime(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.strptime(value, CLASS_DATE_FORMAT)
        raise TypeError("Unsupported datetime value")

    @classmethod
    def from_strings(cls, start_date_raw: str, end_date_raw: str):
        try:
            return cls(
                start_date=cls.parse_datetime(start_date_raw),
                end_date=cls.parse_datetime(end_date_raw),
            )
        except ValueError as error:
            raise ValueError("Invalid date format. Use YYYY-MM-DD HH:MM:SS") from error

    def validate(self, now: datetime):
        if self.start_date < now:
            raise ValueError("Start date cannot be in the past")
        if self.end_date < now:
            raise ValueError("End date cannot be in the past")
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")


@dataclass(frozen=True)
class CreateClassRequest:
    title: str
    schedule: ClassSchedule
    capacity: int
    location: str
    description: str

    @classmethod
    def from_payload(cls, payload: dict):
        title = payload.get("title")
        start_date_raw = payload.get("start_date")
        end_date_raw = payload.get("end_date")
        capacity = payload.get("capacity")
        location = payload.get("location")
        description = payload.get("description")

        if not all([title, start_date_raw, end_date_raw, capacity is not None, location, description]):
            raise ValueError(
                "All fields are required: title, start_date, end_date, capacity, location, description"
            )

        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0")

        schedule = ClassSchedule.from_strings(start_date_raw, end_date_raw)
        schedule.validate(datetime.now())

        return cls(
            title=title,
            schedule=schedule,
            capacity=capacity,
            location=location,
            description=description,
        )

    def to_record(self, trainer_id: str, trainer_name: str):
        return ClassRecord(
            title=self.title,
            trainer_id=trainer_id,
            trainer_name=trainer_name,
            start_date=self.schedule.start_date,
            end_date=self.schedule.end_date,
            capacity=self.capacity,
            location=self.location,
            description=self.description,
        )


@dataclass(frozen=True)
class ClassRecord:
    title: str
    trainer_id: str
    trainer_name: str
    start_date: datetime
    end_date: datetime
    capacity: int
    location: str
    description: str

    def to_document(self):
        return {
            "title": self.title,
            "trainer_id": self.trainer_id,
            "trainer_name": self.trainer_name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "capacity": self.capacity,
            "location": self.location,
            "description": self.description,
            "created_at": datetime.now(),
        }
