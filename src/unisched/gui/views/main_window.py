"""Main window composition for the unisched GUI."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from unisched.gui.controllers import ScheduleRequest, SchedulerController
from unisched.gui.models import AppState
from unisched.gui.views.config_form import ConfigFormWidget
from unisched.gui.views.file_selection import FileSelectionWidget
from unisched.gui.views.results_view import ResultsViewWidget


class MainWindow(QMainWindow):
    """Coordinate view widgets and controller signals."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Unisched - Exam Scheduler")
        self.resize(1000, 700)

        self.state = AppState()
        self.controller = SchedulerController(self)

        self.file_selection = FileSelectionWidget(self)
        self.config_form = ConfigFormWidget(self)
        self.results_view = ResultsViewWidget(self)

        self.run_button = QPushButton("Generate Schedule")
        self.status_label = QLabel("Ready")

        self._setup_layout()
        self._connect_signals()

    def _setup_layout(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.addWidget(self.file_selection)
        root_layout.addWidget(self.config_form)

        action_row = QHBoxLayout()
        action_row.addWidget(self.run_button)
        action_row.addWidget(self.status_label, 1)
        root_layout.addLayout(action_row)

        root_layout.addWidget(self.results_view, 1)

    def _connect_signals(self) -> None:
        self.file_selection.file_selected.connect(self._on_file_selected)
        self.run_button.clicked.connect(self._on_run_clicked)

        self.controller.started.connect(self._on_schedule_started)
        self.controller.finished.connect(self._on_schedule_finished)
        self.controller.failed.connect(self._on_schedule_failed)

    def _on_file_selected(self, file_path: str) -> None:
        self.state.selected_file = file_path
        self.status_label.setText(f"Selected: {file_path}")

    def _on_run_clicked(self) -> None:
        selected_file = self.file_selection.current_file_path()
        if not selected_file:
            QMessageBox.warning(self, "Missing File", "Please choose a registration file first.")
            return

        options = self.config_form.get_options()
        request = ScheduleRequest(
            input_file=selected_file,
            config=options.config,
            max_days=options.max_days,
            slots_per_day=options.slots_per_day,
        )

        self.controller.run_schedule(request)

    def _on_schedule_started(self) -> None:
        self.state.is_running = True
        self.run_button.setEnabled(False)
        self.status_label.setText("Scheduling in progress...")

    def _on_schedule_finished(self, schedule_result: object) -> None:
        self.state.is_running = False
        self.state.last_error = ""
        self.state.last_schedule = schedule_result
        self.run_button.setEnabled(True)
        self.status_label.setText("Scheduling complete")
        self.results_view.set_schedule(schedule_result)

    def _on_schedule_failed(self, message: str) -> None:
        self.state.is_running = False
        self.state.last_error = message
        self.run_button.setEnabled(True)
        self.status_label.setText("Scheduling failed")
        self.results_view.set_error(message)
        QMessageBox.critical(self, "Scheduling Failed", message)
