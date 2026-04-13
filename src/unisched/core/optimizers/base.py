"""Base optimizer contract for scheduling engines."""

from __future__ import annotations

from abc import ABC, abstractmethod

from unisched.domain.models import Course, Schedule, TimeSlot


class BaseOptimizer(ABC):
    """Define a common optimizer interface for scheduling."""

    @abstractmethod
    def optimize(self, courses: list[Course], time_slots: list[TimeSlot]) -> Schedule:
        """Create a schedule for the given courses and available time slots."""
