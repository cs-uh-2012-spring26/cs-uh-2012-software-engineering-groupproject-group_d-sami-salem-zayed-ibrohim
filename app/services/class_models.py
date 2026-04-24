from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import calendar


CLASS_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
VALID_RECURRENCE_FREQUENCIES = {"daily", "weekly", "monthly"}


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
class RecurrenceRule:
    frequency: str
    occurrences: int

    @classmethod
    def from_payload(cls, payload: dict):
        if not isinstance(payload, dict):
            raise ValueError("Recurrence must be an object with frequency and occurrences")

        frequency = payload.get("frequency")
        occurrences = payload.get("occurrences")

        if frequency not in VALID_RECURRENCE_FREQUENCIES:
            raise ValueError("Recurrence frequency must be one of daily, weekly, or monthly")

        if not isinstance(occurrences, int) or occurrences < 2:
            raise ValueError("Recurrence occurrences must be an integer greater than 1")

        return cls(frequency=frequency, occurrences=occurrences)

    def generate_schedules(self, base_schedule: ClassSchedule):
        schedules = [base_schedule]

        for index in range(1, self.occurrences):
            schedules.append(
                ClassSchedule(
                    start_date=self._advance(base_schedule.start_date, index),
                    end_date=self._advance(base_schedule.end_date, index),
                )
            )

        return schedules

    def _advance(self, value: datetime, step: int):
        if self.frequency == "daily":
            return value + timedelta(days=step)
        if self.frequency == "weekly":
            return value + timedelta(weeks=step)
        return self._add_months(value, step)

    @staticmethod
    def _add_months(value: datetime, months: int):
        month = value.month - 1 + months
        year = value.year + month // 12
        month = month % 12 + 1
        day = min(value.day, calendar.monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)


@dataclass(frozen=True)
class CreateClassRequest:
    title: str
    schedule: ClassSchedule
    capacity: int
    location: str
    description: str
    recurrence: Optional[RecurrenceRule] = None

    @classmethod
    def from_payload(cls, payload: dict):
        title = payload.get("title")
        start_date_raw = payload.get("start_date")
        end_date_raw = payload.get("end_date")
        capacity = payload.get("capacity")
        location = payload.get("location")
        description = payload.get("description")
        recurrence_payload = payload.get("recurrence")

        if not all([title, start_date_raw, end_date_raw, capacity is not None, location, description]):
            raise ValueError(
                "All fields are required: title, start_date, end_date, capacity, location, description"
            )

        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0")

        schedule = ClassSchedule.from_strings(start_date_raw, end_date_raw)
        schedule.validate(datetime.now())

        recurrence = None
        if recurrence_payload is not None:
            recurrence = RecurrenceRule.from_payload(recurrence_payload)

        return cls(
            title=title,
            schedule=schedule,
            capacity=capacity,
            location=location,
            description=description,
            recurrence=recurrence,
        )

    def get_schedules(self):
        if self.recurrence is None:
            return [self.schedule]
        return self.recurrence.generate_schedules(self.schedule)

    def to_records(self, trainer_id: str, trainer_name: str):
        return [
            ClassRecord(
                title=self.title,
                trainer_id=trainer_id,
                trainer_name=trainer_name,
                start_date=schedule.start_date,
                end_date=schedule.end_date,
                capacity=self.capacity,
                location=self.location,
                description=self.description,
            )
            for schedule in self.get_schedules()
        ]


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
