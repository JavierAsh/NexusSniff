"""
crash_dialog.py — Diálogo de Crash Report premium para NexusSniff.

Captura excepciones no manejadas y las muestra al usuario con
opción de guardar un log detallado antes de cerrar la aplicación.
"""

import sys
import traceback
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QWidget, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class CrashDialog(QDialog):
    """Diálogo premium para mostrar crashes fatales."""

    def __init__(self, exc_type, exc_value, exc_tb, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NexusSniff — Error Fatal")
        self.setMinimumSize(620, 420)
        self.setMaximumSize(800, 600)
        self.setObjectName("crashDialog")

        self._exc_type = exc_type
        self._exc_value = exc_value
        self._exc_tb = exc_tb
        self._traceback_text = "".join(
            traceback.format_exception(exc_type, exc_value, exc_tb)
        )

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── Header ──
        header = QLabel("⚠  Error Fatal Inesperado")
        header.setObjectName("crashHeader")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #ef4444;")
        layout.addWidget(header)

        # ── Descripción ──
        desc = QLabel(
            "NexusSniff ha encontrado un error crítico.\n"
            "Puedes guardar el reporte antes de cerrar la aplicación."
        )
        desc.setObjectName("crashDescription")
        desc.setWordWrap(True)
        desc.setFont(QFont("Segoe UI", 11))
        layout.addWidget(desc)

        # ── Traceback ──
        self._trace_view = QTextEdit()
        self._trace_view.setObjectName("crashTraceback")
        self._trace_view.setReadOnly(True)
        self._trace_view.setFont(QFont("Consolas", 10))
        self._trace_view.setPlainText(self._traceback_text)
        self._trace_view.setStyleSheet(
            "QTextEdit { background: #0d1117; color: #e6edf3; "
            "border: 1px solid #30363d; border-radius: 6px; padding: 8px; }"
        )
        layout.addWidget(self._trace_view, stretch=1)

        # ── Botones ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._save_btn = QPushButton("💾  Guardar Reporte")
        self._save_btn.setObjectName("crashSaveBtn")
        self._save_btn.setMinimumHeight(36)
        self._save_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._save_btn.clicked.connect(self._save_crash_log)
        btn_row.addWidget(self._save_btn)

        btn_row.addStretch()

        self._close_btn = QPushButton("Cerrar Aplicación")
        self._close_btn.setObjectName("crashCloseBtn")
        self._close_btn.setMinimumHeight(36)
        self._close_btn.setFont(QFont("Segoe UI", 10))
        self._close_btn.clicked.connect(self._close_app)
        btn_row.addWidget(self._close_btn)

        layout.addLayout(btn_row)

    def _save_crash_log(self):
        """Guarda el log del crash a disco."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path.home() / "NexusSniff_Logs"
        log_dir.mkdir(exist_ok=True)

        log_path = log_dir / f"nexus_crash_{timestamp}.log"

        header = (
            f"NexusSniff Crash Report\n"
            f"{'=' * 50}\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
            f"Exception: {self._exc_type.__name__}: {self._exc_value}\n"
            f"{'=' * 50}\n\n"
        )

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(header)
                f.write(self._traceback_text)

            self._save_btn.setText(f"✓ Guardado en {log_path.name}")
            self._save_btn.setEnabled(False)
            logger.info("Crash log guardado: %s", log_path)
        except OSError as e:
            self._save_btn.setText(f"Error: {e}")
            logger.error("No se pudo guardar crash log: %s", e)

    def _close_app(self):
        """Cierra la aplicación de forma limpia."""
        self.reject()
        app = QApplication.instance()
        if app:
            app.quit()


def install_exception_hook():
    """Instala el hook global de excepciones para capturar crashes."""
    original_hook = sys.excepthook

    def _exception_handler(exc_type, exc_value, exc_tb):
        # Ignorar KeyboardInterrupt (Ctrl+C)
        if issubclass(exc_type, KeyboardInterrupt):
            original_hook(exc_type, exc_value, exc_tb)
            return

        # Loguear la excepción
        logger.critical(
            "Excepción no manejada capturada",
            exc_info=(exc_type, exc_value, exc_tb)
        )

        # Mostrar diálogo solo si hay una QApplication activa
        app = QApplication.instance()
        if app:
            try:
                dialog = CrashDialog(exc_type, exc_value, exc_tb)
                dialog.exec()
            except Exception:
                # Si el diálogo mismo falla, caer al hook original
                original_hook(exc_type, exc_value, exc_tb)
        else:
            original_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _exception_handler
