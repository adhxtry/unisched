"""File selection widget for scheduling input."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FileSelectionWidget(QWidget):
    """Provide registration file selection controls."""

    file_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)

        title = QLabel("Registration File:")
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Choose CSV/Excel/ODS file")

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse_file)

        layout.addWidget(title)
        layout.addWidget(self.path_edit, 1)
        layout.addWidget(browse_button)

    def set_file_path(self, file_path: str) -> None:
        """Set selected path and notify listeners."""

        self.path_edit.setText(file_path)
        self.file_selected.emit(file_path)

    def current_file_path(self) -> str:
        """Return selected file path."""

        return self.path_edit.text().strip()

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select registration file",
            "",
            "Registration files (*.csv *.xlsx *.xls *.ods);;All files (*.*)",
        )
        if path:
            self.set_file_path(path)
