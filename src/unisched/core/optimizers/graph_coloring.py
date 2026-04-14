"""Graph coloring optimizer based on DSatur ordering."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterator

from unisched.core.hall_allocation import (
    GroupedHalls,
    assign_halls_for_enrollment,
    build_grouped_halls,
    build_slot_hall_inventory,
)
from unisched.domain.constraints import calculate_penalty, compute_student_conflicts
from unisched.domain.models import Course, ExamEvent, ExamHall, Schedule, TimeSlot

from .base import BaseOptimizer

ConflictGraph = dict[str, dict[str, int]]


@dataclass(frozen=True, slots=True)
class ColoringResult:
    """Internal coloring result with per-course color indices."""

    color_map: dict[str, int]
    hall_map: dict[str, tuple[str, ...]]


def build_conflict_graph(courses: list[Course]) -> ConflictGraph:
    """Build adjacency map where edge weight is shared student count."""

    graph: ConflictGraph = {course.code: {} for course in courses}

    for conflict in compute_student_conflicts(courses):
        graph[conflict.course_a][conflict.course_b] = conflict.shared_students
        graph[conflict.course_b][conflict.course_a] = conflict.shared_students

    return graph


def _dsatur_order(
    graph: ConflictGraph,
    color_map: dict[str, int],
    enrollments: dict[str, int],
) -> Iterator[str]:
    """
    Generator function for DSatur ordering of nodes.
    DSatur chooses the nodes with the highest saturation degree, i.e.,
    the most number of differently colored neighbors.
    """
    uncolored = set(graph)

    while uncolored:

        # Define a scoring function with tie-breaking for saturation degree, degree, and enrollment size
        def score(course_code: str) -> tuple[int, int, int, str]:
            neighbor_colors = {
                color_map[neighbor] for neighbor in graph[course_code] if neighbor in color_map
            }
            return (
                len(neighbor_colors),
                len(graph[course_code]),
                enrollments[course_code],
                course_code,
            )

        chosen = max(uncolored, key=score)
        uncolored.remove(chosen)
        yield chosen


def _color_once(
    graph: ConflictGraph,
    slot_count: int,
    enrollments: dict[str, int],
    rng: random.Random,
    hall_inventory_by_slot: dict[int, GroupedHalls] | None,
    *,
    randomize: bool,
) -> ColoringResult | None:
    """
    Perform a single graph coloring attempt.
    """
    # Start with an empty map
    color_map: dict[str, int] = {}
    hall_map: dict[str, tuple[str, ...]] = {}

    for course_code in _dsatur_order(graph, color_map, enrollments):
        # Determine which colors are blocked by neighbors
        blocked = {color_map[nbr] for nbr in graph[course_code] if nbr in color_map}
        # Find the available color indices
        available = [idx for idx in range(slot_count) if idx not in blocked]

        if not available:
            return None

        if randomize and len(available) > 1:
            rng.shuffle(available)

        assigned = False
        for slot_index in available:
            if hall_inventory_by_slot is None:
                color_map[course_code] = slot_index
                hall_map[course_code] = tuple()
                assigned = True
                break

            assigned_halls = assign_halls_for_enrollment(
                enrollments[course_code],
                hall_inventory_by_slot[slot_index],
            )
            if assigned_halls is None:
                continue

            color_map[course_code] = slot_index
            hall_map[course_code] = tuple(hall.hall for hall in assigned_halls)
            assigned = True
            break

        if not assigned:
            return None

    return ColoringResult(color_map=color_map, hall_map=hall_map)


def _build_schedule(
    courses: list[Course],
    time_slots: list[TimeSlot],
    color_map: dict[str, int],
    hall_map: dict[str, tuple[str, ...]] | None = None,
) -> Schedule:
    active_hall_map = hall_map or {}

    # Build the exam events based on the coloring result
    events = [
        ExamEvent(
            course_code=course.code,
            time_slot=time_slots[color_map[course.code]],
            halls=active_hall_map.get(course.code, tuple()),
        )
        for course in sorted(courses, key=lambda current: current.code)
        if course.code in color_map
    ]

    # Determine which courses were not scheduled
    scheduled = {event.course_code for event in events}
    unscheduled = sorted(course.code for course in courses if course.code not in scheduled)

    conflicts = compute_student_conflicts(courses)
    penalty = calculate_penalty(
        {event.course_code: event.time_slot for event in events},
        conflicts,
    )

    return Schedule(events=events, unscheduled_courses=unscheduled, penalty=penalty)


def optimize_graph_coloring(
    courses: list[Course],
    time_slots: list[TimeSlot],
    *,
    halls: list[ExamHall] | None = None,
    num_tries: int = 32,
    random_seed: int = 0,
) -> Schedule:
    """Run repeated DSatur coloring and keep the best schedule found."""

    if not time_slots:
        raise ValueError("time_slots must not be empty")
    if num_tries < 1:
        raise ValueError("num_tries must be >= 1")

    if not courses:
        return Schedule()

    # Build the conflict graph and enrollment map once since they are reused across attempts
    graph = build_conflict_graph(courses)
    enrollments = {course.code: len(course.students) for course in courses}
    grouped_halls_template = build_grouped_halls(halls or []) if halls is not None else None

    best_schedule: Schedule | None = None
    best_used_slots = float("inf")

    # Run multiple attempts with different random seeds to find a better coloring
    for attempt in range(num_tries):
        rng = random.Random(random_seed + attempt)
        hall_inventory_by_slot = (
            build_slot_hall_inventory(len(time_slots), grouped_halls_template)
            if grouped_halls_template is not None
            else None
        )
        coloring = _color_once(
            graph,
            len(time_slots),
            enrollments,
            rng,
            hall_inventory_by_slot,
            randomize=attempt > 0,  # Only randomize after the first attempt
        )
        if coloring is None:
            continue

        # Build the schedule from the coloring result and evaluate its penalty
        schedule = _build_schedule(
            courses,
            time_slots,
            coloring.color_map,
            coloring.hall_map,
        )
        used_slots = len({event.time_slot for event in schedule.events})

        if best_schedule is None or (schedule.penalty, used_slots) < (
            best_schedule.penalty,
            best_used_slots,
        ):
            best_schedule = schedule
            best_used_slots = used_slots

    if best_schedule is not None:
        return best_schedule

    return Schedule(events=[], unscheduled_courses=sorted(c.code for c in courses), penalty=0)


class GraphColoringOptimizer(BaseOptimizer):
    """Concrete optimizer that schedules courses using graph coloring."""

    def __init__(self, num_tries: int = 32, random_seed: int = 0) -> None:
        self.num_tries = num_tries
        self.random_seed = random_seed

    def optimize(
        self,
        courses: list[Course],
        time_slots: list[TimeSlot],
        *,
        halls: list[ExamHall] | None = None,
    ) -> Schedule:
        return optimize_graph_coloring(
            courses,
            time_slots,
            halls=halls,
            num_tries=self.num_tries,
            random_seed=self.random_seed,
        )
