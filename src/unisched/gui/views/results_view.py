"""Results view for schedule summaries and assignments."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from unisched.domain.models import Schedule


class ResultsViewWidget(QGroupBox):
    """Render scheduling summary and assignment table."""

    export_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Schedule Results", parent)

        main_layout = QVBoxLayout(self)

        summary_row = QHBoxLayout()
        self.summary_label = QLabel("No schedule generated yet")
        summary_row.addWidget(self.summary_label)

        main_layout.addLayout(summary_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Course", "Day", "Slot", "Halls"])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        self.export_button = QPushButton("Export CSV", self)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_requested.emit)
        action_row.addWidget(self.export_button)
        main_layout.addLayout(action_row)

    def clear_results(self) -> None:
        """Clear displayed summary and assignment rows."""

        self.summary_label.setText("No schedule generated yet")
        self.table.setRowCount(0)
        self.export_button.setEnabled(False)

    def set_error(self, message: str) -> None:
        """Display an error message in the summary area."""

        self.summary_label.setText(f"Error: {message}")
        self.table.setRowCount(0)
        self.export_button.setEnabled(False)

    def set_schedule(self, schedule: Schedule) -> None:
        """Display schedule metrics and assignment rows."""

        self.summary_label.setText(
            f"Scheduled: {len(schedule.events)} | "
            f"Unscheduled: {len(schedule.unscheduled_courses)} | "
            f"Penalty: {schedule.penalty}"
        )

        sorted_events = sorted(
            schedule.events,
            key=lambda event: (event.time_slot.day, event.time_slot.slot_index, event.course_code),
        )

        self.table.setRowCount(len(sorted_events))
        for row, event in enumerate(sorted_events):
            self.table.setItem(row, 0, QTableWidgetItem(event.course_code))
            self.table.setItem(row, 1, QTableWidgetItem(str(event.time_slot.day)))
            self.table.setItem(row, 2, QTableWidgetItem(str(event.time_slot.slot_index)))
            self.table.setItem(row, 3, QTableWidgetItem(", ".join(event.halls)))

        self.export_button.setEnabled(True)
