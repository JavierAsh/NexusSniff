# conftest.py — Configuración pytest para tests de NexusSniff
import pytest


@pytest.fixture(scope="session")
def qapp():
    """Proporciona una QApplication compartida para todos los tests."""
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
