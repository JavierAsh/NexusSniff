"""
stats_panel.py — Dashboard de estadísticas en tiempo real.

Cards de resumen + distribución de protocolos.
Totalmente compatible con temas dark/light via QSS objectNames.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QPolygonF, QPainterPath
from typing import Dict
from collections import deque

from app.ui.icons import CubeIconWidget, DiskIconWidget, PulseIconWidget, AlertIconWidget, MetricIconWidget


class SparklineWidget(QWidget):
    """Mini gráfico de líneas (sparkline) para mostrar tendencia."""
    def __init__(self, parent=None, color="#0db9f2"):
        super().__init__(parent)
        self.setMinimumSize(80, 24)
        self.setMaximumHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._data = deque(maxlen=30)
        for _ in range(30):
            self._data.append(0.0)
        self._color = QColor(color)

    def add_value(self, val: float):
        self._data.append(val)
        self.update()

    def set_color(self, color_hex: str):
        self._color = QColor(color_hex)
        self.update()

    def clear_data(self):
        for _ in range(30):
            self._data.append(0.0)
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        max_val = max(self._data)
        min_val = min(self._data)
        range_val = max(max_val - min_val, 1.0)
        
        w, h = self.width(), self.height()
        step = w / (len(self._data) - 1)
        
        path = QPainterPath()
        
        for i, val in enumerate(self._data):
            x = i * step
            # Padding for line thickness
            y = h - 2 - ((val - min_val) / range_val) * (h - 4)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
                
        # Draw gradient below
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()
        fill_color = QColor(self._color)
        fill_color.setAlpha(30)
        painter.fillPath(fill_path, fill_color)
                
        pen = QPen(self._color, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.end()


class StatCard(QFrame):
    """Card individual de estadística — colores controlados por QSS."""

    def __init__(self, title: str, icon_widget: QWidget = None, accent: bool = False, sparkline: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 14, 16, 14)

        # Título con icono
        header = QHBoxLayout()
        if icon_widget:
            icon_widget.setObjectName("statIconWidget")
            header.addWidget(icon_widget)

        title_label = QLabel(title)
        title_label.setObjectName("statLabel")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # Valor y sub-valor en layout horizontal para incluir sparkline a la derecha
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0,0,0,0)
        
        val_sub_layout = QVBoxLayout()
        val_sub_layout.setContentsMargins(0,0,0,0)
        
        # Valor principal
        self._value_label = QLabel("0")
        self._value_label.setObjectName("statAccent" if accent else "statValue")
        val_sub_layout.addWidget(self._value_label)

        # Sub-valor
        self._sub_label = QLabel("")
        self._sub_label.setObjectName("statSubValue")
        val_sub_layout.addWidget(self._sub_label)
        
        body_layout.addLayout(val_sub_layout)
        
        self.sparkline = None
        if sparkline:
            self.sparkline = SparklineWidget(color="#0db9f2" if accent else "#10b981")
            body_layout.addWidget(self.sparkline, alignment=Qt.AlignmentFlag.AlignBottom)
            
        layout.addLayout(body_layout)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_sub_value(self, value: str):
        self._sub_label.setText(value)
        
    def add_sparkline_value(self, value: float):
        if self.sparkline:
            self.sparkline.add_value(value)
            
    def clear_sparkline(self):
        if self.sparkline:
            self.sparkline.clear_data()


class ProtocolBar(QFrame):
    """Barra visual de distribución de protocolo — tema-agnostic."""

    def __init__(self, name: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("protocolBarRow")
        self._name = name
        self._color = color
        self._percentage = 0.0
        self._count = 0
        self.setMinimumHeight(36)
        self.setMaximumHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Color dot semántico del protocolo
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")
        dot.setFixedWidth(16)
        layout.addWidget(dot)

        # Nombre del protocolo
        self._name_label = QLabel(name)
        self._name_label.setObjectName("protoNameLabel")
        self._name_label.setFixedWidth(64)
        layout.addWidget(self._name_label)

        # Barra de progreso visual
        self._bar_bg = QFrame()
        self._bar_bg.setObjectName("protoBarBg")
        self._bar_bg.setFixedHeight(6)
        self._bar_bg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._bar_fill = QFrame(self._bar_bg)
        self._bar_fill.setStyleSheet(
            f"background-color: {color}; border-radius: 3px; background: {color};"
        )
        self._bar_fill.setFixedHeight(6)
        self._bar_fill.setFixedWidth(0)

        layout.addWidget(self._bar_bg)

        # Porcentaje y conteo
        self._pct_label = QLabel("0%")
        self._pct_label.setObjectName("protoPctLabel")
        self._pct_label.setFixedWidth(44)
        self._pct_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._pct_label)

        self._count_label = QLabel("0")
        self._count_label.setObjectName("protoCountLabel")
        self._count_label.setFixedWidth(64)
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._count_label)

    def update_data(self, count: int, total: int):
        self._count = count
        self._percentage = (count / total * 100) if total > 0 else 0
        self._pct_label.setText(f"{self._percentage:.1f}%")
        self._count_label.setText(f"{count:,}")
        bar_width = int(self._bar_bg.width() * self._percentage / 100)
        self._bar_fill.setFixedWidth(max(bar_width, 0))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_bar_bg') and hasattr(self, '_bar_fill'):
            bar_width = int(self._bar_bg.width() * self._percentage / 100)
            self._bar_fill.setFixedWidth(max(bar_width, 0))


class StatsPanel(QWidget):
    """Dashboard de estadísticas en tiempo real."""

    PROTOCOL_COLORS = {
        'TCP':     '#007BFF',   # Azul vibrante
        'UDP':     '#2ECC71',   # Esmeralda
        'ICMP':    '#9B59B6',   # Púrpura (Otros/ICMP)
        'DNS':     '#f97316',
        'HTTP':    '#8b5cf6',
        'HTTPS':   '#F1C40F',   # Oro/Ámbar
        'ARP':     '#ec4899',
        'SSH':     '#ec4899',
        'Unknown': '#95A5A6',   # Gris frío
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statsPanel")
        self._protocol_bars: Dict[str, ProtocolBar] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── Título ──
        title_layout = QHBoxLayout()
        title = QLabel("Dashboard de Red")
        title.setObjectName("sectionTitle")
        title_layout.addWidget(title)

        subtitle = QLabel("Análisis de tráfico y distribución de protocolos en tiempo real")
        subtitle.setObjectName("sectionSubtitle")
        title_layout.addWidget(subtitle, 1)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # ── Cards de resumen ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        accent_color = "#0db9f2"

        self._total_packets_card = StatCard("PAQUETES TOTALES", CubeIconWidget(color=accent_color), accent=True, sparkline=True)
        cards_layout.addWidget(self._total_packets_card)

        self._total_bytes_card = StatCard("BYTES TOTALES", DiskIconWidget(color="#8892a8"))
        cards_layout.addWidget(self._total_bytes_card)

        self._pps_card = StatCard("PAQUETES/SEG", PulseIconWidget(color=accent_color), accent=True, sparkline=True)
        cards_layout.addWidget(self._pps_card)

        self._bps_card = StatCard("THROUGHPUT", MetricIconWidget(color="#8892a8"), sparkline=True)
        cards_layout.addWidget(self._bps_card)

        self._dropped_card = StatCard("PERDIDOS", AlertIconWidget(color="#f59e0b"))
        cards_layout.addWidget(self._dropped_card)

        layout.addLayout(cards_layout)

        # ── Distribución de protocolos ──
        proto_frame = QFrame()
        proto_frame.setObjectName("card")
        proto_layout = QVBoxLayout(proto_frame)
        proto_layout.setSpacing(4)
        proto_layout.setContentsMargins(16, 14, 16, 14)

        # Header de la card
        proto_header = QHBoxLayout()
        proto_title = QLabel("Distribución de Protocolos")
        proto_title.setObjectName("cardTitle")
        proto_header.addWidget(proto_title)
        proto_header.addStretch()

        # Column headers
        col_headers = QHBoxLayout()
        col_headers.addSpacing(92)  # dot + name space
        for text, width in [("—", 200), ("%", 44), ("Paquetes", 64)]:
            lbl = QLabel(text)
            lbl.setObjectName("protoColumnHeader")
            lbl.setFixedWidth(width if text != "—" else 200)
            col_headers.addWidget(lbl)

        proto_layout.addLayout(proto_header)
        proto_layout.addLayout(col_headers)

        sep = QFrame()
        sep.setObjectName("cardDivider")
        sep.setFixedHeight(1)
        proto_layout.addWidget(sep)

        self._proto_container = QVBoxLayout()
        self._proto_container.setSpacing(2)
        proto_layout.addLayout(self._proto_container)
        proto_layout.addStretch()

        layout.addWidget(proto_frame, 1)

    def update_stats(self, stats: Dict):
        """Actualiza las estadísticas con nuevos datos."""
        total_pkts = stats.get('total_packets', 0)
        total_bytes = stats.get('total_bytes', 0)
        pps = stats.get('packets_per_sec', 0.0)
        bps = stats.get('bytes_per_sec', 0.0)
        dropped = stats.get('dropped_packets', 0)

        self._total_packets_card.set_value(f"{total_pkts:,}")
        self._total_packets_card.add_sparkline_value(float(total_pkts))
        
        self._total_bytes_card.set_value(self._format_bytes(total_bytes))
        self._total_bytes_card.set_sub_value(f"{total_bytes:,} bytes")
        self._total_bytes_card.add_sparkline_value(float(total_bytes))
        
        self._pps_card.set_value(f"{pps:,.0f}")
        self._pps_card.add_sparkline_value(pps)
        
        self._bps_card.set_value(self._format_throughput(bps))
        self._bps_card.set_sub_value(f"{bps:,.0f} B/s")
        self._bps_card.add_sparkline_value(bps)
        
        self._dropped_card.set_value(f"{dropped:,}")

        proto_dist = stats.get('protocol_distribution', {})
        total = sum(proto_dist.values()) if proto_dist else 0
        sorted_protos = sorted(proto_dist.items(), key=lambda x: x[1], reverse=True)

        for proto_name, count in sorted_protos:
            if proto_name not in self._protocol_bars:
                color = self.PROTOCOL_COLORS.get(proto_name, '#475569')
                bar = ProtocolBar(proto_name, color)
                self._protocol_bars[proto_name] = bar
                self._proto_container.addWidget(bar)
            self._protocol_bars[proto_name].update_data(count, total)

    def clear(self):
        """Reinicia el dashboard."""
        self._total_packets_card.set_value("0")
        self._total_packets_card.clear_sparkline()
        self._total_bytes_card.set_value("0 B")
        self._total_bytes_card.clear_sparkline()
        self._pps_card.set_value("0")
        self._pps_card.clear_sparkline()
        self._bps_card.set_value("0 B/s")
        self._bps_card.clear_sparkline()
        self._dropped_card.set_value("0")
        for bar in self._protocol_bars.values():
            bar.update_data(0, 0)

    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"

    @staticmethod
    def _format_throughput(bps: float) -> str:
        if bps < 1024:
            return f"{bps:.0f} B/s"
        elif bps < 1024 * 1024:
            return f"{bps / 1024:.1f} KB/s"
        elif bps < 1024 * 1024 * 1024:
            return f"{bps / (1024 * 1024):.1f} MB/s"
        else:
            return f"{bps / (1024 * 1024 * 1024):.2f} GB/s"
