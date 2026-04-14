"""Controller for launching scheduling operations from the GUI."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QThread, QObject, Signal

from unisched import schedule
from unisched.core import GraphColoringOptimizer, SchedulingCoordinator
from unisched.domain.models import Schedule
from unisched.io.loader import HallDataConfig, RegDataConfig


@dataclass(frozen=True, slots=True)
class ScheduleRequest:
    """Represent input required to run one schedule operation."""

    input_file: str
    reg_config: RegDataConfig
    max_days: int | None
    slots_per_day: int
    hall_capacity_file: str | None = None
    hall_config: HallDataConfig | None = None
    num_tries: int = 32
    random_seed: int = 0
    n: int = 4


class _ScheduleWorker(QThread):
    """Run one scheduling request in a background Qt thread."""

    schedule_ready = Signal(object)
    schedule_failed = Signal(str)
    progress_updated = Signal(int, int)

    def __init__(self, request: ScheduleRequest, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.request = request

    def run(self) -> None:
        try:
            optimizer = GraphColoringOptimizer(
                num_tries=self.request.num_tries,
                random_seed=self.request.random_seed,
                n=self.request.n,
                iteration_callback=self._on_iteration_completed,
            )
            coordinator = SchedulingCoordinator(
                optimizer=optimizer,
                slots_per_day=self.request.slots_per_day,
                max_days=self.request.max_days,
            )

            result = schedule(
                self.request.input_file,
                reg_config=self.request.reg_config,
                hall_capacity_file=self.request.hall_capacity_file,
                hall_config=self.request.hall_config,
                coordinator=coordinator,
            )
            self.schedule_ready.emit(result)
        except Exception as exc:  # noqa: BLE001 - GUI should surface failures
            self.schedule_failed.emit(str(exc))

    def _on_iteration_completed(self, current_iteration: int) -> None:
        self.progress_updated.emit(current_iteration, self.request.num_tries)


class SchedulerController(QObject):
    """Bridge GUI actions to scheduling API calls."""

    started = Signal()
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(int, int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker: _ScheduleWorker | None = None

    def run_schedule(self, request: ScheduleRequest) -> None:
        """Start a scheduling run unless a previous one is still active."""

        if self._worker is not None and self._worker.isRunning():
            self.failed.emit("Scheduling is already running")
            return

        worker = _ScheduleWorker(request, self)
        worker.schedule_ready.connect(self._on_schedule_ready)
        worker.schedule_failed.connect(self._on_schedule_failed)
        worker.progress_updated.connect(self._on_schedule_progress)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        self.started.emit()
        worker.start()

    def _on_schedule_ready(self, schedule_result: Schedule) -> None:
        self.finished.emit(schedule_result)

    def _on_schedule_failed(self, message: str) -> None:
        self.failed.emit(message)

    def _on_schedule_progress(self, current_iteration: int, total_iterations: int) -> None:
        self.progress.emit(current_iteration, total_iterations)

    def _on_worker_finished(self) -> None:
        self._worker = None
