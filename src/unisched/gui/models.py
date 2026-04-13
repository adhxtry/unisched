"""GUI-side state models for the unisched desktop app."""

from __future__ import annotations

from dataclasses import dataclass, field

from unisched.domain.models import Schedule


@dataclass(slots=True)
class AppState:
    """Represent mutable GUI state independent from scheduler internals."""

    selected_file: str = ""
    is_running: bool = False
    last_error: str = ""
    last_schedule: Schedule | None = None
    status_message: str = "Ready"
    last_settings: dict[str, str | int | None] = field(default_factory=dict)
