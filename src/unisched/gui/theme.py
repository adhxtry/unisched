"""Theme definitions and stylesheet helpers for Unisched GUI."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QWidget

THEME_LIGHT = "light"
THEME_DARK = "dark"

LIGHT_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f8f9fa;
    color: #212529;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QGroupBox {
    font-weight: 600;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 15px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #495057;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 5px 8px;
    color: #212529;
    min-height: 22px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #0d6efd;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #e9ecef;
    color: #6c757d;
}

QPushButton {
    background-color: #e9ecef;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: 500;
    color: #212529;
}

QPushButton:hover {
    background-color: #dde0e3;
}

QPushButton:pressed {
    background-color: #ced4da;
}

QPushButton:disabled {
    background-color: #e9ecef;
    color: #adb5bd;
    border-color: #e9ecef;
}

QTabWidget::pane {
    border: 1px solid #dee2e6;
    background-color: #ffffff;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #e9ecef;
    border: 1px solid #dee2e6;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom-color: #ffffff;
    font-weight: 600;
}

QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    gridline-color: #e9ecef;
    border: 1px solid #dee2e6;
    border-radius: 4px;
}

QHeaderView::section {
    background-color: #f1f3f5;
    padding: 6px;
    border: 1px solid #dee2e6;
    font-weight: 600;
}

QProgressBar {
    border: 1px solid #ced4da;
    border-radius: 4px;
    text-align: center;
    background-color: #e9ecef;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #0d6efd;
    border-radius: 3px;
}

QToolTip {
    background-color: #212529;
    color: #f8f9fa;
    border: 1px solid #343a40;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}
"""

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1a1b1e;
    color: #c1c2c5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QGroupBox {
    font-weight: 600;
    border: 1px solid #2c2e33;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 15px;
    background-color: #25262b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #909296;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #141517;
    border: 1px solid #373a40;
    border-radius: 4px;
    padding: 5px 8px;
    color: #c1c2c5;
    min-height: 22px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #339af0;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #25262b;
    color: #5c5f66;
}

QPushButton {
    background-color: #2c2e33;
    border: 1px solid #373a40;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: 500;
    color: #e9ecef;
}

QPushButton:hover {
    background-color: #373a40;
}

QPushButton:pressed {
    background-color: #25262b;
}

QPushButton:disabled {
    background-color: #1a1b1e;
    color: #5c5f66;
    border-color: #25262b;
}

QTabWidget::pane {
    border: 1px solid #2c2e33;
    background-color: #25262b;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #25262b;
    border: 1px solid #2c2e33;
    color: #909296;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #2c2e33;
    border-bottom-color: #2c2e33;
    color: #e9ecef;
    font-weight: 600;
}

QTableWidget {
    background-color: #1a1b1e;
    alternate-background-color: #25262b;
    gridline-color: #2c2e33;
    border: 1px solid #2c2e33;
    border-radius: 4px;
    color: #c1c2c5;
}

QHeaderView::section {
    background-color: #25262b;
    padding: 6px;
    border: 1px solid #2c2e33;
    font-weight: 600;
    color: #e9ecef;
}

QProgressBar {
    border: 1px solid #373a40;
    border-radius: 4px;
    text-align: center;
    background-color: #25262b;
    height: 18px;
    color: #e9ecef;
}

QProgressBar::chunk {
    background-color: #1c7ed6;
    border-radius: 3px;
}

QToolTip {
    background-color: #141517;
    color: #e9ecef;
    border: 1px solid #373a40;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}
"""


def apply_theme(target: QWidget | QApplication, theme_name: str) -> None:
    """Apply the given theme stylesheet ('light' or 'dark')."""
    stylesheet = DARK_STYLESHEET if theme_name == THEME_DARK else LIGHT_STYLESHEET
    target.setStyleSheet(stylesheet)
