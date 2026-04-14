from unisched.core.optimizers.graph_coloring import (
    GraphColoringOptimizer,
    build_conflict_graph,
    optimize_graph_coloring,
)
from unisched.domain.models import Course, ExamHall, TimeSlot


def _sample_courses() -> list[Course]:
    return [
        Course(code="A", students=frozenset({"s1", "s2"})),
        Course(code="B", students=frozenset({"s2", "s3"})),
        Course(code="C", students=frozenset({"s4"})),
    ]


def test_build_conflict_graph_uses_shared_student_weight() -> None:
    graph = build_conflict_graph(_sample_courses())

    assert graph["A"]["B"] == 1
    assert "C" not in graph["A"]


def test_optimize_graph_coloring_avoids_same_slot_for_conflicting_courses() -> None:
    courses = _sample_courses()
    time_slots = [TimeSlot(day=1, slot_index=1), TimeSlot(day=1, slot_index=2)]

    schedule = optimize_graph_coloring(courses, time_slots, num_tries=8, random_seed=7)
    mapping = schedule.assignment_map()

    assert schedule.is_complete is True
    assert mapping["A"] != mapping["B"]


def test_optimize_graph_coloring_marks_unscheduled_when_slots_insufficient() -> None:
    courses = _sample_courses()
    one_slot = [TimeSlot(day=1, slot_index=1)]

    schedule = optimize_graph_coloring(courses, one_slot, num_tries=2)

    assert schedule.events == []
    assert set(schedule.unscheduled_courses) == {"A", "B", "C"}


def test_optimize_graph_coloring_assigns_halls_when_capacity_is_available() -> None:
    courses = _sample_courses()
    time_slots = [TimeSlot(day=1, slot_index=1), TimeSlot(day=1, slot_index=2)]
    halls = [
        ExamHall(hall="L-1", capacity=300, group=1),
        ExamHall(hall="L-2", capacity=100, group=1),
    ]

    schedule = optimize_graph_coloring(
        courses,
        time_slots,
        halls=halls,
        num_tries=8,
        random_seed=7,
    )

    assert schedule.is_complete is True
    assert all(event.halls for event in schedule.events)


def test_optimize_graph_coloring_respects_hard_group_constraint() -> None:
    students = frozenset({f"s{i}" for i in range(30)})
    courses = [Course(code="A", students=students)]
    time_slots = [TimeSlot(day=1, slot_index=1)]
    halls = [
        ExamHall(hall="G1-H1", capacity=20, group=1),
        ExamHall(hall="G2-H1", capacity=20, group=2),
    ]

    schedule = optimize_graph_coloring(courses, time_slots, halls=halls, num_tries=1)

    assert schedule.events == []
    assert schedule.unscheduled_courses == ["A"]


def test_graph_coloring_optimizer_iteration_callback_uses_one_based_index() -> None:
    seen_iterations: list[int] = []

    optimizer = GraphColoringOptimizer(
        num_tries=4,
        random_seed=0,
        iteration_callback=seen_iterations.append,
    )
    courses = _sample_courses()
    time_slots = [TimeSlot(day=1, slot_index=1), TimeSlot(day=1, slot_index=2)]

    optimizer.optimize(courses, time_slots)

    assert seen_iterations == [1, 2, 3, 4]
