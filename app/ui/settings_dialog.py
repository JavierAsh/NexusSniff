"""
settings_dialog.py — Diálogo de configuración premium de NexusSniff.

Diseño con sidebar lateral para navegación entre secciones:
  • General    — Tema y preferencias visuales
  • Captura    — Motor de captura (buffer, snapshot, promiscuo)
  • Exportación — Directorio de salida con validación
  • Sistema    — Info de versión, Npcap, Python
"""

import sys
import os
import platform
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QFormLayout, QLineEdit,
    QCheckBox, QFileDialog, QApplication, QWidget, QStackedWidget,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon


from app.ui.icons import create_vector_icon
from app import __version__


# ═══════════════════════════════════════════════════════════════
#  Sidebar Button (interno al diálogo)
# ═══════════════════════════════════════════════════════════════

class _SettingsSidebarBtn(QPushButton):
    """Botón de navegación de la sidebar de settings."""

    def __init__(self, icon: QIcon, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsSidebarBtn")
        self.setCheckable(True)
        self.setFixedHeight(42)
        self.setIcon(icon)
        self.setIconSize(QSize(18, 18))
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


# ═══════════════════════════════════════════════════════════════
#  Settings Dialog
# ═══════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """Diálogo de configuración con sidebar de navegación."""

    DEFAULTS = {
        'theme': 'Dark Mode (Nexus)',
        'buffer_size': 65536,
        'snap_len': 65535,
        'promiscuous': True,
        'export_dir': '',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración — NexusSniff")
        self.setMinimumSize(680, 520)
        self.resize(720, 540)
        self._settings = QSettings("NexusSniff", "NexusSniff")

        # Guardar el tema original para poder revertir si el usuario cancela
        self._original_theme = self._settings.value('theme', self.DEFAULTS['theme'])

        self._setup_ui()
        self._load_settings()

        # Arrancar con el mismo tema activo (solo en el diálogo, no modificar app global)
        app = QApplication.instance()
        if app is not None:
            self.setStyleSheet(app.styleSheet())

    # ───────────────────────────────────────────────────────────
    #  UI Setup
    # ───────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Contenedor principal (sidebar + contenido)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("settingsSidebar")
        sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 16, 10, 16)
        sidebar_layout.setSpacing(4)

        # Título de la sidebar
        sidebar_title = QLabel("Configuración")
        sidebar_title.setObjectName("settingsSidebarTitle")
        sidebar_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addSpacing(12)

        # Botones de navegación
        self._nav_buttons = []

        self._btn_general = _SettingsSidebarBtn(
            create_vector_icon("settings", "#c8d0e0", 18), "  General"
        )
        self._nav_buttons.append(self._btn_general)

        self._btn_capture = _SettingsSidebarBtn(
            create_vector_icon("capture", "#c8d0e0", 18), "  Captura"
        )
        self._nav_buttons.append(self._btn_capture)

        self._btn_export = _SettingsSidebarBtn(
            create_vector_icon("folder", "#c8d0e0", 18), "  Exportación"
        )
        self._nav_buttons.append(self._btn_export)

        self._btn_system = _SettingsSidebarBtn(
            create_vector_icon("network", "#c8d0e0", 18), "  Sistema"
        )
        self._nav_buttons.append(self._btn_system)

        for btn in self._nav_buttons:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Botón restablecer
        self._reset_btn = QPushButton("↺ Restablecer")
        self._reset_btn.setObjectName("settingsResetBtn")
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.setToolTip("Volver a los valores predeterminados")
        self._reset_btn.clicked.connect(self._reset_defaults)
        sidebar_layout.addWidget(self._reset_btn)

        body.addWidget(sidebar)

        # Separador vertical
        v_sep = QFrame()
        v_sep.setObjectName("settingsVSep")
        v_sep.setFixedWidth(1)
        body.addWidget(v_sep)

        # ── Área de contenido ──
        content_area = QWidget()
        content_area.setObjectName("settingsContent")
        content_wrapper = QVBoxLayout(content_area)
        content_wrapper.setContentsMargins(24, 20, 24, 16)
        content_wrapper.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_general_page())
        self._stack.addWidget(self._build_capture_page())
        self._stack.addWidget(self._build_export_page())
        self._stack.addWidget(self._build_system_page())
        content_wrapper.addWidget(self._stack, 1)

        # ── Footer con botones ──
        footer_sep = QFrame()
        footer_sep.setObjectName("settingsFooterSep")
        footer_sep.setFixedHeight(1)
        content_wrapper.addWidget(footer_sep)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 12, 0, 0)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("  Guardar  ")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        content_wrapper.addLayout(btn_layout)
        body.addWidget(content_area, 1)

        root.addLayout(body, 1)

        # Conectar navegación
        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))

        # Activar primera página
        self._btn_general.setChecked(True)

    # ───────────────────────────────────────────────────────────
    #  Páginas de contenido
    # ───────────────────────────────────────────────────────────

    def _build_general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Título de sección
        layout.addWidget(self._section_title("General", "Personalización y apariencia"))

        # Tema
        group = QGroupBox("Apariencia")
        form = QFormLayout(group)
        form.setContentsMargins(16, 24, 16, 16)
        form.setVerticalSpacing(14)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark Mode (Nexus)", "Light Mode"])
        self._theme_combo.setToolTip(
            "El tema se aplica de forma global.\n"
            "Dark Mode: Fondo oscuro con acentos cyan.\n"
            "Light Mode: Fondo claro para entornos iluminados."
        )
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        form.addRow("Tema:", self._theme_combo)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _build_capture_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(self._section_title("Motor de Captura", "Configuración del engine C++ y Npcap"))

        group = QGroupBox("Parámetros de Captura")
        form = QFormLayout(group)
        form.setContentsMargins(16, 24, 16, 16)
        form.setVerticalSpacing(14)

        # Ring buffer
        self._buffer_size_spin = QSpinBox()
        self._buffer_size_spin.setRange(1024, 1048576)
        self._buffer_size_spin.setValue(65536)
        self._buffer_size_spin.setSingleStep(1024)
        self._buffer_size_spin.setSuffix(" paquetes")
        self._buffer_size_spin.setToolTip(
            "Cantidad máxima de paquetes que se almacenan en memoria.\n"
            "Valores altos consumen más RAM pero evitan pérdida de\n"
            "paquetes en redes de alto tráfico.\n"
            "Rango: 1,024 – 1,048,576"
        )
        form.addRow("Ring Buffer:", self._buffer_size_spin)

        # Snapshot length
        self._snap_len_spin = QSpinBox()
        self._snap_len_spin.setRange(64, 65535)
        self._snap_len_spin.setValue(65535)
        self._snap_len_spin.setSuffix(" bytes")
        self._snap_len_spin.setToolTip(
            "Cantidad de bytes a capturar por paquete.\n"
            "65535 captura el paquete completo.\n"
            "Valores menores ahorran memoria si solo\n"
            "necesitas inspeccionar cabeceras."
        )
        form.addRow("Snapshot Length:", self._snap_len_spin)

        # Modo promiscuo
        self._promiscuous_check = QCheckBox("Capturar en modo promiscuo")
        self._promiscuous_check.setChecked(True)
        self._promiscuous_check.setToolTip(
            "Modo promiscuo captura TODO el tráfico del segmento de red,\n"
            "no solo el dirigido a esta máquina.\n"
            "Desactívalo si solo necesitas tu propio tráfico."
        )
        form.addRow("", self._promiscuous_check)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _build_export_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(self._section_title("Exportación", "Directorio de salida para capturas"))

        group = QGroupBox("Destino de Exportación")
        form = QFormLayout(group)
        form.setContentsMargins(16, 24, 16, 16)
        form.setVerticalSpacing(14)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(8)
        dir_row.setContentsMargins(0, 0, 0, 0)

        self._export_dir = QLineEdit()
        self._export_dir.setPlaceholderText("Selecciona un directorio de capturas...")
        self._export_dir.setFixedHeight(36)
        self._export_dir.textChanged.connect(self._validate_export_dir)
        dir_row.addWidget(self._export_dir)

        browse_btn = QPushButton()
        browse_btn.setObjectName("browseButton")
        browse_btn.setIcon(create_vector_icon("folder", "#c8d0e0", 18))
        browse_btn.setFixedSize(36, 36)
        browse_btn.setToolTip("Seleccionar directorio")
        browse_btn.clicked.connect(self._browse_export_dir)
        dir_row.addWidget(browse_btn)

        form.addRow("Directorio:", dir_row)

        # Indicador de validación
        self._dir_status = QLabel("")
        self._dir_status.setObjectName("settingsDirStatus")
        form.addRow("", self._dir_status)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _build_system_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(self._section_title("Sistema", "Información del entorno"))

        group = QGroupBox("Información del Sistema")
        info_layout = QVBoxLayout(group)
        info_layout.setContentsMargins(16, 24, 16, 16)
        info_layout.setSpacing(10)

        # Info rows
        info_items = [
            ("NexusSniff", f"v{__version__}"),
            ("Python", f"{sys.version.split()[0]}  ({platform.architecture()[0]})"),
            ("Sistema", f"{platform.system()} {platform.release()}"),
            ("Arquitectura", platform.machine()),
        ]

        # Detectar Npcap
        npcap_status = self._detect_npcap()
        info_items.append(("Npcap", npcap_status))

        # Detectar engine
        engine_status = self._detect_engine()
        info_items.append(("Motor C++", engine_status))

        for label_text, value_text in info_items:
            row = QHBoxLayout()
            row.setSpacing(12)

            lbl = QLabel(label_text)
            lbl.setObjectName("settingsInfoLabel")
            lbl.setFixedWidth(120)
            row.addWidget(lbl)

            val = QLabel(value_text)
            val.setObjectName("settingsInfoValue")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(val)
            row.addStretch()

            info_layout.addLayout(row)

        layout.addWidget(group)
        layout.addStretch()
        return page

    # ───────────────────────────────────────────────────────────
    #  Helpers UI
    # ───────────────────────────────────────────────────────────

    @staticmethod
    def _section_title(title: str, subtitle: str) -> QWidget:
        """Crea un encabezado de sección con título y subtítulo."""
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 4)
        lay.setSpacing(2)

        t = QLabel(title)
        t.setObjectName("settingsSectionTitle")
        t.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lay.addWidget(t)

        s = QLabel(subtitle)
        s.setObjectName("settingsSectionSubtitle")
        lay.addWidget(s)

        return widget

    def _switch_page(self, index: int):
        """Cambia la página activa de la sidebar."""
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)
        self._stack.setCurrentIndex(index)

    # ───────────────────────────────────────────────────────────
    #  Detección de sistema
    # ───────────────────────────────────────────────────────────

    @staticmethod
    def _detect_npcap() -> str:
        """Detecta si Npcap está instalado."""
        npcap_dir = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "Npcap"
        if npcap_dir.exists():
            # Buscar versión en el registro o archivo
            ver_file = npcap_dir / "version.txt"
            if ver_file.exists():
                try:
                    return f"✓ Instalado ({ver_file.read_text().strip()})"
                except Exception:
                    pass
            return "✓ Instalado"
        return "✗ No detectado"

    @staticmethod
    def _detect_engine() -> str:
        """Detecta si el módulo nexus_engine está disponible."""
        try:
            from app import nexus_engine  # noqa: F401
            return "✓ nexus_engine cargado"
        except ImportError:
            return "✗ No disponible"

    # ───────────────────────────────────────────────────────────
    #  Validación
    # ───────────────────────────────────────────────────────────

    def _validate_export_dir(self, path_text: str):
        """Valida que el directorio exista y sea escribible."""
        if not path_text:
            self._dir_status.setText("")
            self._dir_status.setObjectName("settingsDirStatus")
            return

        p = Path(path_text)
        if p.is_dir() and os.access(str(p), os.W_OK):
            self._dir_status.setText("✓ Directorio válido y con permisos de escritura")
            self._dir_status.setObjectName("settingsDirOk")
        elif p.is_dir():
            self._dir_status.setText("⚠ Directorio existe pero sin permisos de escritura")
            self._dir_status.setObjectName("settingsDirWarn")
        else:
            self._dir_status.setText("✗ Directorio no encontrado")
            self._dir_status.setObjectName("settingsDirError")

        # Forzar re-estilización
        self._dir_status.style().unpolish(self._dir_status)
        self._dir_status.style().polish(self._dir_status)

    def _browse_export_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de capturas"
        )
        if directory:
            self._export_dir.setText(directory)

    # ───────────────────────────────────────────────────────────
    #  Tema
    # ───────────────────────────────────────────────────────────

    def _on_theme_changed(self, theme_text: str):
        """Aplica el tema SOLO al diálogo como preview (no toca la app global)."""
        theme_file = "light" if "Light Mode" in theme_text else "dark"
        # Cargar el contenido del tema sin aplicarlo a la QApplication
        from app.main import _load_theme_content
        theme_content = _load_theme_content(theme_file)
        self.setStyleSheet(theme_content)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        self.repaint()

    # ───────────────────────────────────────────────────────────
    #  Persistencia
    # ───────────────────────────────────────────────────────────

    def get_settings(self) -> dict:
        """Devuelve la configuración actual."""
        return {
            'theme': self._theme_combo.currentText(),
            'buffer_size': self._buffer_size_spin.value(),
            'snap_len': self._snap_len_spin.value(),
            'promiscuous': self._promiscuous_check.isChecked(),
            'export_dir': self._export_dir.text(),
        }

    def _load_settings(self):
        """Carga la configuración desde QSettings o usa defaults."""
        theme = self._settings.value('theme', self.DEFAULTS['theme'])
        idx = self._theme_combo.findText(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)

        self._buffer_size_spin.setValue(
            int(self._settings.value('buffer_size', self.DEFAULTS['buffer_size']))
        )
        self._snap_len_spin.setValue(
            int(self._settings.value('snap_len', self.DEFAULTS['snap_len']))
        )

        promisc = self._settings.value('promiscuous', self.DEFAULTS['promiscuous'], type=bool)
        self._promiscuous_check.setChecked(promisc)

        self._export_dir.setText(
            self._settings.value('export_dir', self.DEFAULTS['export_dir'])
        )

    def _reset_defaults(self):
        """Restablece todos los controles a los valores predeterminados."""
        idx = self._theme_combo.findText(self.DEFAULTS['theme'])
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._buffer_size_spin.setValue(self.DEFAULTS['buffer_size'])
        self._snap_len_spin.setValue(self.DEFAULTS['snap_len'])
        self._promiscuous_check.setChecked(self.DEFAULTS['promiscuous'])
        self._export_dir.setText(self.DEFAULTS['export_dir'])

    def accept(self):
        """Guarda la configuración y cierra."""
        conf = self.get_settings()
        for k, v in conf.items():
            self._settings.setValue(k, v)
        super().accept()


