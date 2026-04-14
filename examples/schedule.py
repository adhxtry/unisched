"""
This file will use the `unisched` library to schedule the
anonymized registration data in `data/anonymous-registration-data.csv`
"""

from __future__ import annotations

from pathlib import Path

import tqdm

from unisched import schedule
from unisched.io import HallDataConfig, RegDataConfig
from unisched.core import SchedulingCoordinator, GraphColoringOptimizer


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_file = base_dir / "data" / "anonymous-registration-data.csv"
    hall_file = base_dir / "data" / "hall_cap.csv"

    MAX_TRIES = 1000

    progress_bar = tqdm.tqdm(total=MAX_TRIES, desc="Optimizing")

    coordinator = SchedulingCoordinator(
        optimizer=GraphColoringOptimizer(
            num_tries=MAX_TRIES,
            random_seed=42,
            iteration_callback=lambda i: progress_bar.update(1),
        ),
        slots_per_day=2,
        max_days=8,
    )

    result = schedule(
        input_file,
        reg_config=RegDataConfig(student_id_col="Name", course_col="Course Title"),
        hall_capacity_file=hall_file,
        hall_config=HallDataConfig(
            hall_col="Hall Name", capacity_col="Half Capacity", group_col="Group"
        ),
        coordinator=coordinator,
    )

    progress_bar.close()

    print(f"Total exams: {len(result.events)}")
    print(f"Unscheduled courses: {len(result.unscheduled_courses)}")
    print(f"Penalty: {result.penalty}")
    print("First 10 assignments:")

    for event in result.events[:10]:
        halls = ", ".join(event.halls) if event.halls else "<none>"
        print(
            f"  {event.course_code}: day {event.time_slot.day}, "
            f"slot {event.time_slot.slot_index}, halls {halls}"
        )


if __name__ == "__main__":
    main()
