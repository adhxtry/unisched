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
        self.setToolTip(
            "View and export the generated exam timetable, metrics, and room assignments."
        )

        main_layout = QVBoxLayout(self)

        summary_row = QHBoxLayout()
        self.summary_label = QLabel("No schedule generated yet")
        self.summary_label.setToolTip(
            "Schedule Metrics:\n"
            "• Scheduled: Total number of exams successfully placed in the timetable.\n"
            "• Unscheduled: Exams that could not fit into the available time slots / rooms.\n"
            "• Penalty: Soft penalty score based on same-day student exams (0 is a perfect schedule with zero same-day conflicts)."
        )
        summary_row.addWidget(self.summary_label)

        main_layout.addLayout(summary_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Course", "Day", "Slot", "Halls"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setToolTip(
            "Exam Timetable Assignments:\n"
            "• Course: The course code or subject title.\n"
            "• Day: The scheduled exam day number (1, 2, ...).\n"
            "• Slot: The session on that day (e.g. 1 for Morning, 2 for Afternoon).\n"
            "• Halls: The assigned exam halls with adequate capacity."
        )
        main_layout.addWidget(self.table)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        self.export_button = QPushButton("Export CSV", self)
        self.export_button.setToolTip(
            "Click to export the displayed timetable to a CSV spreadsheet file on your computer."
        )
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
