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

    courses_list = list(courses)
    student_to_courses: dict[str, list[str]] = {}
    for course in courses_list:
        for student in course.students:
            student_to_courses.setdefault(student, []).append(course.code)

    pair_counts: dict[tuple[str, str], int] = {}
    for enrolled in student_to_courses.values():
        if len(enrolled) < 2:
            continue
        for i in range(len(enrolled)):
            c1 = enrolled[i]
            for j in range(i + 1, len(enrolled)):
                c2 = enrolled[j]
                if c1 == c2:
                    continue
                pair = (c1, c2) if c1 < c2 else (c2, c1)
                pair_counts[pair] = pair_counts.get(pair, 0) + 1

    return [
        ConflictModel(
            course_a=c1,
            course_b=c2,
            shared_students=count,
        )
        for (c1, c2), count in sorted(pair_counts.items())
    ]


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
