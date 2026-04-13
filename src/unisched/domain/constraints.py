"""Conflict and penalty helpers for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping

from .models import Course, Schedule, TimeSlot


@dataclass(frozen=True, slots=True)
class ConflictModel:
    """Represent a pair-wise conflict between two courses."""

    course_a: str
    course_b: str
    shared_students: int


def compute_student_conflicts(courses: Iterable[Course]) -> list[ConflictModel]:
    """Build pairwise conflicts for courses sharing one or more students."""

    result: list[ConflictModel] = []
    sorted_courses = sorted(courses, key=lambda course: course.code)

    for course_a, course_b in combinations(sorted_courses, 2):
        overlap = len(course_a.students & course_b.students)
        if overlap > 0:
            result.append(
                ConflictModel(
                    course_a=course_a.code,
                    course_b=course_b.code,
                    shared_students=overlap,
                )
            )

    return result


def calculate_penalty(
    assignments: Mapping[str, TimeSlot],
    conflicts: Iterable[ConflictModel],
    *,
    same_day_weight: int = 1,
) -> int:
    """Calculate a simple penalty based on same-day conflicting exams."""

    if same_day_weight < 0:
        raise ValueError("same_day_weight must be >= 0")

    penalty = 0
    for conflict in conflicts:
        slot_a = assignments.get(conflict.course_a)
        slot_b = assignments.get(conflict.course_b)
        if slot_a is None or slot_b is None:
            continue

        if slot_a.day == slot_b.day:
            penalty += conflict.shared_students * same_day_weight

    return penalty


def calculate_schedule_penalty(
    schedule: Schedule,
    conflicts: Iterable[ConflictModel],
    *,
    same_day_weight: int = 1,
) -> int:
    """Calculate penalty directly from a schedule object."""

    return calculate_penalty(
        schedule.assignment_map(),
        conflicts,
        same_day_weight=same_day_weight,
    )
