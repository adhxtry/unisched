"""Public headless API for exam scheduling."""

from __future__ import annotations

from pathlib import Path

from unisched.core.coordinator import SchedulingCoordinator
from unisched.domain.models import Schedule
from unisched.io.files import ValidatedFile
from unisched.io.loader import HallDataConfig, RegDataConfig


def schedule(
    input_file: str | Path | ValidatedFile,
    reg_config: RegDataConfig | None = None,
    *,
    hall_capacity_file: str | Path | ValidatedFile | None = None,
    hall_config: HallDataConfig | None = None,
    max_days: int | None = None,
    slots_per_day: int = 2,
    coordinator: SchedulingCoordinator | None = None,
) -> Schedule:
    """Create an exam schedule from a registration file.

    Args:
        input_file: Path to the registration data file (CSV, Excel, or ODS).
        reg_config: Optional configuration for loading registration data.
        hall_capacity_file: Optional path to exam hall capacity file (CSV, Excel, or ODS).
        hall_config: Optional configuration for loading hall capacity data.
        max_days: Optional maximum number of days to schedule exams over. (default: course_count // slots_per_day + 1)
        slots_per_day: Number of exam slots available per day (default: 2).
        coordinator: Optional custom SchedulingCoordinator instance.
    """

    active_coordinator = coordinator or SchedulingCoordinator(
        max_days=max_days,
        slots_per_day=slots_per_day,
    )
    return active_coordinator.load_and_schedule(
        input_file=input_file,
        reg_config=reg_config,
        hall_capacity_file=hall_capacity_file,
        hall_config=hall_config,
    )
