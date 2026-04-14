"""Main window composition for the unisched GUI."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from unisched.domain.models import Schedule
from unisched.gui.controllers import ScheduleRequest, SchedulerController
from unisched.gui.models import AppState
from unisched.io import save_schedule_to_csv
from unisched.gui.views.config_form import ConfigFormWidget
from unisched.gui.views.results_view import ResultsViewWidget


class MainWindow(QMainWindow):
    """Coordinate view widgets and controller signals."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Unisched - Exam Scheduler")
        self.resize(1000, 700)

        self.state = AppState()
        self.controller = SchedulerController(self)

        self.config_form = ConfigFormWidget(self)
        self.results_view = ResultsViewWidget(self)
        self.tabs = QTabWidget(self)

        self.run_button = QPushButton("Generate Schedule")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Ready")

        self._setup_layout()
        self._connect_signals()
        self._load_ui_state()

    def _setup_layout(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)

        configuration_tab = QWidget(self)
        configuration_layout = QVBoxLayout(configuration_tab)
        configuration_layout.addWidget(self.config_form)
        configuration_layout.addStretch(1)

        schedule_tab = QWidget(self)
        schedule_layout = QVBoxLayout(schedule_tab)
        schedule_layout.addWidget(self.results_view)

        self.tabs.addTab(configuration_tab, "Configuration")
        self.tabs.addTab(schedule_tab, "Schedule")
        root_layout.addWidget(self.tabs, 1)

        action_row = QHBoxLayout()
        action_row.addWidget(self.progress_bar)
        action_row.addStretch(1)
        action_row.addWidget(self.status_label)
        action_row.addWidget(self.run_button)
        root_layout.addLayout(action_row)

    def _connect_signals(self) -> None:
        self.run_button.clicked.connect(self._on_run_clicked)
        self.results_view.export_requested.connect(self._on_export_requested)

        self.controller.started.connect(self._on_schedule_started)
        self.controller.finished.connect(self._on_schedule_finished)
        self.controller.failed.connect(self._on_schedule_failed)
        self.controller.progress.connect(self._on_schedule_progress)

    def _on_run_clicked(self) -> None:
        options = self.config_form.get_options()
        selected_file = options.registration_file
        if not selected_file:
            QMessageBox.warning(self, "Missing File", "Please choose a registration file first.")
            return

        request = ScheduleRequest(
            input_file=selected_file,
            reg_config=options.reg_config,
            max_days=options.max_days,
            slots_per_day=options.slots_per_day,
            hall_capacity_file=options.hall_capacity_file,
            hall_config=options.hall_config,
            num_tries=options.num_tries,
            random_seed=options.random_seed,
            n=options.n,
        )

        self.state.last_settings["num_tries"] = options.num_tries
        self.controller.run_schedule(request)

    def _on_schedule_started(self) -> None:
        self.state.is_running = True
        self.run_button.setEnabled(False)
        num_tries = int(self.state.last_settings.get("num_tries", 1) or 1)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, max(1, num_tries))
        self.progress_bar.setValue(0)
        self.status_label.setText("Scheduling in progress...")

    def _on_schedule_finished(self, schedule_result: object) -> None:
        if not isinstance(schedule_result, Schedule):
            self._on_schedule_failed("Scheduler returned an unexpected result type")
            return

        self.state.is_running = False
        self.state.last_error = ""
        self.state.last_schedule = schedule_result
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Scheduling complete")
        self.results_view.set_schedule(schedule_result)
        self.tabs.setCurrentIndex(1)

    def _on_schedule_failed(self, message: str) -> None:
        self.state.is_running = False
        self.state.last_error = message
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Scheduling failed")
        self.results_view.set_error(message)
        QMessageBox.critical(self, "Scheduling Failed", message)

    def _on_schedule_progress(self, current_iteration: int, total_iterations: int) -> None:
        self.progress_bar.setRange(0, max(1, total_iterations))
        self.progress_bar.setValue(min(current_iteration, total_iterations))

    def _on_export_requested(self) -> None:
        schedule_result = self.state.last_schedule
        if schedule_result is None:
            QMessageBox.warning(self, "No Schedule", "Generate a schedule before exporting.")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export schedule as CSV",
            "schedule.csv",
            "CSV files (*.csv)",
        )
        if not output_path:
            return

        try:
            save_schedule_to_csv(schedule_result, output_path)
            self.status_label.setText("Schedule exported")
        except Exception as exc:  # noqa: BLE001 - GUI should surface failures
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _ui_state_path(self) -> Path:
        base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not base_dir:
            base_dir = str(Path.home() / ".unisched")

        state_dir = Path(base_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "ui_state.json"

    def _load_ui_state(self) -> None:
        state_path = self._ui_state_path()
        if not state_path.exists():
            return

        try:
            state_payload = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return

        config_state = state_payload.get("config_form", {})
        if isinstance(config_state, dict):
            self.config_form.apply_ui_state(config_state)

        tab_index = state_payload.get("active_tab")
        if isinstance(tab_index, int) and 0 <= tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(tab_index)

    def _save_ui_state(self) -> None:
        state_payload = {
            "active_tab": self.tabs.currentIndex(),
            "config_form": self.config_form.get_ui_state(),
        }
        state_path = self._ui_state_path()
        state_path.write_text(
            json.dumps(state_payload, indent=2),
            encoding="utf-8",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self._save_ui_state()
        except OSError:
            pass

        super().closeEvent(event)
