"""
This file will use the `unisched` library to schedule the
anonymized registration data in `data/anonymous-registration-data.csv`
"""

from __future__ import annotations

from pathlib import Path

from unisched import schedule
from unisched.io.loader import RegDataConfig


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_file = base_dir / "data" / "anonymous-registration-data.csv"

    result = schedule(
        input_file,
        config=RegDataConfig(student_id_col="Name", course_col="Course Number"),
        max_days=8,
    )

    print(f"Total exams: {len(result.events)}")
    print(f"Unscheduled courses: {len(result.unscheduled_courses)}")
    print(f"Penalty: {result.penalty}")
    print("First 10 assignments:")

    for event in result.events[:10]:
        print(
            f"  {event.course_code}: day {event.time_slot.day}, "
            f"slot {event.time_slot.slot_index}"
        )


if __name__ == "__main__":
    main()
