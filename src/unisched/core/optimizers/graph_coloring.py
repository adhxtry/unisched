"""Graph coloring optimizer based on DSatur ordering."""

from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterator

from unisched.core.hall_allocation import (
    GroupedHalls,
    assign_halls_for_enrollment,
    build_grouped_halls,
    build_slot_hall_inventory,
    preview_halls_for_enrollment,
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
    student_to_courses: dict[str, list[str]] = {}

    for course in courses:
        for student in course.students:
            student_to_courses.setdefault(student, []).append(course.code)

    for enrolled in student_to_courses.values():
        if len(enrolled) < 2:
            continue
        for i in range(len(enrolled)):
            c1 = enrolled[i]
            for j in range(i + 1, len(enrolled)):
                c2 = enrolled[j]
                if c1 == c2:
                    continue
                graph[c1][c2] = graph[c1].get(c2, 0) + 1
                graph[c2][c1] = graph[c2].get(c1, 0) + 1

    return graph


def _dsatur_order(
    graph: ConflictGraph,
    color_map: dict[str, int],
    enrollments: dict[str, int],
) -> Iterator[str]:
    """
    Generator function for DSatur ordering of nodes.
    Maintains saturation degrees incrementally for high performance.
    """
    adj_colors: dict[str, set[int]] = {
        node: {color_map[nbr] for nbr in graph[node] if nbr in color_map}
        for node in graph
    }
    degrees: dict[str, int] = {node: len(graph[node]) for node in graph}
    uncolored = set(graph) - set(color_map)

    while uncolored:
        chosen = max(
            uncolored,
            key=lambda c: (len(adj_colors[c]), degrees[c], enrollments.get(c, 0), c),
        )
        uncolored.remove(chosen)
        yield chosen


def _try_kempe_recolor(
    course_code: str,
    target_slot: int,
    graph: ConflictGraph,
    slot_count: int,
    color_map: dict[str, int],
    hall_map: dict[str, tuple[str, ...]],
    adj_colors: dict[str, set[int]],
    enrollments: dict[str, int],
    hall_inventory_by_slot: dict[int, GroupedHalls] | None,
    slot_days: list[int] | None,
) -> tuple[dict[str, int], dict[str, tuple[str, ...]]] | None:
    """
    Attempt to free up target_slot for course_code by recoloring conflicting neighbor(s).
    """
    conflicts = [nbr for nbr in graph[course_code] if color_map.get(nbr) == target_slot]
    if len(conflicts) != 1:
        return None

    conflicting_nbr = conflicts[0]

    # Find alternative slots for conflicting_nbr
    nbr_blocked = {
        color_map[nbr_nbr]
        for nbr_nbr in graph[conflicting_nbr]
        if nbr_nbr in color_map and nbr_nbr != course_code
    }
    alt_slots = [
        slot
        for slot in range(slot_count)
        if slot != target_slot and slot not in nbr_blocked
    ]

    if not alt_slots:
        return None

    def alt_score(slot: int) -> int:
        if slot_days is None:
            return 0
        day = slot_days[slot]
        return sum(
            weight
            for nbr_nbr, weight in graph[conflicting_nbr].items()
            if nbr_nbr in color_map and nbr_nbr != course_code and slot_days[color_map[nbr_nbr]] == day
        )

    alt_slots.sort(key=alt_score)

    for alt_slot in alt_slots:
        if hall_inventory_by_slot is None:
            new_color_map = dict(color_map)
            new_color_map[conflicting_nbr] = alt_slot
            new_color_map[course_code] = target_slot
            return new_color_map, dict(hall_map)

        slot_target_inv = [g[:] for g in hall_inventory_by_slot[target_slot]]
        slot_alt_inv = [g[:] for g in hall_inventory_by_slot[alt_slot]]

        target_courses = [
            c for c, s in color_map.items() if s == target_slot and c != conflicting_nbr
        ] + [course_code]
        target_courses.sort(key=lambda c: (-enrollments.get(c, 0), c))

        target_assigned: dict[str, tuple[str, ...]] = {}
        target_feasible = True
        for c in target_courses:
            halls = assign_halls_for_enrollment(enrollments.get(c, 0), slot_target_inv)
            if halls is None:
                target_feasible = False
                break
            target_assigned[c] = tuple(h.hall for h in halls)

        if not target_feasible:
            continue

        alt_courses = [c for c, s in color_map.items() if s == alt_slot] + [conflicting_nbr]
        alt_courses.sort(key=lambda c: (-enrollments.get(c, 0), c))

        alt_assigned: dict[str, tuple[str, ...]] = {}
        alt_feasible = True
        for c in alt_courses:
            halls = assign_halls_for_enrollment(enrollments.get(c, 0), slot_alt_inv)
            if halls is None:
                alt_feasible = False
                break
            alt_assigned[c] = tuple(h.hall for h in halls)

        if not alt_feasible:
            continue

        hall_inventory_by_slot[target_slot] = slot_target_inv
        hall_inventory_by_slot[alt_slot] = slot_alt_inv

        new_color_map = dict(color_map)
        new_color_map[conflicting_nbr] = alt_slot
        new_color_map[course_code] = target_slot

        new_hall_map = dict(hall_map)
        new_hall_map.update(target_assigned)
        new_hall_map.update(alt_assigned)
        return new_color_map, new_hall_map

    return None


def _color_once(
    graph: ConflictGraph,
    slot_count: int,
    enrollments: dict[str, int],
    rng: random.Random,
    hall_inventory_by_slot: dict[int, GroupedHalls] | None,
    *,
    randomize: bool,
    slot_days: list[int] | None = None,
    enable_repair: bool = True,
) -> ColoringResult | None:
    """
    Perform a single graph coloring attempt with dynamic DSatur and objective-aware selection.
    """
    color_map: dict[str, int] = {}
    hall_map: dict[str, tuple[str, ...]] = {}

    adj_colors: dict[str, set[int]] = {node: set() for node in graph}
    degrees: dict[str, int] = {node: len(graph[node]) for node in graph}
    uncolored = set(graph)

    while uncolored:
        if not randomize:
            chosen = max(
                uncolored,
                key=lambda c: (len(adj_colors[c]), degrees[c], enrollments.get(c, 0), c),
            )
        else:
            max_sat = max(len(adj_colors[c]) for c in uncolored)
            candidates = [c for c in uncolored if len(adj_colors[c]) >= max_sat - 1]
            candidates.sort(
                key=lambda c: (len(adj_colors[c]), degrees[c], enrollments.get(c, 0)),
                reverse=True,
            )
            top_k = candidates[: min(4, len(candidates))]
            chosen = rng.choice(top_k)

        uncolored.remove(chosen)

        blocked = adj_colors[chosen]
        available = [slot for slot in range(slot_count) if slot not in blocked]

        assigned_slot: int | None = None
        assigned_halls_tuple: tuple[str, ...] = tuple()

        if available:
            feasible_candidates: list[tuple[int, tuple[int, int, int], tuple[str, ...]]] = []

            for slot_index in available:
                if hall_inventory_by_slot is not None:
                    preview = preview_halls_for_enrollment(
                        enrollments.get(chosen, 0),
                        hall_inventory_by_slot[slot_index],
                    )
                    if preview is None:
                        continue
                    halls_tuple = tuple(hall.hall for hall in preview[2])
                else:
                    halls_tuple = tuple()

                penalty_delta = 0
                if slot_days is not None:
                    target_day = slot_days[slot_index]
                    penalty_delta = sum(
                        weight
                        for nbr, weight in graph[chosen].items()
                        if nbr in color_map and slot_days[color_map[nbr]] == target_day
                    )

                impact = sum(
                    1
                    for nbr in graph[chosen]
                    if nbr in uncolored and slot_index not in adj_colors[nbr]
                )

                score = (penalty_delta, impact, slot_index)
                feasible_candidates.append((slot_index, score, halls_tuple))

            if feasible_candidates:
                if not randomize or len(feasible_candidates) == 1:
                    feasible_candidates.sort(key=lambda item: item[1])
                    assigned_slot, _, assigned_halls_tuple = feasible_candidates[0]
                else:
                    min_penalty = min(item[1][0] for item in feasible_candidates)
                    best_pool = [
                        item for item in feasible_candidates if item[1][0] == min_penalty
                    ]
                    best_pool.sort(key=lambda item: item[1][1])
                    top_pool = best_pool[: min(3, len(best_pool))]
                    assigned_slot, _, assigned_halls_tuple = rng.choice(top_pool)

                if hall_inventory_by_slot is not None:
                    assign_halls_for_enrollment(
                        enrollments.get(chosen, 0),
                        hall_inventory_by_slot[assigned_slot],
                    )

        if assigned_slot is None:
            if enable_repair:
                candidate_target_slots = list(range(slot_count))
                if randomize:
                    rng.shuffle(candidate_target_slots)

                repair_success = False
                for target_slot in candidate_target_slots:
                    recolor_res = _try_kempe_recolor(
                        chosen,
                        target_slot,
                        graph,
                        slot_count,
                        color_map,
                        hall_map,
                        adj_colors,
                        enrollments,
                        hall_inventory_by_slot,
                        slot_days,
                    )
                    if recolor_res is not None:
                        color_map, hall_map = recolor_res
                        for node in graph:
                            adj_colors[node] = {
                                color_map[nbr] for nbr in graph[node] if nbr in color_map
                            }
                        repair_success = True
                        break

                if not repair_success:
                    return None
            else:
                return None
        else:
            color_map[chosen] = assigned_slot
            hall_map[chosen] = assigned_halls_tuple

            for nbr in graph[chosen]:
                adj_colors[nbr].add(assigned_slot)

    return ColoringResult(color_map=color_map, hall_map=hall_map)


def _build_schedule(
    courses: list[Course],
    time_slots: list[TimeSlot],
    color_map: dict[str, int],
    hall_map: dict[str, tuple[str, ...]] | None = None,
    precomputed_conflicts: list | None = None,
) -> Schedule:
    active_hall_map = hall_map or {}

    events = [
        ExamEvent(
            course_code=course.code,
            time_slot=time_slots[color_map[course.code]],
            halls=active_hall_map.get(course.code, tuple()),
        )
        for course in sorted(courses, key=lambda current: current.code)
        if course.code in color_map
    ]

    scheduled = {event.course_code for event in events}
    unscheduled = sorted(course.code for course in courses if course.code not in scheduled)

    conflicts = (
        precomputed_conflicts
        if precomputed_conflicts is not None
        else compute_student_conflicts(courses)
    )
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
    n: int = 1,
    iteration_callback: Callable[[int], None] | None = None,
) -> Schedule:
    """Run repeated DSatur coloring and keep the best schedule found."""

    if not time_slots:
        raise ValueError("time_slots must not be empty")
    if num_tries < 1:
        raise ValueError("num_tries must be >= 1")
    if n < 1:
        raise ValueError("n must be >= 1")

    if not courses:
        return Schedule()

    graph = build_conflict_graph(courses)
    enrollments = {course.code: len(course.students) for course in courses}
    grouped_halls_template = build_grouped_halls(halls or []) if halls is not None else None
    conflicts = compute_student_conflicts(courses)
    slot_days = [ts.day for ts in time_slots]

    best_schedule: Schedule | None = None
    best_score: tuple[int, int, int] | None = None

    def run_attempt(attempt: int) -> tuple[int, ColoringResult | None]:
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
            randomize=attempt > 0,
            slot_days=slot_days,
            enable_repair=True,
        )
        return attempt, coloring

    with ThreadPoolExecutor(max_workers=min(n, num_tries)) as executor:
        future_to_attempt = {
            executor.submit(run_attempt, attempt): attempt for attempt in range(num_tries)
        }

        for future in as_completed(future_to_attempt):
            attempt, coloring = future.result()

            if iteration_callback is not None:
                iteration_callback(attempt + 1)

            if coloring is None:
                continue

            schedule = _build_schedule(
                courses,
                time_slots,
                coloring.color_map,
                coloring.hall_map,
                precomputed_conflicts=conflicts,
            )
            used_slots = len({event.time_slot for event in schedule.events})
            score = (len(schedule.unscheduled_courses), schedule.penalty, used_slots)

            if best_score is None or score < best_score:
                best_score = score
                best_schedule = schedule

    if best_schedule is not None and best_schedule.is_complete:
        return best_schedule

    return Schedule(events=[], unscheduled_courses=sorted(c.code for c in courses), penalty=0)


class GraphColoringOptimizer(BaseOptimizer):
    """Concrete optimizer that schedules courses using graph coloring."""

    def __init__(
        self,
        num_tries: int = 32,
        random_seed: int = 0,
        n: int = 4,
        iteration_callback: Callable[[int], None] | None = None,
    ) -> None:
        self.num_tries = num_tries
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
        return optimize_graph_coloring(
            courses,
            time_slots,
            halls=halls,
            num_tries=self.num_tries,
            random_seed=self.random_seed,
            n=self.n,
            iteration_callback=self.iteration_callback,
        )

