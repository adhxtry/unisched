"""Results view for schedule summaries and assignments."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from unisched.domain.models import Schedule


class ResultsViewWidget(QGroupBox):
    """Render scheduling summary and assignment table."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Schedule Results", parent)

        main_layout = QVBoxLayout(self)

        summary_row = QHBoxLayout()
        self.summary_label = QLabel("No schedule generated yet")
        summary_row.addWidget(self.summary_label)

        main_layout.addLayout(summary_row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Course", "Day", "Slot"])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

    def clear_results(self) -> None:
        """Clear displayed summary and assignment rows."""

        self.summary_label.setText("No schedule generated yet")
        self.table.setRowCount(0)

    def set_error(self, message: str) -> None:
        """Display an error message in the summary area."""

        self.summary_label.setText(f"Error: {message}")
        self.table.setRowCount(0)

    def set_schedule(self, schedule: Schedule) -> None:
        """Display schedule metrics and assignment rows."""

        self.summary_label.setText(
            f"Scheduled: {len(schedule.events)} | "
            f"Unscheduled: {len(schedule.unscheduled_courses)} | "
            f"Penalty: {schedule.penalty}"
        )

        self.table.setRowCount(len(schedule.events))
        for row, event in enumerate(schedule.events):
            self.table.setItem(row, 0, QTableWidgetItem(event.course_code))
            self.table.setItem(row, 1, QTableWidgetItem(str(event.time_slot.day)))
            self.table.setItem(row, 2, QTableWidgetItem(str(event.time_slot.slot_index)))
