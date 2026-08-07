import pytest

from unisched.core.optimizers import (
    SimulatedAnnealingOptimizer,
    optimize_simulated_annealing,
)
from unisched.domain.models import Course, ExamHall, TimeSlot


def _courses() -> list[Course]:
    return [
        Course(code="A", students=frozenset({"s1", "s2"})),
        Course(code="B", students=frozenset({"s2", "s3"})),
        Course(code="C", students=frozenset({"s1", "s4"})),
        Course(code="D", students=frozenset({"s5"})),
    ]


def test_annealing_returns_complete_conflict_free_schedule() -> None:
    slots = [TimeSlot(day=day, slot_index=slot) for day in range(1, 3) for slot in (1, 2)]

    schedule = optimize_simulated_annealing(_courses(), slots, iterations=2_000, random_seed=7)
    assignments = schedule.assignment_map()

    assert schedule.is_complete
    assert assignments["A"] != assignments["B"]
    assert assignments["A"] != assignments["C"]


def test_annealing_is_reproducible() -> None:
    slots = [TimeSlot(day=day, slot_index=slot) for day in range(1, 3) for slot in (1, 2)]

    first = optimize_simulated_annealing(_courses(), slots, iterations=500, random_seed=11)
    second = optimize_simulated_annealing(_courses(), slots, iterations=500, random_seed=11)

    assert first == second


def test_annealing_assigns_halls_and_preserves_capacity() -> None:
    slots = [TimeSlot(day=1, slot_index=1), TimeSlot(day=1, slot_index=2)]
    halls = [ExamHall(hall="H1", capacity=3, group=1)]

    schedule = optimize_simulated_annealing(_courses()[:2], slots, halls=halls, iterations=200)

    assert schedule.is_complete
    assert all(event.halls for event in schedule.events)


def test_annealing_reports_infeasible_problem() -> None:
    slots = [TimeSlot(day=1, slot_index=1)]

    schedule = optimize_simulated_annealing(_courses()[:2], slots, iterations=10)

    assert schedule.events == []
    assert schedule.unscheduled_courses == ["A", "B"]


def test_annealing_restarts_dsatur_when_first_seed_fails() -> None:
    edges = [
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 6),
        (1, 2),
        (1, 5),
        (2, 5),
        (3, 6),
        (4, 6),
        (5, 6),
    ]
    students = [set() for _ in range(7)]
    for edge_index, (course_a, course_b) in enumerate(edges):
        student = f"edge-{edge_index}"
        students[course_a].add(student)
        students[course_b].add(student)
    courses = [
        Course(code=str(index), students=frozenset(enrollment))
        for index, enrollment in enumerate(students)
    ]
    slots = [TimeSlot(day=index, slot_index=1) for index in range(1, 4)]

    schedule = optimize_simulated_annealing(courses, slots, iterations=10, random_seed=0)

    assert schedule.is_complete


def test_optimizer_callback_and_validation() -> None:
    seen: list[int] = []
    optimizer = SimulatedAnnealingOptimizer(iterations=4, iteration_callback=seen.append)

    optimizer.optimize(_courses(), [TimeSlot(day=1, slot_index=1), TimeSlot(day=2, slot_index=1)])

    assert seen == [1, 2, 3, 4]
    with pytest.raises(ValueError, match="iterations"):
        optimize_simulated_annealing(_courses(), [TimeSlot(day=1, slot_index=1)], iterations=0)
