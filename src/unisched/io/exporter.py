"""Schedule export utilities for the ``unisched.io`` layer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from unisched.domain.models import Schedule
from unisched.io.files import ValidatedFile


def schedule_to_dataframe(schedule: Schedule) -> pd.DataFrame:
    """Convert a schedule into a tabular representation for export."""

    sorted_events = sorted(
        schedule.events,
        key=lambda event: (event.time_slot.day, event.time_slot.slot_index, event.course_code),
    )

    rows = [
        {
            "course_code": event.course_code,
            "day": event.time_slot.day,
            "slot_index": event.time_slot.slot_index,
            "halls": ", ".join(event.halls),
        }
        for event in sorted_events
    ]

    return pd.DataFrame(rows, columns=["course_code", "day", "slot_index", "halls"])


def save_schedule_to_csv(
    schedule: Schedule,
    output_file: str | Path | ValidatedFile,
) -> Path:
    """Persist scheduled events to a CSV file and return the written path."""

    validated_output = (
        output_file
        if isinstance(output_file, ValidatedFile)
        else ValidatedFile.from_path(output_file)
    )

    if validated_output.extension != ".csv":
        raise ValueError("output_file must use a .csv extension")

    schedule_to_dataframe(schedule).to_csv(validated_output.path, index=False)
    return validated_output.path
