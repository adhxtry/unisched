"""Fast simulated annealing optimizer for feasible exam schedules."""

from __future__ import annotations

import math
import random
from typing import Callable

from unisched.core.hall_allocation import (
    GroupedHalls,
    assign_halls_for_enrollment,
    build_grouped_halls,
    build_slot_hall_inventory,
)
from unisched.domain.constraints import calculate_penalty, compute_student_conflicts
from unisched.domain.models import Course, ExamEvent, ExamHall, Schedule, TimeSlot

from .base import BaseOptimizer
from .graph_coloring import _color_once, build_conflict_graph


def _schedule_from_state(
    courses: list[Course],
    time_slots: list[TimeSlot],
    state: list[int],
    halls: list[ExamHall] | None,
) -> Schedule:
    hall_map: dict[int, tuple[str, ...]] = {}
    if halls is not None:
        grouped = build_grouped_halls(halls)
        inventory = build_slot_hall_inventory(len(time_slots), grouped)
        allocation_order = sorted(
            range(len(courses)),
            key=lambda index: (-len(courses[index].students), courses[index].code),
        )
        for course_index in allocation_order:
            course = courses[course_index]
            assigned = assign_halls_for_enrollment(
                len(course.students), inventory[state[course_index]]
            )
            if assigned is None:
                return Schedule(unscheduled_courses=sorted(item.code for item in courses))
            hall_map[course_index] = tuple(hall.hall for hall in assigned)

    events = [
        ExamEvent(
            course_code=course.code,
            time_slot=time_slots[state[index]],
            halls=hall_map.get(index, tuple()),
        )
        for index, course in enumerate(courses)
    ]
    conflicts = compute_student_conflicts(courses)
    penalty = calculate_penalty({event.course_code: event.time_slot for event in events}, conflicts)
    return Schedule(events=events, penalty=penalty)


def _hall_state_is_feasible(
    state: list[int],
    courses: list[Course],
    slot_a: int,
    slot_b: int,
    moved_course: int,
    new_slot: int,
    grouped: GroupedHalls,
) -> bool:
    """Check only slots touched by a move, avoiding a full schedule rebuild."""
    candidate = state[:]
    candidate[moved_course] = new_slot
    for slot_index in {slot_a, slot_b}:
        inventory = [group[:] for group in grouped]
        allocation_order = sorted(
            (index for index in range(len(courses)) if candidate[index] == slot_index),
            key=lambda index: (-len(courses[index].students), courses[index].code),
        )
        for course_index in allocation_order:
            course = courses[course_index]
            if assign_halls_for_enrollment(len(course.students), inventory) is None:
                return False
    return True


def _run_single_annealing(
    worker_index: int,
    courses: list[Course],
    time_slots: list[TimeSlot],
    graph: ConflictGraph,
    enrollments: dict[str, int],
    grouped: GroupedHalls | None,
    conflicts: list,
    iterations: int,
    initial_temperature: float,
    cooling_rate: float,
    seed_base: int,
    halls: list[ExamHall] | None,
    iteration_callback: Callable[[int], None] | None,
    track_callback: bool,
) -> Schedule:
    slot_days = [ts.day for ts in time_slots]
    seed = None
    for attempt in range(32):
        inventory = (
            build_slot_hall_inventory(len(time_slots), grouped) if grouped is not None else None
        )
        seed = _color_once(
            graph,
            len(time_slots),
            enrollments,
            random.Random(seed_base + worker_index * 1000 + attempt),
            inventory,
            randomize=attempt > 0 or worker_index > 0,
            slot_days=slot_days,
        )
        if seed is not None:
            break

    if seed is None:
        return Schedule(unscheduled_courses=sorted(course.code for course in courses))

    positions = {course.code: index for index, course in enumerate(courses)}
    state = [seed.color_map[course.code] for course in courses]
    current_penalty = calculate_penalty(
        {course.code: time_slots[state[index]] for index, course in enumerate(courses)},
        conflicts,
    )
    best_state = state[:]
    best_penalty = current_penalty
    rng = random.Random(seed_base + worker_index * 1000 + 1)
    temperature = initial_temperature
    neighbors = [
        [(positions[neighbor], weight) for neighbor, weight in graph[course.code].items()]
        for course in courses
    ]

    for iteration in range(iterations):
        if len(time_slots) > 1:
            course_index = rng.randrange(len(courses))
            old_slot = state[course_index]
            new_slot = rng.randrange(len(time_slots) - 1)
            if new_slot >= old_slot:
                new_slot += 1

            if not any(state[neighbor] == new_slot for neighbor, _ in neighbors[course_index]) and (
                grouped is None
                or _hall_state_is_feasible(
                    state, courses, old_slot, new_slot, course_index, new_slot, grouped
                )
            ):
                delta = 0
                old_day = time_slots[old_slot].day
                new_day = time_slots[new_slot].day
                if old_day != new_day:
                    for neighbor, weight in neighbors[course_index]:
                        neighbor_day = time_slots[state[neighbor]].day
                        delta += weight * ((new_day == neighbor_day) - (old_day == neighbor_day))

                if delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-12)):
                    state[course_index] = new_slot
                    current_penalty += delta
                    if current_penalty < best_penalty:
                        best_penalty = current_penalty
                        best_state = state[:]

            temperature = max(temperature * cooling_rate, 1e-12)

        if track_callback and iteration_callback is not None:
            iteration_callback(iteration + 1)

    return _schedule_from_state(courses, time_slots, best_state, halls)


def _run_single_annealing_worker(
    worker_index: int,
    courses: list[Course],
    time_slots: list[TimeSlot],
    graph: ConflictGraph,
    enrollments: dict[str, int],
    grouped: GroupedHalls | None,
    conflicts: dict[str, set[str]],
    iterations: int,
    initial_temperature: float,
    cooling_rate: float,
    seed_base: int,
    halls: list[ExamHall] | None,
) -> Schedule:
    return _run_single_annealing(
        worker_index,
        courses,
        time_slots,
        graph,
        enrollments,
        grouped,
        conflicts,
        iterations,
        initial_temperature,
        cooling_rate,
        seed_base,
        halls,
        None,
        False,
    )


def optimize_simulated_annealing(
    courses: list[Course],
    time_slots: list[TimeSlot],
    *,
    halls: list[ExamHall] | None = None,
    iterations: int = 200_000,
    initial_temperature: float = 10.0,
    cooling_rate: float = 0.9998,
    random_seed: int = 0,
    n: int = 1,
    iteration_callback: Callable[[int], None] | None = None,
) -> Schedule:
    """Improve feasible DSatur schedules using parallel simulated annealing chains."""
    if not time_slots:
        raise ValueError("time_slots must not be empty")
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    if initial_temperature <= 0:
        raise ValueError("initial_temperature must be > 0")
    if not 0 < cooling_rate < 1:
        raise ValueError("cooling_rate must be between 0 and 1")
    if n < 1:
        raise ValueError("n must be >= 1")
    if not courses:
        return Schedule()

    sorted_courses = sorted(courses, key=lambda course: course.code)
    graph = build_conflict_graph(sorted_courses)
    enrollments = {course.code: len(course.students) for course in sorted_courses}
    grouped = build_grouped_halls(halls or []) if halls is not None else None
    conflicts = compute_student_conflicts(sorted_courses)

    if n == 1:
        return _run_single_annealing(
            0,
            sorted_courses,
            time_slots,
            graph,
            enrollments,
            grouped,
            conflicts,
            iterations,
            initial_temperature,
            cooling_rate,
            random_seed,
            halls,
            iteration_callback,
            track_callback=True,
        )

    from concurrent.futures import ProcessPoolExecutor, as_completed

    schedules: list[Schedule] = []
    with ProcessPoolExecutor(max_workers=n) as executor:
        futures = [
            executor.submit(
                _run_single_annealing_worker,
                worker_idx,
                sorted_courses,
                time_slots,
                graph,
                enrollments,
                grouped,
                conflicts,
                iterations,
                initial_temperature,
                cooling_rate,
                random_seed,
                halls,
            )
            for worker_idx in range(n)
        ]

        completed = 0
        for future in as_completed(futures):
            schedules.append(future.result())
            completed += 1
            if iteration_callback is not None:
                iteration_callback(int((completed / n) * iterations))

    best_schedule = min(
        schedules,
        key=lambda s: (len(s.unscheduled_courses), s.penalty),
    )
    return best_schedule


class SimulatedAnnealingOptimizer(BaseOptimizer):
    """Concrete optimizer using incremental simulated annealing."""

    def __init__(
        self,
        iterations: int = 200_000,
        initial_temperature: float = 10.0,
        cooling_rate: float = 0.9998,
        random_seed: int = 0,
        n: int = 1,
        iteration_callback: Callable[[int], None] | None = None,
    ) -> None:
        self.iterations = iterations
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.random_seed = random_seed
        self.n = n
        self.iteration_callback = iteration_callback

    def optimize(
        self,
        courses: list[Course],
        time_slots: list[TimeSlot],
        *,
        halls: list[ExamHall] | None = None,
    ) -> Schedule:
        return optimize_simulated_annealing(
            courses,
            time_slots,
            halls=halls,
            iterations=self.iterations,
            initial_temperature=self.initial_temperature,
            cooling_rate=self.cooling_rate,
            random_seed=self.random_seed,
            n=self.n,
            iteration_callback=self.iteration_callback,
        )
