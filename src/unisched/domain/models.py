"""Domain models for the minimal scheduling MVP."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, order=True)
class TimeSlot:
    """Represent a scheduling slot using day and per-day index."""

    day: int
    slot_index: int

    def __post_init__(self) -> None:
        if self.day < 1:
            raise ValueError("day must be >= 1")
        if self.slot_index < 1:
            raise ValueError("slot_index must be >= 1")


@dataclass(frozen=True, slots=True)
class Course:
    """Represent a course and its enrolled students."""

    code: str
    students: frozenset[str]

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ExamHall:
    """Represent an exam hall with seating capacity and allocation group."""

    hall: str
    capacity: int
    group: int

    def __post_init__(self) -> None:
        if not self.hall:
            raise ValueError("hall must be a non-empty string")
        if self.capacity < 1:
            raise ValueError("capacity must be >= 1")
        if self.group < 0:
            raise ValueError("group must be >= 0")


@dataclass(frozen=True, slots=True)
class ExamEvent:
    """Represent a single exam assignment for one course."""

    course_code: str
    time_slot: TimeSlot
    halls: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class Schedule:
    """Represent a computed exam schedule."""

    events: list[ExamEvent] = field(default_factory=list)
    unscheduled_courses: list[str] = field(default_factory=list)
    penalty: int = 0

    def assignment_map(self) -> dict[str, TimeSlot]:
        """Return a mapping from course code to assigned time slot."""

        return {event.course_code: event.time_slot for event in self.events}

    @property
    def is_complete(self) -> bool:
        """Return True when all courses were scheduled."""

        return len(self.unscheduled_courses) == 0
