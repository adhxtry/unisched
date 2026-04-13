from unisched.domain.constraints import (
    calculate_penalty,
    compute_student_conflicts,
)
from unisched.domain.models import Course, ExamEvent, Schedule, TimeSlot


def test_timeslot_validation_and_ordering() -> None:
    early = TimeSlot(day=1, slot_index=1)
    late = TimeSlot(day=1, slot_index=2)

    assert early < late


def test_conflict_computation_and_penalty() -> None:
    course_a = Course(code="A", students=frozenset({"s1", "s2"}))
    course_b = Course(code="B", students=frozenset({"s2", "s3"}))
    course_c = Course(code="C", students=frozenset({"s4"}))

    conflicts = compute_student_conflicts([course_a, course_b, course_c])

    assert len(conflicts) == 1
    assert conflicts[0].course_a == "A"
    assert conflicts[0].course_b == "B"
    assert conflicts[0].shared_students == 1

    assignments = {
        "A": TimeSlot(day=1, slot_index=1),
        "B": TimeSlot(day=1, slot_index=2),
        "C": TimeSlot(day=2, slot_index=1),
    }

    assert calculate_penalty(assignments, conflicts) == 1


def test_schedule_assignment_map_and_completeness() -> None:
    schedule = Schedule(
        events=[
            ExamEvent(course_code="A", time_slot=TimeSlot(day=1, slot_index=1)),
            ExamEvent(course_code="B", time_slot=TimeSlot(day=1, slot_index=2)),
        ],
        unscheduled_courses=[],
        penalty=0,
    )

    mapping = schedule.assignment_map()

    assert mapping["A"] == TimeSlot(day=1, slot_index=1)
    assert schedule.is_complete is True
