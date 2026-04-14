from pathlib import Path

import pandas as pd
import pytest

from unisched.domain.models import ExamEvent, Schedule, TimeSlot
from unisched.io import save_schedule_to_csv, schedule_to_dataframe


def test_schedule_to_dataframe_sorts_rows_and_serializes_halls() -> None:
    """Export rows should be sorted by day, slot, and course code with hall text."""

    schedule = Schedule(
        events=[
            ExamEvent(course_code="B", time_slot=TimeSlot(day=1, slot_index=2), halls=("L-2",)),
            ExamEvent(course_code="A", time_slot=TimeSlot(day=1, slot_index=2), halls=()),
            ExamEvent(
                course_code="C",
                time_slot=TimeSlot(day=1, slot_index=1),
                halls=("L-1", "L-3"),
            ),
        ],
        unscheduled_courses=[],
        penalty=0,
    )

    frame = schedule_to_dataframe(schedule)

    assert frame["course_code"].tolist() == ["C", "A", "B"]
    assert frame["halls"].tolist() == ["L-1, L-3", "", "L-2"]


def test_save_schedule_to_csv_writes_expected_rows(tmp_path: Path) -> None:
    """Saving should create a CSV with sorted schedule rows and expected columns."""

    schedule = Schedule(
        events=[
            ExamEvent(course_code="CS101", time_slot=TimeSlot(day=2, slot_index=1), halls=("A",)),
            ExamEvent(course_code="MA101", time_slot=TimeSlot(day=1, slot_index=1), halls=()),
        ],
        unscheduled_courses=["PH101"],
        penalty=4,
    )
    output_path = tmp_path / "schedule.csv"

    written_path = save_schedule_to_csv(schedule, output_path)
    loaded = pd.read_csv(output_path)

    assert written_path == output_path.resolve()
    assert loaded["course_code"].tolist() == ["MA101", "CS101"]
    assert list(loaded.columns) == ["course_code", "day", "slot_index", "halls"]


def test_save_schedule_to_csv_requires_csv_extension(tmp_path: Path) -> None:
    """Non-CSV destinations should fail with a clear validation error."""

    schedule = Schedule(events=[], unscheduled_courses=[], penalty=0)

    with pytest.raises(ValueError, match=".csv"):
        save_schedule_to_csv(schedule, tmp_path / "schedule.txt")
