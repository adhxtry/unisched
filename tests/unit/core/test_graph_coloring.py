from unisched.core.optimizers.graph_coloring import (
    build_conflict_graph,
    optimize_graph_coloring,
)
from unisched.domain.models import Course, TimeSlot


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
