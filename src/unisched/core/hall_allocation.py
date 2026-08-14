"""Hall-allocation helpers used by scheduling optimizers."""

from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from typing import Iterable

from unisched.domain.models import ExamHall

GroupedHalls = list[list[ExamHall]]


def build_grouped_halls(halls: Iterable[ExamHall]) -> GroupedHalls:
    """Group halls by group id and sort each group by ascending capacity."""

    grouped: defaultdict[int, list[ExamHall]] = defaultdict(list)
    for hall in halls:
        grouped[hall.group].append(hall)

    ordered_groups: GroupedHalls = []
    for group in sorted(grouped):
        ordered_groups.append(
            sorted(grouped[group], key=lambda current: (current.capacity, current.hall))
        )

    return ordered_groups


def clone_grouped_halls(grouped_halls: GroupedHalls) -> GroupedHalls:
    """Create a shallow clone of grouped hall inventory lists."""

    return [group[:] for group in grouped_halls]


def build_slot_hall_inventory(
    slot_count: int, grouped_halls: GroupedHalls
) -> dict[int, GroupedHalls]:
    """Create independent hall inventories for each slot index."""

    if slot_count < 1:
        raise ValueError("slot_count must be >= 1")

    return {slot_idx: clone_grouped_halls(grouped_halls) for slot_idx in range(slot_count)}


def preview_halls_for_enrollment(
    enrollment: int,
    grouped_halls: GroupedHalls,
) -> tuple[int, list[ExamHall], tuple[ExamHall, ...]] | None:
    """Find the best hall assignment for an enrollment without mutating grouped_halls."""

    if enrollment < 1:
        return (0, [], tuple())

    best_solution: tuple[int, list[ExamHall], tuple[ExamHall, ...]] | None = None
    best_score: tuple[int, int, int] | None = None

    for group_index, halls in enumerate(grouped_halls):
        halls_copy = halls[:]
        total_capacity = 0
        selected_halls: list[ExamHall] = []

        while total_capacity < enrollment and halls_copy:
            remaining = enrollment - total_capacity
            # Pick the smallest hall that meets the remaining capacity; fallback to the largest hall.
            hall_index = bisect_left(halls_copy, remaining, key=lambda hall: hall.capacity)
            if hall_index == len(halls_copy):
                hall_index -= 1

            chosen_hall = halls_copy.pop(hall_index)
            selected_halls.append(chosen_hall)
            total_capacity += chosen_hall.capacity

        if total_capacity < enrollment:
            continue

        score = (total_capacity, len(selected_halls), group_index)
        if best_score is None or score < best_score:
            best_score = score
            best_solution = (
                group_index,
                halls_copy,
                tuple(sorted(selected_halls, key=lambda hall: hall.hall)),
            )

    return best_solution


def assign_halls_for_enrollment(
    enrollment: int,
    grouped_halls: GroupedHalls,
) -> tuple[ExamHall, ...] | None:
    """Assign halls from one group with minimal excess capacity for a course."""

    if enrollment < 1:
        return tuple()

    solution = preview_halls_for_enrollment(enrollment, grouped_halls)
    if solution is None:
        return None

    group_index, remaining_halls, assigned_halls = solution
    grouped_halls[group_index] = remaining_halls
    return assigned_halls

