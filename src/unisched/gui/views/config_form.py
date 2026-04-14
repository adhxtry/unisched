"""Configuration form for scheduling options."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
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

from unisched.io.files import ValidatedFile
from unisched.io.loader import HallDataConfig, RegDataConfig
from unisched.io.loader import DataLoader


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
        self._loader = DataLoader()
        self._registration_sheet_columns: dict[str, list[str]] = {}
        self._hall_sheet_columns: dict[str, list[str]] = {}

        layout = QVBoxLayout(self)

        registration_group = QGroupBox("Registration Configuration", self)
        registration_layout = QFormLayout(registration_group)

        self.student_col_combo = QComboBox(self)
        self.course_col_combo = QComboBox(self)
        self.sheet_name_combo = QComboBox(self)
        self.student_col_combo.setEnabled(False)
        self.course_col_combo.setEnabled(False)
        self.sheet_name_combo.setEnabled(False)

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
        registration_layout.addRow("Sheet", self.sheet_name_combo)
        registration_layout.addRow("Student ID column", self.student_col_combo)
        registration_layout.addRow("Course column", self.course_col_combo)

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

        self.hall_col_combo = QComboBox(self)
        self.hall_capacity_col_combo = QComboBox(self)
        self.hall_group_col_combo = QComboBox(self)
        self.hall_sheet_name_combo = QComboBox(self)
        self.hall_col_combo.setEnabled(False)
        self.hall_capacity_col_combo.setEnabled(False)
        self.hall_group_col_combo.setEnabled(False)
        self.hall_sheet_name_combo.setEnabled(False)

        hall_layout.addRow("Hall capacity file", hall_file_row)
        hall_layout.addRow("Sheet", self.hall_sheet_name_combo)
        hall_layout.addRow("Hall column", self.hall_col_combo)
        hall_layout.addRow("Capacity column", self.hall_capacity_col_combo)
        hall_layout.addRow("Group column", self.hall_group_col_combo)

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

        self.sheet_name_combo.currentIndexChanged.connect(self._refresh_registration_column_combos)
        self.hall_sheet_name_combo.currentIndexChanged.connect(self._refresh_hall_column_combos)

    def _browse_hall_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select hall capacity file",
            "",
            "Hall files (*.csv *.xlsx *.xls *.ods);;All files (*.*)",
        )
        if path:
            self.hall_file_input.setText(path)
            self._preload_hall_file(path)

    def _browse_registration_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select registration file",
            "",
            "Registration files (*.csv *.xlsx *.xls *.ods);;All files (*.*)",
        )
        if path:
            self.registration_file_input.setText(path)
            self._preload_registration_file(path)

    def _reset_combo(self, combo: QComboBox) -> None:
        combo.clear()
        combo.setEnabled(False)

    def _set_combo_items(self, combo: QComboBox, items: list[str], preferred: str | None) -> None:
        combo.clear()
        combo.addItems(items)
        combo.setEnabled(bool(items))
        if preferred and preferred in items:
            combo.setCurrentText(preferred)

    def _preferred_column(self, columns: list[str], options: tuple[str, ...]) -> str | None:
        lowered = {column.lower(): column for column in columns}
        for option in options:
            if option.lower() in lowered:
                return lowered[option.lower()]
        return None

    def _selected_sheet_name(self, combo: QComboBox) -> str | None:
        sheet_name = combo.currentText().strip()
        if not sheet_name or sheet_name == "CSV":
            return None
        return sheet_name

    def _columns_for_selected_sheet(
        self,
        sheet_map: dict[str, list[str]],
        sheet_combo: QComboBox,
    ) -> list[str]:
        if not sheet_map:
            return []

        selected_sheet = sheet_combo.currentText().strip()
        if not selected_sheet:
            return []

        return sheet_map.get(selected_sheet, [])

    def _preload_registration_file(self, file_path: str) -> None:
        try:
            validated_file = ValidatedFile.from_path(file_path)
            self._registration_sheet_columns = self._loader.preload_sheet_columns_map(
                validated_file
            )
            self._set_combo_items(
                self.sheet_name_combo,
                list(self._registration_sheet_columns.keys()),
                preferred=self.sheet_name_combo.currentText() or None,
            )
            self._refresh_registration_column_combos()
        except Exception as exc:  # noqa: BLE001 - show preload failures in form
            self._registration_sheet_columns = {}
            self._reset_combo(self.sheet_name_combo)
            self._reset_combo(self.student_col_combo)
            self._reset_combo(self.course_col_combo)
            self.sheet_name_combo.addItem("Error")
            self.sheet_name_combo.setToolTip(str(exc))

    def _preload_hall_file(self, file_path: str) -> None:
        try:
            validated_file = ValidatedFile.from_path(file_path)
            self._hall_sheet_columns = self._loader.preload_sheet_columns_map(validated_file)
            self._set_combo_items(
                self.hall_sheet_name_combo,
                list(self._hall_sheet_columns.keys()),
                preferred=self.hall_sheet_name_combo.currentText() or None,
            )
            self._refresh_hall_column_combos()
        except Exception as exc:  # noqa: BLE001 - show preload failures in form
            self._hall_sheet_columns = {}
            self._reset_combo(self.hall_sheet_name_combo)
            self._reset_combo(self.hall_col_combo)
            self._reset_combo(self.hall_capacity_col_combo)
            self._reset_combo(self.hall_group_col_combo)
            self.hall_sheet_name_combo.addItem("Error")
            self.hall_sheet_name_combo.setToolTip(str(exc))

    def _refresh_registration_column_combos(self) -> None:
        columns = self._columns_for_selected_sheet(
            self._registration_sheet_columns,
            self.sheet_name_combo,
        )

        preferred_student = self._preferred_column(columns, ("student_id", "student", "name"))
        preferred_course = self._preferred_column(columns, ("course", "course_title", "title"))
        self._set_combo_items(self.student_col_combo, columns, preferred_student)
        self._set_combo_items(self.course_col_combo, columns, preferred_course)

    def _refresh_hall_column_combos(self) -> None:
        columns = self._columns_for_selected_sheet(
            self._hall_sheet_columns,
            self.hall_sheet_name_combo,
        )

        preferred_hall = self._preferred_column(columns, ("hall", "hall name"))
        preferred_capacity = self._preferred_column(columns, ("capacity", "half capacity"))
        preferred_group = self._preferred_column(columns, ("group",))

        self._set_combo_items(self.hall_col_combo, columns, preferred_hall)
        self._set_combo_items(self.hall_capacity_col_combo, columns, preferred_capacity)
        self._set_combo_items(self.hall_group_col_combo, columns, preferred_group)

    def get_ui_state(self) -> dict[str, str | int | bool]:
        """Return a serializable snapshot of form values for persistence."""

        return {
            "registration_file": self.registration_file_input.text(),
            "student_col": self.student_col_combo.currentText(),
            "course_col": self.course_col_combo.currentText(),
            "sheet_name": self.sheet_name_combo.currentText(),
            "hall_file": self.hall_file_input.text(),
            "hall_col": self.hall_col_combo.currentText(),
            "hall_capacity_col": self.hall_capacity_col_combo.currentText(),
            "hall_group_col": self.hall_group_col_combo.currentText(),
            "hall_sheet_name": self.hall_sheet_name_combo.currentText(),
            "slots_per_day": self.slots_per_day_input.value(),
            "limit_days": self.limit_days_checkbox.isChecked(),
            "max_days": self.max_days_input.value(),
            "num_tries": self.num_tries_input.value(),
            "random_seed": self.random_seed_input.value(),
            "n": self.n_input.value(),
        }

    def apply_ui_state(self, state: dict[str, str | int | bool]) -> None:
        """Apply persisted form values and refresh preload metadata labels."""

        registration_file = str(state.get("registration_file", ""))
        self.registration_file_input.setText(registration_file)

        hall_file = str(state.get("hall_file", ""))
        self.hall_file_input.setText(hall_file)

        self.slots_per_day_input.setValue(int(state.get("slots_per_day", 2)))
        self.limit_days_checkbox.setChecked(bool(state.get("limit_days", False)))
        self.max_days_input.setValue(int(state.get("max_days", 14)))
        self.num_tries_input.setValue(int(state.get("num_tries", 32)))
        self.random_seed_input.setValue(int(state.get("random_seed", 0)))
        self.n_input.setValue(int(state.get("n", 4)))

        if registration_file:
            self._preload_registration_file(registration_file)
        if hall_file:
            self._preload_hall_file(hall_file)

        saved_sheet = str(state.get("sheet_name", ""))
        saved_student_col = str(state.get("student_col", ""))
        saved_course_col = str(state.get("course_col", ""))
        saved_hall_sheet = str(state.get("hall_sheet_name", ""))
        saved_hall_col = str(state.get("hall_col", ""))
        saved_capacity_col = str(state.get("hall_capacity_col", ""))
        saved_group_col = str(state.get("hall_group_col", ""))

        if saved_sheet and self.sheet_name_combo.findText(saved_sheet) >= 0:
            self.sheet_name_combo.setCurrentText(saved_sheet)
        if saved_student_col and self.student_col_combo.findText(saved_student_col) >= 0:
            self.student_col_combo.setCurrentText(saved_student_col)
        if saved_course_col and self.course_col_combo.findText(saved_course_col) >= 0:
            self.course_col_combo.setCurrentText(saved_course_col)

        if saved_hall_sheet and self.hall_sheet_name_combo.findText(saved_hall_sheet) >= 0:
            self.hall_sheet_name_combo.setCurrentText(saved_hall_sheet)
        if saved_hall_col and self.hall_col_combo.findText(saved_hall_col) >= 0:
            self.hall_col_combo.setCurrentText(saved_hall_col)
        if saved_capacity_col and self.hall_capacity_col_combo.findText(saved_capacity_col) >= 0:
            self.hall_capacity_col_combo.setCurrentText(saved_capacity_col)
        if saved_group_col and self.hall_group_col_combo.findText(saved_group_col) >= 0:
            self.hall_group_col_combo.setCurrentText(saved_group_col)

        if not registration_file:
            self._reset_combo(self.sheet_name_combo)
            self._reset_combo(self.student_col_combo)
            self._reset_combo(self.course_col_combo)
        if not hall_file:
            self._reset_combo(self.hall_sheet_name_combo)
            self._reset_combo(self.hall_col_combo)
            self._reset_combo(self.hall_capacity_col_combo)
            self._reset_combo(self.hall_group_col_combo)

    def get_options(self) -> SchedulingOptions:
        """Build scheduling options from current form values."""

        parsed_sheet_name = self._selected_sheet_name(self.sheet_name_combo)

        reg_config = RegDataConfig(
            student_id_col=self.student_col_combo.currentText().strip(),
            course_col=self.course_col_combo.currentText().strip(),
            sheet_name=parsed_sheet_name,
        )

        hall_file_raw = self.hall_file_input.text().strip()
        parsed_hall_sheet_name = self._selected_sheet_name(self.hall_sheet_name_combo)
        hall_capacity_file = hall_file_raw if hall_file_raw else None
        hall_config = (
            HallDataConfig(
                hall_col=self.hall_col_combo.currentText().strip(),
                capacity_col=self.hall_capacity_col_combo.currentText().strip(),
                group_col=self.hall_group_col_combo.currentText().strip(),
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
