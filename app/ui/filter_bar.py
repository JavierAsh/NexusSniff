"""
filter_bar.py — Barra de filtros BPF con preajustes de protocolo.

Ofrece un QComboBox editable con filtros comunes predefinidos
agrupados por categoría, permitiendo también tipeo libre de
expresiones BPF personalizadas.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont
from app.ui.icons import create_vector_icon


# ════════════════════════════════════════════════
#  Preajustes de filtro  (valor, label visible)
# ════════════════════════════════════════════════
FILTER_PRESETS = [
    # --- Placeholder ---
    ("",                          "Sin filtro (capturar todo)"),

    # --- Protocolos ---
    ("tcp",                       "TCP — Solo paquetes TCP"),
    ("udp",                       "UDP — Solo paquetes UDP"),
    ("icmp",                      "ICMP — Solo paquetes ICMP"),
    ("arp",                       "ARP — Solo paquetes ARP"),
    ("ip",                        "IPv4 — Paquetes IPv4"),
    ("ip6",                       "IPv6 — Paquetes IPv6"),
    ("vlan",                      "VLAN — Paquetes con VLAN"),

    # --- Aplicaciones comunes ---
    ("tcp port 80",               "HTTP — Puerto 80"),
    ("tcp port 443",              "HTTPS — Puerto 443"),
    ("tcp port 53 or udp port 53","DNS — Puerto 53 (TCP/UDP)"),
    ("tcp port 22",               "SSH — Puerto 22"),
    ("tcp port 21",               "FTP — Puerto 21"),
    ("tcp port 25",               "SMTP — Puerto 25"),
    ("udp port 67 or udp port 68","DHCP — Puertos 67/68 (UDP)"),

    # --- Tamaño ---
    ("greater 1500",              "Paquetes grandes (> 1500 bytes)"),
    ("less 64",                   "Paquetes pequeños (< 64 bytes)"),
    ("greater 1000",              "Paquetes > 1 KB"),
    ("less 100",                  "Paquetes < 100 bytes"),
]


class FilterBar(QWidget):
    """Barra de filtros BPF con preajustes prácticos."""

    filter_applied = pyqtSignal(str)   # Emitida con la expresión BPF
    filter_cleared = pyqtSignal()      # Emitida al limpiar el filtro

    def __init__(self, parent=None):
        super().__init__(parent)
        self._applied_filter = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Icono de filtro (vectorial)
        icon_label = QLabel()
        icon_label.setPixmap(
            create_vector_icon("filter", "#c8d0e0", 18).pixmap(18, 18)
        )
        icon_label.setFixedWidth(24)
        layout.addWidget(icon_label)

        # ComboBox (no editable) para mostrar opciones claramente
        self._filter_combo = QComboBox()
        self._filter_combo.setEditable(False)
        self._filter_combo.setMinimumHeight(36)
        self._filter_combo.setFont(QFont("JetBrains Mono", 11))
        self._filter_combo.setToolTip("Selecciona un filtro de la lista")

        # Cargar preajustes
        for bpf_expr, display_label in FILTER_PRESETS:
            self._filter_combo.addItem(display_label, bpf_expr)

        layout.addWidget(self._filter_combo, 1)

        # Botón aplicar
        self._apply_btn = QPushButton("Aplicar")
        self._apply_btn.setObjectName("primaryButton")
        self._apply_btn.setFixedWidth(90)
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._apply_filter)
        layout.addWidget(self._apply_btn)

        # Connect combo box change
        self._filter_combo.currentIndexChanged.connect(self._on_combo_changed)

        # Botón limpiar (X)
        self._clear_btn = QPushButton()
        self._clear_btn.setObjectName("clearFilterBtn")
        self._clear_btn.setIcon(create_vector_icon("clear_x", "#8892a8", 14))
        self._clear_btn.setFixedSize(36, 36)
        self._clear_btn.setToolTip("Limpiar filtro")
        self._clear_btn.clicked.connect(self._clear_filter)
        layout.addWidget(self._clear_btn)

    def _on_combo_changed(self):
        """Habilita o deshabilita el botón aplicar según si hay cambios."""
        current_expr = self.get_filter()
        self._apply_btn.setEnabled(current_expr != self._applied_filter)

    def _apply_filter(self):
        """Aplica el filtro actual."""
        expression = self.get_filter()
        self._applied_filter = expression
        self._apply_btn.setEnabled(False)
        self._clear_btn.setEnabled(bool(expression))
        self.filter_applied.emit(expression)

    def _clear_filter(self):
        """Limpia el filtro."""
        if self._applied_filter != "":
            self._applied_filter = ""
            self.filter_cleared.emit()
        self._filter_combo.setCurrentIndex(0)
        self._clear_btn.setEnabled(False)

    def get_filter(self) -> str:
        """Devuelve la expresión de filtro actual."""
        return self._filter_combo.currentData() or ""
