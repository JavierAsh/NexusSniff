"""
capture_panel.py — Panel de captura de paquetes en vivo.

Panel principal con:
- Selector de interfaz de red
- Campo de filtro BPF
- Botones Iniciar/Detener
- Tabla de paquetes en tiempo real
- Splitter con detalle + hex view

Optimizaciones v1.1:
- scrollToBottom suspendido al seleccionar un paquete
- Corrección de _on_packet_selected para selección robusta
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView,
    QComboBox, QPushButton, QLabel, QFrame, QAbstractItemView,
    QHeaderView, QMessageBox, QMenu, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction

from app.core.packet_model import PacketTableModel
from app.core.capture_worker import CaptureWorker
from app.core.export_manager import ExportManager
from app.ui.detail_panel import DetailPanel
from app.ui.hex_view import HexView
from app.ui.filter_bar import FilterBar
from app.ui.icons import create_vector_icon


class InfoColumnDelegate(QStyledItemDelegate):
    """Delegate para aplicar fuente monospace a la columna de INFO."""
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        font = QFont("JetBrains Mono", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        option.font = font


class CapturePanel(QWidget):
    """Panel de captura en vivo con tabla, detalle y hex view."""

    stats_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capture_worker = None
        self._interfaces = []
        self._auto_scroll = True   # Controla el scroll automático
        self._selected_row = -1    # Fila actualmente seleccionada
        self._setup_ui()
        self._load_interfaces()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ══ Barra superior: interfaz + controles ══
        controls_frame = QFrame()
        controls_frame.setObjectName("panel")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(12)

        # Selector de interfaz
        iface_icon_label = QLabel()
        iface_icon_label.setPixmap(create_vector_icon("network", "#c8d0e0", 18).pixmap(18, 18))
        iface_icon_label.setFixedWidth(24)
        controls_layout.addWidget(iface_icon_label)
        iface_label = QLabel("Interfaz:")
        iface_label.setObjectName("ifaceLabel")
        controls_layout.addWidget(iface_label)

        self._interface_combo = QComboBox()
        self._interface_combo.setMinimumWidth(300)
        self._interface_combo.setMinimumHeight(36)
        controls_layout.addWidget(self._interface_combo, 1)

        # Botón Iniciar
        self._start_btn = QPushButton("Iniciar Captura")
        self._start_btn.setIcon(create_vector_icon("play", "#ffffff", 18))
        self._start_btn.setObjectName("successButton")
        self._start_btn.setMinimumHeight(36)
        self._start_btn.setMinimumWidth(160)
        self._start_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._start_btn.clicked.connect(self._start_capture)
        controls_layout.addWidget(self._start_btn)

        # Botón Detener
        self._stop_btn = QPushButton("Detener")
        self._stop_btn.setIcon(create_vector_icon("stop", "#ffffff", 18))
        self._stop_btn.setObjectName("dangerButton")
        self._stop_btn.setMinimumHeight(36)
        self._stop_btn.setMinimumWidth(120)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_capture)
        controls_layout.addWidget(self._stop_btn)

        # Botón Limpiar
        self._clear_btn = QPushButton("Limpiar")
        self._clear_btn.setIcon(create_vector_icon("trash", "#c8d0e0", 18))
        self._clear_btn.setMinimumHeight(36)
        self._clear_btn.setEnabled(False)  # Deshabilitado inicialmente
        self._clear_btn.clicked.connect(self._clear_packets)
        controls_layout.addWidget(self._clear_btn)

        # Botón Exportar
        self._export_btn = QPushButton("Exportar")
        self._export_btn.setIcon(create_vector_icon("folder", "#c8d0e0", 18))
        self._export_btn.setMinimumHeight(36)
        self._export_btn.setEnabled(False)  # Deshabilitado inicialmente
        self._export_btn.clicked.connect(self._export_capture)
        controls_layout.addWidget(self._export_btn)

        layout.addWidget(controls_frame)

        # ══ Barra de filtros ══
        self._filter_bar = FilterBar()
        self._filter_bar.filter_applied.connect(self._on_filter_applied)
        self._filter_bar.filter_cleared.connect(self._on_filter_cleared)
        layout.addWidget(self._filter_bar)

        # ══ Estado de captura activa ══
        status_row = QHBoxLayout()
        self._packet_count_label = QLabel("0 paquetes capturados")
        self._packet_count_label.setObjectName("packetCountLabel")
        status_row.addWidget(self._packet_count_label)

        status_row.addStretch()

        # ── Estado de captura (Badge estable a la izquierda del botón de scroll) ──
        self._capture_active_badge = QLabel("● CAPTURANDO")
        self._capture_active_badge.setObjectName("captureActiveBadge")
        # Mantener espacio ocupado (stable layout) pero ocultar visualmente al inicio
        self._capture_active_badge.setStyleSheet("color: transparent; background: transparent; border: none;")
        self._capture_active_badge.setFixedWidth(130)
        self._capture_active_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._capture_active_badge.setProperty("dim", False)
        status_row.addWidget(self._capture_active_badge)

        status_row.addSpacing(12) # Separación clara entre indicador y botón

        # ── Botón de scroll automático ──
        self._auto_scroll_btn = QPushButton("Auto-scroll: ON")
        self._auto_scroll_btn.setIcon(create_vector_icon("arrow_down", "#c8d0e0", 16))
        self._auto_scroll_btn.setObjectName("autoScrollBtn")
        self._auto_scroll_btn.setMinimumHeight(28)
        self._auto_scroll_btn.setMaximumHeight(28)
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
        status_row.addWidget(self._auto_scroll_btn)

        layout.addLayout(status_row)

        # Timer para animar el badge de captura
        self._badge_timer = QTimer(self)
        self._badge_timer.setInterval(600)
        self._badge_timer.timeout.connect(self._pulse_badge)

        # ══ Splitter principal ══
        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setChildrenCollapsible(False)

        # ── Tabla de paquetes ──
        self._packet_model = PacketTableModel()
        self._table_view = QTableView()
        self._table_view.setModel(self._packet_model)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table_view.verticalHeader().setVisible(False)
        self._table_view.setSortingEnabled(False)
        self._table_view.setShowGrid(False)

        # Configurar anchos de columnas
        header = self._table_view.horizontalHeader()
        from app.core.packet_model import COLUMNS
        for i, (_, _, width) in enumerate(COLUMNS):
            if i == len(COLUMNS) - 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                self._table_view.setItemDelegateForColumn(i, InfoColumnDelegate(self._table_view))
            else:
                self._table_view.setColumnWidth(i, width)

        # Conectar la selección de manera robusta
        self._table_view.selectionModel().selectionChanged.connect(self._on_packet_selected)
        self._table_view.clicked.connect(self._on_table_clicked)
        self._splitter.addWidget(self._table_view)

        # ── Panel inferior: Detalle + HexView ──
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.setChildrenCollapsible(False)

        self._detail_panel = DetailPanel()
        self._detail_panel.field_selected.connect(self._on_field_selected)
        bottom_splitter.addWidget(self._detail_panel)

        self._hex_view = HexView()
        bottom_splitter.addWidget(self._hex_view)

        bottom_splitter.setSizes([400, 400])
        self._splitter.addWidget(bottom_splitter)

        self._splitter.setSizes([400, 300])
        layout.addWidget(self._splitter, 1)

    def _update_buttons(self):
        """Actualiza el estado habilitado de los botones según si hay paquetes."""
        has_packets = self._packet_model.packet_count() > 0
        self._clear_btn.setEnabled(has_packets)
        self._export_btn.setEnabled(has_packets)

    def _load_interfaces(self):
        """Carga las interfaces de red disponibles."""
        try:
            import app.nexus_engine as nexus_engine
            self._interfaces = nexus_engine.PacketCapturer.list_interfaces()
            for iface in self._interfaces:
                desc = iface.description
                addrs = ", ".join(iface.addresses) if iface.addresses else "sin IP"
                self._interface_combo.addItem(f"{desc}  ({addrs})", iface.name)
        except ImportError:
            # Motor no compilado, agregar interfaces de ejemplo
            self._interface_combo.addItem(
                "⚠ Motor C++ no compilado — usar datos de ejemplo",
                "__demo__"
            )
        except Exception as e:
            self._interface_combo.addItem(f"Error: {e}", "__error__")

    def _create_worker(self, interface_name: str, bpf_filter: str):
        """Crea y conecta un CaptureWorker. Método centralizado para evitar duplicación."""
        self._capture_worker = CaptureWorker()
        self._capture_worker.configure(interface_name, bpf_filter)
        self._capture_worker.new_packets.connect(self._on_new_packets)
        self._capture_worker.stats_updated.connect(self._on_stats_updated)
        self._capture_worker.capture_error.connect(self._on_capture_error)
        self._capture_worker.capture_started.connect(self._on_capture_started)
        self._capture_worker.capture_stopped.connect(self._on_capture_stopped)
        self._capture_worker.start()

    def _start_capture(self):
        """Inicia la captura de paquetes."""
        if self._interface_combo.currentData() in ("__demo__", "__error__"):
            QMessageBox.warning(
                self, "Motor no disponible",
                "El motor C++ (nexus_engine.pyd) no está compilado.\n"
                "Ejecuta: cmake -B build -S . && cmake --build build --config Release"
            )
            return

        interface_name = self._interface_combo.currentData()
        bpf_filter = self._filter_bar.get_filter()
        self._create_worker(interface_name, bpf_filter)

    def _stop_capture(self):
        """Detiene la captura."""
        if self._capture_worker:
            self._stop_btn.setEnabled(False)
            self._capture_worker.stop_capture()

    def _clear_packets(self):
        """Limpia la tabla de paquetes."""
        self._packet_model.clear()
        self._detail_panel.clear()
        self._hex_view.clear()
        self._packet_count_label.setText("0 paquetes capturados")
        self._selected_row = -1

        # Actualizar estado de botones
        self._update_buttons()

    def _export_capture(self):
        """Exporta los paquetes capturados con opciones de formato."""
        from app.core.capture_worker import packet_to_dict

        raw_packets = [
            self._packet_model.get_packet(i)
            for i in range(self._packet_model.packet_count())
        ]
        if not raw_packets:
            QMessageBox.information(self, "Sin datos", "No hay paquetes para exportar.")
            return

        # Convertir PacketData C++ a dicts bajo demanda (solo al exportar)
        packets = [
            packet_to_dict(p) if not isinstance(p, dict) else p
            for p in raw_packets
        ]
        if not packets:
            QMessageBox.information(self, "Sin datos", "No hay paquetes para exportar.")
            return

        menu = QMenu(self)
        menu.setObjectName("exportMenu")
        act_pcap  = menu.addAction(create_vector_icon("network", "#c8d0e0", 18), "PCAP (.pcap) — Compatible Wireshark")
        menu.addSeparator()
        act_excel = menu.addAction(create_vector_icon("dashboard", "#c8d0e0", 18), "Excel (.xlsx) — Con hojas separadas")
        act_csv   = menu.addAction(create_vector_icon("folder", "#c8d0e0", 18), "CSV — Tabla plana")
        act_json  = menu.addAction(create_vector_icon("folder", "#c8d0e0", 18), "JSON — Raw completo")

        sender_btn = self._export_btn
        pos = sender_btn.mapToGlobal(sender_btn.rect().bottomLeft())
        chosen = menu.exec(pos)

        stats = getattr(self, '_last_stats', {})
        if chosen == act_pcap:
            ExportManager.export_pcap(packets, self)
        elif chosen == act_excel:
            ExportManager.export_excel(packets, stats, self)
        elif chosen == act_csv:
            ExportManager.export_csv(packets, self)
        elif chosen == act_json:
            ExportManager.export_json(packets, self)

    def _toggle_auto_scroll(self, checked: bool):
        """Activa o desactiva el scroll automático y actualiza el botón."""
        # Evitar ciclos o actualizaciones innecesarias si ya está en ese estado
        # (aunque el botón ya lo controla por ser checkable, esto es más robusto)
        self._auto_scroll = checked
        self._auto_scroll_btn.setChecked(checked)
        label = "Auto-scroll: ON" if checked else "Auto-scroll: OFF"
        self._auto_scroll_btn.setText(label)
        
        # Al reactivar el autoscroll, liberar selección para que se mueva con nuevos paquetes
        if checked:
            self._selected_row = -1
            # Opcional: limpiar selección de la tabla para que se vea claro el seguimiento
            self._table_view.clearSelection()

    def _on_filter_applied(self, expression: str):
        """Aplica el filtro BPF reiniciando la captura con la nueva expresión."""
        if self._capture_worker and self._capture_worker.isRunning():
            self._pending_filter = expression
            self._capture_worker.capture_stopped.connect(self._on_restart_after_stop)
            self._stop_capture()
        # Si no hay captura activa, el filtro se usará en la próxima captura

    def _on_filter_cleared(self):
        """Limpia el filtro y reinicia la captura sin filtro si estaba activa."""
        if self._capture_worker and self._capture_worker.isRunning():
            self._pending_filter = ""
            self._capture_worker.capture_stopped.connect(self._on_restart_after_stop)
            self._stop_capture()

    def _on_restart_after_stop(self):
        """Reinicia la captura tras recibir la señal capture_stopped."""
        bpf_filter = getattr(self, '_pending_filter', '')
        self._pending_filter = None
        interface_name = self._interface_combo.currentData()
        if interface_name in ("__demo__", "__error__"):
            return
        self._create_worker(interface_name, bpf_filter)

    def _on_new_packets(self, packets: list):
        """Maneja la llegada de nuevos paquetes."""
        self._packet_model.add_packets(packets)
        count = self._packet_model.packet_count()
        self._packet_count_label.setText(f"{count:,} paquetes capturados")

        # Actualizar estado de botones
        self._update_buttons()

        # Solo hacer scroll si auto-scroll está activado
        if self._auto_scroll:
            self._table_view.scrollToBottom()

    def _on_stats_updated(self, stats: dict):
        """Retransmite las estadísticas al panel de stats."""
        self._last_stats = stats
        self.stats_updated.emit(stats)

    def _on_capture_error(self, error: str):
        """Maneja errores de captura."""
        QMessageBox.critical(self, "Error de Captura", error)
        self._on_capture_stopped()

    def _on_capture_started(self):
        """UI actualizada al iniciar captura."""
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._interface_combo.setEnabled(False)
        
        # Resetear estilo al default del QSS para que sea visible
        self._capture_active_badge.setStyleSheet("")
        self._capture_active_badge.setProperty("dim", False)
        self._badge_timer.start()
        self._last_stats = {}

    def _on_capture_stopped(self):
        """UI actualizada al detener captura."""
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._interface_combo.setEnabled(True)
        
        # Ocultar visualmente pero mantener en layout para evitar saltos
        self._capture_active_badge.setStyleSheet("color: transparent; background: transparent; border: none;")
        self._badge_timer.stop()

    def _pulse_badge(self):
        """Alterna el estilo del badge para efecto de pulso sin cambiar visibilidad (evita saltos)."""
        is_dim = self._capture_active_badge.property("dim")
        dim = not is_dim
        self._capture_active_badge.setProperty("dim", dim)
        
        # Debemos repetir el diseño base (radius, padding) para no perderlo al sobreescribir con setStyleSheet
        if dim:
            # Estado atenuado — Manteniendo el diseño "píldora"
            self._capture_active_badge.setStyleSheet(
                "color: rgba(16, 185, 129, 0.4); "
                "background: rgba(16, 185, 129, 0.05); "
                "border: 1px solid rgba(16, 185, 129, 0.1); "
                "border-radius: 10px; padding: 2px 10px;"
            )
        else:
            # Estado brillante (revertir al QSS base del archivo dark/light.qss)
            self._capture_active_badge.setStyleSheet("")

        # Forzar re-lectura del estilo
        self._capture_active_badge.style().unpolish(self._capture_active_badge)
        self._capture_active_badge.style().polish(self._capture_active_badge)
        self._capture_active_badge.update()

    def _on_table_clicked(self, index):
        """Al hacer clic en la tabla, pausar autoscroll si estaba activo."""
        if index.isValid():
            if self._auto_scroll:
                self._toggle_auto_scroll(False)
            self._show_packet_at_row(index.row())

    def _on_packet_selected(self, selected, deselected):
        """Muestra el detalle del paquete seleccionado y detiene autoscroll (clic o teclado)."""
        indexes = selected.indexes()
        if not indexes:
            return
            
        row = indexes[0].row()
        # Si el usuario navega (teclado) o selecciona, pausamos autoscroll para que pueda leer cómodamente
        if self._auto_scroll:
            self._toggle_auto_scroll(False)
            
        self._show_packet_at_row(row)

    def _show_packet_at_row(self, row: int):
        """Muestra el detalle de un paquete dado su índice de fila."""
        if row < 0:
            return
        packet = self._packet_model.get_packet(row)
        if packet is None:
            return
        self._selected_row = row

        # Convertir PacketData C++ a dict para detail_panel si es necesario
        if isinstance(packet, dict):
            packet_dict = packet
        else:
            from app.core.capture_worker import packet_to_dict
            packet_dict = packet_to_dict(packet)

        self._detail_panel.set_packet(packet_dict)

        raw_data = packet_dict.get('raw_data', b'')
        if isinstance(raw_data, (bytes, bytearray)) and raw_data:
            self._hex_view.set_data(bytes(raw_data))
        else:
            self._hex_view.clear()

    def _on_field_selected(self, start: int, end: int, layer: str):
        """Resalta bytes en la vista hex según la capa seleccionada."""
        self._hex_view.highlight_range(start, end, layer)

    def cleanup(self):
        """Limpieza al cerrar."""
        if self._capture_worker and self._capture_worker.isRunning():
            self._capture_worker.stop_capture()
            self._capture_worker.wait(3000)
