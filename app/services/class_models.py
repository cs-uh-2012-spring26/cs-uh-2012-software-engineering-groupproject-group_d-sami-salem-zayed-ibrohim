from dataclasses import dataclass
from datetime import datetime
from app.db.classes import (
    CAPACITY,
    CREATED_AT,
    DESCRIPTION,
    END_DATE,
    LOCATION,
    START_DATE,
    TITLE,
    TRAINER_ID,
    TRAINER_NAME,
)


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
        title = payload.get(TITLE)
        start_date_raw = payload.get(START_DATE)
        end_date_raw = payload.get(END_DATE)
        capacity = payload.get(CAPACITY)
        location = payload.get(LOCATION)
        description = payload.get(DESCRIPTION)

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
            TITLE: self.title,
            TRAINER_ID: self.trainer_id,
            TRAINER_NAME: self.trainer_name,
            START_DATE: self.start_date,
            END_DATE: self.end_date,
            CAPACITY: self.capacity,
            LOCATION: self.location,
            DESCRIPTION: self.description,
            CREATED_AT: datetime.now(),
        }
