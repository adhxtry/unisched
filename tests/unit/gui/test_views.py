import pytest
from PySide6.QtWidgets import QApplication

from unisched.gui.views.config_form import ConfigFormWidget
from unisched.gui.views.main_window import MainWindow
from unisched.gui.views.results_view import ResultsViewWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_config_form_widget_instantiation(qapp) -> None:
    widget = ConfigFormWidget()
    assert widget.student_col_combo is not None
    assert widget.optimizer_combo is not None
    assert widget.registration_file_input is not None


def test_results_view_widget_instantiation(qapp) -> None:
    widget = ResultsViewWidget()
    assert widget.table is not None
    assert widget.export_button is not None


def test_main_window_instantiation(qapp) -> None:
    window = MainWindow()
    assert window.config_form is not None
    assert window.results_view is not None
    assert window.run_button is not None


def test_theme_toggle(qapp) -> None:
    window = MainWindow()
    initial_theme = window.current_theme
    window._toggle_theme()
    assert window.current_theme != initial_theme
    window._toggle_theme()
    assert window.current_theme == initial_theme
