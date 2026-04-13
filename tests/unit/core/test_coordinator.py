from pathlib import Path

import pandas as pd
import pytest

from unisched.core.coordinator import SchedulingCoordinator
from unisched.io.loader import RegDataConfig


def test_coordinator_load_and_schedule_csv(tmp_path: Path) -> None:
    input_path = tmp_path / "registration.csv"
    pd.DataFrame(
        {
            "student_id": [1, 1, 2, 3],
            "course": ["A", "B", "A", "C"],
        }
    ).to_csv(input_path, index=False)

    coordinator = SchedulingCoordinator()
    schedule = coordinator.load_and_schedule(input_path)

    assert len(schedule.events) == 3
    assert schedule.is_complete is True


def test_coordinator_supports_custom_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "registration.csv"
    pd.DataFrame(
        {
            "sid": [101, 101, 102],
            "unit": ["M1", "M2", "M1"],
        }
    ).to_csv(input_path, index=False)

    coordinator = SchedulingCoordinator()
    schedule = coordinator.load_and_schedule(
        input_path,
        RegDataConfig(student_id_col="sid", course_col="unit"),
    )

    assert len(schedule.events) == 2
    assert schedule.is_complete is True


def test_coordinator_respects_max_days_limit(tmp_path: Path) -> None:
    input_path = tmp_path / "registration.csv"
    pd.DataFrame(
        {
            "student_id": [1, 1, 2],
            "course": ["A", "B", "A"],
        }
    ).to_csv(input_path, index=False)

    coordinator = SchedulingCoordinator(slots_per_day=1, max_days=1)
    schedule = coordinator.load_and_schedule(input_path)

    # With one slot total, conflicting A/B courses cannot both be scheduled.
    assert schedule.is_complete is False
    assert len(schedule.unscheduled_courses) == 2


def test_coordinator_rejects_invalid_max_days() -> None:
    coordinator = SchedulingCoordinator(max_days=0)

    with pytest.raises(ValueError, match="max_days"):
        coordinator._generate_time_slots(3)
