"""
settings_dialog.py — Diálogo de configuración de NexusSniff.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QFormLayout, QLineEdit,
    QCheckBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont

from app.main import load_theme


class SettingsDialog(QDialog):
    """Diálogo de configuración de la aplicación."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración — NexusSniff")
        self.setMinimumSize(500, 450)
        self._settings = QSettings("NexusSniff", "NexusSniff")
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ── Apariencia ──
        appearance_group = QGroupBox("Apariencia")
        appearance_layout = QFormLayout(appearance_group)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark Mode (Nexus)", "Light Mode"])
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        appearance_layout.addRow("Tema:", self._theme_combo)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 18)
        self._font_size_spin.setValue(13)
        self._font_size_spin.setSuffix(" px")
        appearance_layout.addRow("Tamaño de fuente:", self._font_size_spin)

        layout.addWidget(appearance_group)

        # ── Captura ──
        capture_group = QGroupBox("Motor de Captura")
        capture_layout = QFormLayout(capture_group)

        self._buffer_size_spin = QSpinBox()
        self._buffer_size_spin.setRange(1024, 1048576)
        self._buffer_size_spin.setValue(65536)
        self._buffer_size_spin.setSingleStep(1024)
        self._buffer_size_spin.setSuffix(" paquetes")
        capture_layout.addRow("Tamaño del ring buffer:", self._buffer_size_spin)

        self._snap_len_spin = QSpinBox()
        self._snap_len_spin.setRange(64, 65535)
        self._snap_len_spin.setValue(65535)
        self._snap_len_spin.setSuffix(" bytes")
        capture_layout.addRow("Snapshot length:", self._snap_len_spin)

        self._promiscuous_check = QCheckBox("Capturar en modo promiscuo")
        self._promiscuous_check.setChecked(True)
        capture_layout.addRow("", self._promiscuous_check)

        layout.addWidget(capture_group)

        # ── Exportación ──
        export_group = QGroupBox("Exportación")
        export_layout = QFormLayout(export_group)

        dir_layout = QHBoxLayout()
        self._export_dir = QLineEdit()
        self._export_dir.setPlaceholderText("Directorio de capturas...")
        dir_layout.addWidget(self._export_dir)

        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self._browse_export_dir)
        dir_layout.addWidget(browse_btn)

        export_layout.addRow("Directorio:", dir_layout)
        layout.addWidget(export_group)

        layout.addStretch()

        # ── Botones ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _browse_export_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de capturas"
        )
        if directory:
            self._export_dir.setText(directory)

    def _on_theme_changed(self, theme_text: str):
        """Aplica el tema instantáneamente al cambiar la selección."""
        theme_file = "light" if "Light Mode" in theme_text else "dark"
        load_theme(QApplication.instance(), theme_file)
        self.setStyleSheet(QApplication.instance().styleSheet())

    def get_settings(self) -> dict:
        """Devuelve la configuración actual."""
        return {
            'theme': self._theme_combo.currentText(),
            'font_size': self._font_size_spin.value(),
            'buffer_size': self._buffer_size_spin.value(),
            'snap_len': self._snap_len_spin.value(),
            'promiscuous': self._promiscuous_check.isChecked(),
            'export_dir': self._export_dir.text(),
        }

    def _load_settings(self):
        """Carga la configuración desde QSettings o usa defaults."""
        theme = self._settings.value('theme', 'Dark Mode (Nexus)')
        idx = self._theme_combo.findText(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        
        self._font_size_spin.setValue(int(self._settings.value('font_size', 13)))
        self._buffer_size_spin.setValue(int(self._settings.value('buffer_size', 65536)))
        self._snap_len_spin.setValue(int(self._settings.value('snap_len', 65535)))
        
        # El valor de bool puede cargarse como string por QSettings
        promisc = self._settings.value('promiscuous', True, type=bool)
        self._promiscuous_check.setChecked(promisc)
        
        self._export_dir.setText(self._settings.value('export_dir', ''))

    def accept(self):
        """Guarda la configuración y cierra."""
        conf = self.get_settings()
        for k, v in conf.items():
            self._settings.setValue(k, v)
        super().accept()
