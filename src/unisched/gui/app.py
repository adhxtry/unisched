"""GUI application entrypoint for unisched."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .views import MainWindow


def run_gui_app() -> int:
    """Start the Qt application and return process exit code."""

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
