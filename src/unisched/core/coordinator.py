"""Scheduling coordinator that orchestrates IO and optimizer calls."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from unisched.core.optimizers import BaseOptimizer, GraphColoringOptimizer
from unisched.domain.models import Course, ExamHall, Schedule, TimeSlot
from unisched.io.files import ValidatedFile
from unisched.io.loader import HallDataConfig, RegDataConfig, DataLoader


class SchedulingCoordinator:
    """Coordinate loading, transformation, and optimization."""

    def __init__(
        self,
        optimizer: BaseOptimizer | None = None,
        *,
        slots_per_day: int = 2,
        max_days: int | None = None,
    ) -> None:
        self.optimizer = optimizer or GraphColoringOptimizer()
        self.slots_per_day = slots_per_day
        self.max_days = max_days
        self.loader = DataLoader()

    def _build_courses(self, data: pd.DataFrame, config: RegDataConfig) -> list[Course]:
        courses: list[Course] = []

        grouped = data.groupby(config.course_col)
        for course_code, group in grouped:
            students = frozenset(str(value) for value in group[config.student_id_col])
            courses.append(Course(code=str(course_code), students=students))

        courses.sort(key=lambda course: course.code)
        return courses

    def _build_halls(self, data: pd.DataFrame, config: HallDataConfig) -> list[ExamHall]:
        halls: list[ExamHall] = []

        for _, row in data.iterrows():
            halls.append(
                ExamHall(
                    hall=str(row[config.hall_col]),
                    capacity=int(row[config.capacity_col]),
                    group=int(row[config.group_col]),
                )
            )

        halls.sort(key=lambda hall: (hall.group, hall.capacity, hall.hall))
        return halls

    def _generate_time_slots(self, course_count: int) -> list[TimeSlot]:
        if self.slots_per_day < 1:
            raise ValueError("slots_per_day must be >= 1")

        required_days = math.ceil(max(1, course_count) / self.slots_per_day)

        if self.max_days is None:
            total_days = required_days
        else:
            if self.max_days < 1:
                raise ValueError("max_days must be >= 1")
            total_days = self.max_days

        return [
            TimeSlot(day=day, slot_index=slot_index)
            for day in range(1, total_days + 1)
            for slot_index in range(1, self.slots_per_day + 1)
        ]

    def load_and_schedule(
        self,
        input_file: str | Path | ValidatedFile,
        reg_config: RegDataConfig | None = None,
        *,
        hall_capacity_file: str | Path | ValidatedFile | None = None,
        hall_config: HallDataConfig | None = None,
    ) -> Schedule:
        """Load registration data and return an exam schedule."""

        validated_file = (
            input_file
            if isinstance(input_file, ValidatedFile)
            else ValidatedFile.from_path(input_file)
        )

        active_config = reg_config or RegDataConfig()
        data = self.loader.load_registration_data(validated_file, active_config)
        courses = self._build_courses(data, active_config)
        time_slots = self._generate_time_slots(len(courses))
        halls: list[ExamHall] | None = None

        if hall_capacity_file is not None:
            validated_hall_file = (
                hall_capacity_file
                if isinstance(hall_capacity_file, ValidatedFile)
                else ValidatedFile.from_path(hall_capacity_file)
            )
            active_hall_config = hall_config or HallDataConfig()
            hall_data = self.loader.load_hall_capacity_data(
                validated_hall_file,
                active_hall_config,
            )
            halls = self._build_halls(hall_data, active_hall_config)

        return self.optimizer.optimize(courses, time_slots, halls=halls)
