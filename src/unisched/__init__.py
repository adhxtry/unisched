"""
Top-level package for the `unisched` exam scheduling framework.

Public API direction (planned):
- Expose a stable, headless scheduling facade for library users.
- Keep pandas DataFrame as the boundary format for inputs and outputs.
- Delegate internals to layered packages:
    - `unisched.io`: data loading and normalization.
    - `unisched.core`: orchestration, optimization, and validation workflow.
    - `unisched.domain`: entities, value objects, and constraint rules.

Planned API surface to implement in this package:
- `schedule_exams(data: DataFrame, *, optimizer: str | BaseOptimizer, ...)`
- `validate_schedule(schedule: Schedule, constraints: list[Constraint])`
- `move_course_and_resolve(schedule: Schedule, course_id: str, target: TimeSlot, ...)`
- Result/report models for schedule output and conflict diagnostics.

Notes:
- GUI-facing APIs are intentionally deferred for now.
- This module should remain the single, stable import point for advanced users.
"""

from .api import schedule
from .core import BaseOptimizer, GraphColoringOptimizer, SchedulingCoordinator
from .domain import Course, ExamEvent, Schedule, TimeSlot

__all__ = [
    "BaseOptimizer",
    "Course",
    "ExamEvent",
    "GraphColoringOptimizer",
    "Schedule",
    "SchedulingCoordinator",
    "TimeSlot",
    "schedule",
]
