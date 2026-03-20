"""
main_window.py — Ventana principal de NexusSniff.

Diseño premium con sidebar vertical, área central con transiciones
suaves, y soporte completo de temas dark/light sin colores hardcodeados.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QStatusBar,
    QFrame, QSizePolicy, QApplication, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient, QPen, QBrush
import os
from pathlib import Path

from app.ui.capture_panel import CapturePanel
from app.ui.stats_panel import StatsPanel
from app.ui.settings_dialog import SettingsDialog
from app.ui.icons import create_vector_icon
from PyQt6.QtCore import QSettings




class SidebarButton(QPushButton):
    """Botón de la sidebar con icono vectorial arriba y label pequeño debajo."""

    def __init__(self, icon: QIcon, label_text: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarButton")
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(64, 60)
        self.setIcon(icon)
        self.setIconSize(QSize(22, 22))

        # Layout interno: icono arriba (gestionado por el propio QPushButton), label abajo
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 24, 0, 4)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)

        text_lbl = QLabel(label_text)
        text_lbl.setObjectName("sidebarButtonLabel")
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_lbl.setFont(QFont("Segoe UI", 8))
        layout.addWidget(text_lbl)


class Sidebar(QWidget):
    """Barra lateral izquierda (Sidebar) vertical que provee navegación 
    entre las diferentes vistas principales. Utiliza iconos vectoriales 
    estilizados y etiquetas inferiores auto-ajustables.
    """

    SIDEBAR_WIDTH = 80

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(self.SIDEBAR_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo vectorial
        logo_container = QWidget()
        logo_container.setObjectName("sidebarLogoContainer")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 4, 0, 4)
        logo_layout.setSpacing(0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._logo_widget = QLabel()
        logo_path = Path(__file__).parent.parent / "resources" / "icons" / "logo_icon.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._logo_widget.setPixmap(pixmap)
        logo_layout.addWidget(self._logo_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_container)

        layout.addSpacing(8)

        # Separador superior
        sep_top = QFrame()
        sep_top.setObjectName("sidebarSeparator")
        sep_top.setFixedHeight(1)
        layout.addWidget(sep_top)

        layout.addSpacing(6)

        # Botones de navegación
        self.buttons = []

        self.dashboard_btn = SidebarButton(
            create_vector_icon("dashboard", "#c8d0e0", 22), "Stats", "Dashboard"
        )
        self.buttons.append(self.dashboard_btn)
        layout.addWidget(self.dashboard_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.capture_btn = SidebarButton(
            create_vector_icon("capture", "#c8d0e0", 22), "Captura", "Captura en Vivo"
        )
        self.buttons.append(self.capture_btn)
        layout.addWidget(self.capture_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # Separador inferior
        sep_bottom = QFrame()
        sep_bottom.setObjectName("sidebarSeparator")
        sep_bottom.setFixedHeight(1)
        layout.addWidget(sep_bottom)

        layout.addSpacing(6)

        # Botón de configuración
        self.settings_btn = SidebarButton(
            create_vector_icon("settings", "#c8d0e0", 22), "Config", "Configuración"
        )
        self.buttons.append(self.settings_btn)
        layout.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_active(self, button: SidebarButton):
        """Marca de manera exclusiva (estilo radio-button lógico) un botón en el menú izquierdo.
        
        Args:
            button (SidebarButton): Referencia al Widget de botón a marcar activo.
        """
        for btn in self.buttons:
            btn.setChecked(btn == button)


class MainWindow(QMainWindow):
    """Frame y ventana principal de la interfaz de NexusSniff (`QApplication`).
    
    Gestiona la orquestación del Sidebar, las pantallas apiladas (Dashboard, Captura)
    y barra de estado utilizando widgets dinámicos y transiciones con animaciones (fade).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NexusSniff — Network Analyzer")
        self.setMinimumSize(1200, 800)
        self.resize(1440, 900)

        # Establecer el icono de la ventana con el logo recortado (sin fondo)
        icon_path = Path(__file__).parent.parent / "resources" / "icons" / "logo_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._setup_ui()
        self._setup_statusbar()
        self._setup_connections()

        # Timer para actualizar la barra de estado
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(1000)
        self._status_timer.timeout.connect(self._update_status_time)
        self._status_timer.start()

        # Mostrar el panel de captura por defecto
        self._sidebar.capture_btn.setChecked(True)
        self._show_capture_panel()

    def _setup_ui(self):
        """Configura la interfaz principal."""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──
        self._sidebar = Sidebar()
        main_layout.addWidget(self._sidebar)

        # ── Separador vertical ──
        v_separator = QFrame()
        v_separator.setObjectName("verticalSeparator")
        v_separator.setFixedWidth(1)
        main_layout.addWidget(v_separator)

        # ── Área central ──
        content_area = QWidget()
        content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(8)

        app_title = QLabel("NexusSniff")
        app_title.setObjectName("headerTitle")
        app_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        header_layout.addWidget(app_title)

        self._header_subtitle = QLabel("Network Analyzer")
        self._header_subtitle.setObjectName("headerSubtitle")
        header_layout.addWidget(self._header_subtitle)

        header_layout.addStretch()

        # Indicador de estado
        self._status_indicator = QLabel("● Idle")
        self._status_indicator.setObjectName("statusIndicatorIdle")
        header_layout.addWidget(self._status_indicator)

        content_layout.addWidget(header)

        # ── Stacked widget para paneles ──
        self._stack = QStackedWidget()
        self._stack.setObjectName("mainStack")

        # Panel 0: Dashboard/Stats
        self._stats_panel = StatsPanel()
        self._stack.addWidget(self._stats_panel)

        # Panel 1: Captura
        self._capture_panel = CapturePanel()
        self._capture_panel.stats_updated.connect(self._stats_panel.update_stats)
        self._stack.addWidget(self._capture_panel)

        content_layout.addWidget(self._stack, 1)
        main_layout.addWidget(content_area, 1)

        # Efecto de opacidad para transición suave
        self._opacity_effect = QGraphicsOpacityEffect(self._stack)
        self._stack.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_anim.finished.connect(self._on_fade_finished)
        self._pending_index = -1

    def _fade_to(self, index: int):
        """Transición con fade al switchear paneles."""
        if self._stack.currentIndex() == index:
            return
        self._pending_index = index
        self._fade_anim.stop()
        # Desconectar señal finished para evitar conexiones múltiples
        try:
            self._fade_anim.finished.disconnect()
        except TypeError:
            pass
        self._fade_anim.finished.connect(self._on_fade_finished)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def _on_fade_finished(self):
        """Callback cuando el fade out termina — hace el switch y fade in."""
        if self._pending_index >= 0:
            self._stack.setCurrentIndex(self._pending_index)
            self._pending_index = -1
            try:
                self._fade_anim.finished.disconnect()
            except TypeError:
                pass
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()

    def _create_status_widget(self, icon_name: str, initial_text: str, object_name: str):
        """Creates a composite widget with an icon and a label for the statusbar."""
        container = QWidget()
        container.setObjectName("statusItemContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(6)
        
        icon_lbl = QLabel()
        icon_lbl.setObjectName("statusIconLabel")
        icon_lbl.setPixmap(create_vector_icon(icon_name, "#5a6478", 14).pixmap(14, 14))
        layout.addWidget(icon_lbl)
        
        text_lbl = QLabel(initial_text)
        text_lbl.setObjectName(object_name)
        layout.addWidget(text_lbl)
        return container, text_lbl

    def _create_status_divider(self):
        """Crea un separador vertical estilizado para la barra de estado."""
        divider = QFrame()
        divider.setObjectName("statusBarDivider")
        divider.setFixedWidth(1)
        divider.setFixedHeight(18)
        return divider

    def _setup_statusbar(self):
        """Configura la barra de estado inferior."""
        statusbar = QStatusBar()
        statusbar.setObjectName("mainStatusBar")
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)

        # Usar widgets compuestos con iconos y dividers estilizados
        self._status_packets_container, self._status_packets = self._create_status_widget("dashboard", "Paquetes: 0", "statusActive")
        statusbar.addWidget(self._status_packets_container)

        statusbar.addWidget(self._create_status_divider())

        self._status_bytes_container, self._status_bytes = self._create_status_widget("folder", "Bytes: 0", "statusNormal")
        statusbar.addWidget(self._status_bytes_container)

        statusbar.addWidget(self._create_status_divider())

        self._status_pps_container, self._status_pps = self._create_status_widget("network", "0 pkt/s", "statusNormal")
        statusbar.addWidget(self._status_pps_container)

        # Versión a la derecha
        version_label = QLabel("NexusSniff v1.3.0")
        version_label.setObjectName("statusVersion")
        statusbar.addPermanentWidget(version_label)

    def _setup_connections(self):
        """Conecta las señales de la sidebar."""
        self._sidebar.dashboard_btn.clicked.connect(self._show_dashboard)
        self._sidebar.capture_btn.clicked.connect(self._show_capture_panel)
        self._sidebar.settings_btn.clicked.connect(self._show_settings)
        self._capture_panel.stats_updated.connect(self._update_statusbar)

    def _show_dashboard(self):
        """Muestra el panel de dashboard."""
        self._sidebar.set_active(self._sidebar.dashboard_btn)
        self._fade_to(0)
        self._header_subtitle.setText("Dashboard de Red")
        self._status_indicator.setObjectName("statusIndicatorInfo")
        self._status_indicator.setText("● Dashboard")
        self._refresh_indicator_style()

    def _show_capture_panel(self):
        """Muestra el panel de captura."""
        self._sidebar.set_active(self._sidebar.capture_btn)
        self._fade_to(1)
        self._header_subtitle.setText("Captura en Vivo")
        self._status_indicator.setObjectName("statusIndicatorCapture")
        self._status_indicator.setText("● Captura")
        self._refresh_indicator_style()

    def _refresh_indicator_style(self):
        """Fuerza actualización del estilo del indicador."""
        self._status_indicator.style().unpolish(self._status_indicator)
        self._status_indicator.style().polish(self._status_indicator)

    def _show_settings(self):
        """Muestra el diálogo de configuración."""
        from app.main import load_theme
        # Snapshot del tema antes de abrir para poder revertir al cancelar
        current_settings = QSettings("NexusSniff", "NexusSniff")
        theme_before = current_settings.value("theme", "Dark Mode (Nexus)")
        theme_file_before = "light" if "Light Mode" in theme_before else "dark"

        dialog = SettingsDialog(self)
        # Aplicar el stylesheet de la aplicación al dialog para garantizar el tema
        dialog.setStyleSheet(QApplication.instance().styleSheet())

        if dialog.exec():
            # Guardado — aplicar el nuevo tema a toda la aplicación
            new_settings = QSettings("NexusSniff", "NexusSniff")
            current_theme = new_settings.value("theme", "Dark Mode (Nexus)")
            theme_file = "light" if "Light Mode" in current_theme else "dark"
            load_theme(QApplication.instance(), theme_file)
        else:
            # Cancelado — restaurar el tema original en la app global
            load_theme(QApplication.instance(), theme_file_before)

    def _update_statusbar(self, stats: dict):
        """Actualiza la barra de estado con estadísticas."""
        self._status_packets.setText(f"Paquetes: {stats.get('total_packets', 0):,}")
        total_bytes = stats.get('total_bytes', 0)
        if total_bytes < 1024 * 1024:
            self._status_bytes.setText(f"Bytes: {total_bytes / 1024:.1f} KB")
        else:
            self._status_bytes.setText(f"Bytes: {total_bytes / (1024*1024):.1f} MB")
        self._status_pps.setText(f"{stats.get('packets_per_sec', 0):.0f} pkt/s")

    def _update_status_time(self):
        """Actualización periódica de la barra de estado."""
        pass

    def closeEvent(self, event):
        """Limpieza al cerrar la ventana."""
        self._capture_panel.cleanup()
        event.accept()
