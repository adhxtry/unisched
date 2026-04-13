from __future__ import annotations

import sys

from unisched import schedule
from unisched.io.loader import RegDataConfig


def main():
    if len(sys.argv) < 2:
        print("Usage: unisched <registration-file>")
        return 0

    result = schedule(
        sys.argv[1],
        config=RegDataConfig(student_id_col="Name", course_col="Course Number"),
    )
    print(f"Scheduled exams: {len(result.events)}")
    print(f"Unscheduled courses: {len(result.unscheduled_courses)}")
    print(f"Penalty: {result.penalty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
