"""Configuration form for scheduling options."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QFileDialog,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from unisched.io.loader import HallDataConfig, RegDataConfig


@dataclass(frozen=True, slots=True)
class SchedulingOptions:
    """Represent config options collected from UI form controls."""

    registration_file: str | None
    reg_config: RegDataConfig
    hall_capacity_file: str | None
    hall_config: HallDataConfig | None
    max_days: int | None
    slots_per_day: int
    num_tries: int
    random_seed: int
    n: int


class ConfigFormWidget(QWidget):
    """Provide inputs for data column mapping and scheduler options."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        registration_group = QGroupBox("Registration Configuration", self)
        registration_layout = QFormLayout(registration_group)

        self.student_col_input = QLineEdit("student_id")
        self.course_col_input = QLineEdit("course")
        self.sheet_name_input = QLineEdit("")
        self.sheet_name_input.setPlaceholderText("Optional sheet name/index")

        self.registration_file_input = QLineEdit("")
        self.registration_file_input.setReadOnly(True)
        self.registration_file_input.setPlaceholderText("Choose CSV/Excel/ODS file")
        registration_file_row = QWidget(self)
        registration_file_layout = QHBoxLayout(registration_file_row)
        registration_file_layout.setContentsMargins(0, 0, 0, 0)
        registration_file_layout.addWidget(self.registration_file_input)

        browse_registration_button = QPushButton("Browse", self)
        browse_registration_button.clicked.connect(self._browse_registration_file)
        registration_file_layout.addWidget(browse_registration_button)

        registration_layout.addRow("Registration file", registration_file_row)
        registration_layout.addRow("Student ID column", self.student_col_input)
        registration_layout.addRow("Course column", self.course_col_input)
        registration_layout.addRow("Sheet name/index", self.sheet_name_input)

        hall_group = QGroupBox("Exam Hall Configuration", self)
        hall_layout = QFormLayout(hall_group)

        self.hall_file_input = QLineEdit("")
        self.hall_file_input.setReadOnly(True)
        self.hall_file_input.setPlaceholderText("Optional hall-capacity file")
        hall_file_row = QWidget(self)
        hall_file_layout = QHBoxLayout(hall_file_row)
        hall_file_layout.setContentsMargins(0, 0, 0, 0)
        hall_file_layout.addWidget(self.hall_file_input)

        browse_hall_button = QPushButton("Browse", self)
        browse_hall_button.clicked.connect(self._browse_hall_file)
        hall_file_layout.addWidget(browse_hall_button)

        self.hall_col_input = QLineEdit("hall")
        self.hall_capacity_col_input = QLineEdit("capacity")
        self.hall_group_col_input = QLineEdit("group")
        self.hall_sheet_name_input = QLineEdit("")
        self.hall_sheet_name_input.setPlaceholderText("Optional sheet name/index")

        hall_layout.addRow("Hall capacity file", hall_file_row)
        hall_layout.addRow("Hall column", self.hall_col_input)
        hall_layout.addRow("Capacity column", self.hall_capacity_col_input)
        hall_layout.addRow("Group column", self.hall_group_col_input)
        hall_layout.addRow("Sheet name/index", self.hall_sheet_name_input)

        optimizer_group = QGroupBox("Optimizer Configuration", self)
        optimizer_layout = QFormLayout(optimizer_group)

        self.slots_per_day_input = QSpinBox()
        self.slots_per_day_input.setRange(1, 8)
        self.slots_per_day_input.setValue(2)

        self.num_tries_input = QSpinBox()
        self.num_tries_input.setRange(1, 100000)
        self.num_tries_input.setValue(32)

        self.random_seed_input = QSpinBox()
        self.random_seed_input.setRange(-2147483648, 2147483647)
        self.random_seed_input.setValue(0)

        self.n_input = QSpinBox()
        self.n_input.setRange(1, 128)
        self.n_input.setValue(4)

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

        optimizer_layout.addRow("Slots per day", self.slots_per_day_input)
        optimizer_layout.addRow("Day limit", limit_days_wrapper)
        optimizer_layout.addRow("Num tries", self.num_tries_input)
        optimizer_layout.addRow("Random seed", self.random_seed_input)
        optimizer_layout.addRow("Parallel workers", self.n_input)

        layout.addWidget(registration_group)
        layout.addWidget(hall_group)
        layout.addWidget(optimizer_group)
        layout.addStretch(1)

    def _parse_sheet_name(self, sheet_name_raw: str) -> str | int | None:
        if sheet_name_raw == "":
            return None
        if sheet_name_raw.isdigit():
            return int(sheet_name_raw)
        return sheet_name_raw

    def _browse_hall_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select hall capacity file",
            "",
            "Hall files (*.csv *.xlsx *.xls *.ods);;All files (*.*)",
        )
        if path:
            self.hall_file_input.setText(path)

    def _browse_registration_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select registration file",
            "",
            "Registration files (*.csv *.xlsx *.xls *.ods);;All files (*.*)",
        )
        if path:
            self.registration_file_input.setText(path)

    def get_options(self) -> SchedulingOptions:
        """Build scheduling options from current form values."""

        parsed_sheet_name = self._parse_sheet_name(self.sheet_name_input.text().strip())

        reg_config = RegDataConfig(
            student_id_col=self.student_col_input.text().strip(),
            course_col=self.course_col_input.text().strip(),
            sheet_name=parsed_sheet_name,
        )

        hall_file_raw = self.hall_file_input.text().strip()
        parsed_hall_sheet_name = self._parse_sheet_name(self.hall_sheet_name_input.text().strip())
        hall_capacity_file = hall_file_raw if hall_file_raw else None
        hall_config = (
            HallDataConfig(
                hall_col=self.hall_col_input.text().strip(),
                capacity_col=self.hall_capacity_col_input.text().strip(),
                group_col=self.hall_group_col_input.text().strip(),
                sheet_name=parsed_hall_sheet_name,
            )
            if hall_capacity_file
            else None
        )

        max_days = self.max_days_input.value() if self.limit_days_checkbox.isChecked() else None
        registration_file = self.registration_file_input.text().strip() or None

        return SchedulingOptions(
            registration_file=registration_file,
            reg_config=reg_config,
            hall_capacity_file=hall_capacity_file,
            hall_config=hall_config,
            max_days=max_days,
            slots_per_day=self.slots_per_day_input.value(),
            num_tries=self.num_tries_input.value(),
            random_seed=self.random_seed_input.value(),
            n=self.n_input.value(),
        )
