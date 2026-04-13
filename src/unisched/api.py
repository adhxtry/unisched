"""Public headless API for exam scheduling."""

from __future__ import annotations

from pathlib import Path

from unisched.core.coordinator import SchedulingCoordinator
from unisched.domain.models import Schedule
from unisched.io.files import ValidatedFile
from unisched.io.loader import RegDataConfig


def schedule(
    input_file: str | Path | ValidatedFile,
    config: RegDataConfig | None = None,
    *,
    max_days: int | None = None,
    slots_per_day: int = 2,
    coordinator: SchedulingCoordinator | None = None,
) -> Schedule:
    """Create an exam schedule from a registration file."""

    active_coordinator = coordinator or SchedulingCoordinator(
        max_days=max_days,
        slots_per_day=slots_per_day,
    )
    return active_coordinator.load_and_schedule(input_file=input_file, config=config)
