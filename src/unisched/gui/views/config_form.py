"""Configuration form for scheduling options."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from unisched.io.loader import RegDataConfig


@dataclass(frozen=True, slots=True)
class SchedulingOptions:
    """Represent config options collected from UI form controls."""

    config: RegDataConfig
    max_days: int | None
    slots_per_day: int


class ConfigFormWidget(QGroupBox):
    """Provide inputs for data column mapping and scheduler options."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Scheduler Configuration", parent)

        layout = QFormLayout(self)

        self.student_col_input = QLineEdit("student_id")
        self.course_col_input = QLineEdit("course")
        self.sheet_name_input = QLineEdit("")
        self.sheet_name_input.setPlaceholderText("Optional sheet name/index")

        self.slots_per_day_input = QSpinBox()
        self.slots_per_day_input.setRange(1, 8)
        self.slots_per_day_input.setValue(2)

        self.limit_days_checkbox = QCheckBox("Use max days limit")
        self.max_days_input = QSpinBox()
        self.max_days_input.setRange(1, 365)
        self.max_days_input.setValue(14)
        self.max_days_input.setEnabled(False)
        self.limit_days_checkbox.toggled.connect(self.max_days_input.setEnabled)

        limit_days_wrapper = QWidget()
        limit_days_layout = QHBoxLayout(limit_days_wrapper)
        limit_days_layout.setContentsMargins(0, 0, 0, 0)
        limit_days_layout.addWidget(self.limit_days_checkbox)
        limit_days_layout.addWidget(self.max_days_input)

        layout.addRow("Student ID column", self.student_col_input)
        layout.addRow("Course column", self.course_col_input)
        layout.addRow("Sheet name/index", self.sheet_name_input)
        layout.addRow("Slots per day", self.slots_per_day_input)
        layout.addRow("Day limit", limit_days_wrapper)

    def get_options(self) -> SchedulingOptions:
        """Build scheduling options from current form values."""

        sheet_name_raw = self.sheet_name_input.text().strip()
        parsed_sheet_name: str | int | None
        if sheet_name_raw == "":
            parsed_sheet_name = None
        elif sheet_name_raw.isdigit():
            parsed_sheet_name = int(sheet_name_raw)
        else:
            parsed_sheet_name = sheet_name_raw

        config = RegDataConfig(
            student_id_col=self.student_col_input.text().strip(),
            course_col=self.course_col_input.text().strip(),
            sheet_name=parsed_sheet_name,
        )

        max_days = self.max_days_input.value() if self.limit_days_checkbox.isChecked() else None

        return SchedulingOptions(
            config=config,
            max_days=max_days,
            slots_per_day=self.slots_per_day_input.value(),
        )
