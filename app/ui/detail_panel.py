"""
detail_panel.py — Inspector de paquete con capas OSI expandibles.

Muestra las capas decodificadas de un paquete en un QTreeWidget
con badges de colores por capa, estilo premium sin colores hardcodeados.
Compatible con temas dark y light vía QSS objectNames.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QFrame
)
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any

from app.ui.icons import create_vector_icon


# Colores semánticos por capa (se mantienen en ambos temas, son de datos no de UI)
LAYER_COLORS = {
    'ethernet': '#ec4899',
    'ipv4':     '#0db9f2',
    'ipv6':     '#6366f1',
    'tcp':      '#007BFF',   # Azul Vibrante
    'udp':      '#2ECC71',   # Esmeralda
    'icmp':     '#9B59B6',   # Púrpura
    'arp':      '#f97316',
    'dns':      '#a855f7',
    'http':     '#8b5cf6',
    'payload':  '#64748b',
}

LAYER_ICONS = {
    'ethernet': '⬡',
    'ipv4':     '◉',
    'ipv6':     '◎',
    'tcp':      '▸',
    'udp':      '▸',
    'icmp':     '▸',
    'arp':      '▸',
    'dns':      '▸',
    'http':     '▸',
}


class DetailPanel(QWidget):
    """Panel de detalle de un paquete con capas OSI en TreeView premium."""

    field_selected = pyqtSignal(int, int, str)  # start_byte, end_byte, layer_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailPanelWidget")

        # Fuentes pre-creadas (evita recrearlas por cada paquete)
        self._bold_layer_font = QFont("Segoe UI", 11)
        self._bold_layer_font.setBold(True)
        self._mono_font = QFont("JetBrains Mono", 10)
        self._mono_font.setStyleHint(QFont.StyleHint.Monospace)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header del panel
        header = QWidget()
        header.setObjectName("detailPanelHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("⬡ Inspección de Paquete")
        title.setObjectName("panelHeaderTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._layer_count_label = QLabel("")
        self._layer_count_label.setObjectName("panelHeaderBadge")
        self._layer_count_label.setVisible(False)
        header_layout.addWidget(self._layer_count_label)

        layout.addWidget(header)

        # Container for Tree and Empty State
        from PyQt6.QtWidgets import QStackedWidget
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # TreeWidget usando objectName para QSS theming
        self._tree = QTreeWidget()
        self._tree.setObjectName("detailTree")
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(20)
        self._tree.setAnimated(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        
        self._stack.addWidget(self._tree)

        # Empty State
        empty_container = QWidget()
        empty_container.setObjectName("emptyStateContainer")
        empty_layout = QVBoxLayout(empty_container)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel()
        empty_icon.setPixmap(create_vector_icon("capture", "#8892a8", 48).pixmap(48, 48))
        empty_icon.setObjectName("emptyStateIcon")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_text = QLabel("Selecciona un paquete de la tabla\npara inspeccionar sus detalles")
        empty_text.setObjectName("emptyStateText")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_text)

        self._stack.addWidget(empty_container)
        self._stack.setCurrentIndex(1) # Start with empty state

    def set_packet(self, packet: Dict[str, Any]):
        """Muestra las capas de un paquete con badge coloridos por capa."""
        self._tree.clear()

        if not packet:
            self._layer_count_label.setText("")
            self._stack.setCurrentIndex(1) # Show empty state
            return

        self._stack.setCurrentIndex(0) # Show tree View

        layers_added = 0

        # ── Capa Ethernet ──
        if packet.get('has_ethernet'):
            layers_added += 1
            eth_item = QTreeWidgetItem(self._tree)
            src = packet.get('src_mac', '??:??:??:??:??:??')
            dst = packet.get('dst_mac', '??:??:??:??:??:??')
            eth_item.setText(0, f"⬡  Ethernet II   {src} → {dst}")
            eth_item.setForeground(0, QColor(LAYER_COLORS['ethernet']))
            eth_item.setData(0, Qt.ItemDataRole.UserRole, ('ethernet', 0, 14))
            eth_item.setFont(0, self._bold_layer_font)

            self._add_field(eth_item, "Destino MAC", dst)
            self._add_field(eth_item, "Origen MAC", src)
            eth_type = packet.get('ethernet', {}).get('ethertype', 0)
            if eth_type:
                self._add_field(eth_item, "Ethertype", f"0x{eth_type:04x}")

        # ── Capa IPv4 ──
        if packet.get('has_ipv4'):
            layers_added += 1
            ipv4 = packet.get('ipv4', {})
            src_ip = packet.get('src_ip', '')
            dst_ip = packet.get('dst_ip', '')
            ip_item = QTreeWidgetItem(self._tree)
            ip_item.setText(0, f"◉  Internet Protocol v4   {src_ip} → {dst_ip}")
            ip_item.setForeground(0, QColor(LAYER_COLORS['ipv4']))
            ihl = ipv4.get('ihl', 5)
            ip_item.setData(0, Qt.ItemDataRole.UserRole, ('ipv4', 14, 14 + ihl * 4))
            ip_item.setFont(0, self._bold_layer_font)

            self._add_field(ip_item, "Versión", str(ipv4.get('version', 4)))
            self._add_field(ip_item, "IHL", f"{ihl}  ({ihl * 4} bytes)")
            self._add_field(ip_item, "Longitud total", str(ipv4.get('total_length', 0)))
            self._add_field(ip_item, "ID", f"0x{ipv4.get('identification', 0):04x}")
            self._add_field(ip_item, "TTL", str(ipv4.get('ttl', 0)))
            self._add_field(ip_item, "Protocolo", str(ipv4.get('protocol', 0)))
            self._add_field(ip_item, "Checksum", f"0x{ipv4.get('checksum', 0):04x}")
            self._add_field(ip_item, "Origen", src_ip)
            self._add_field(ip_item, "Destino", dst_ip)

        # ── Capa TCP ──
        if packet.get('has_tcp'):
            layers_added += 1
            tcp = packet.get('tcp', {})
            sp, dp = tcp.get('src_port', 0), tcp.get('dst_port', 0)
            tcp_item = QTreeWidgetItem(self._tree)
            tcp_item.setText(0, f"▸  TCP   :{sp} → :{dp}")
            tcp_item.setForeground(0, QColor(LAYER_COLORS['tcp']))
            tcp_item.setFont(0, self._bold_layer_font)

            self._add_field(tcp_item, "Puerto origen", str(sp))
            self._add_field(tcp_item, "Puerto destino", str(dp))
            self._add_field(tcp_item, "Seq", str(tcp.get('seq_number', 0)))
            self._add_field(tcp_item, "Ack", str(tcp.get('ack_number', 0)))
            flags_val = tcp.get('flags', 0)
            flags_str = self._decode_tcp_flags(flags_val)
            self._add_field(tcp_item, "Flags", f"0x{flags_val:02x}  {flags_str}")
            self._add_field(tcp_item, "Window", str(tcp.get('window_size', 0)))
            self._add_field(tcp_item, "Checksum", f"0x{tcp.get('checksum', 0):04x}")

        # ── Capa UDP ──
        if packet.get('has_udp'):
            layers_added += 1
            udp = packet.get('udp', {})
            sp, dp = udp.get('src_port', 0), udp.get('dst_port', 0)
            udp_item = QTreeWidgetItem(self._tree)
            udp_item.setText(0, f"▸  UDP   :{sp} → :{dp}")
            udp_item.setForeground(0, QColor(LAYER_COLORS['udp']))
            udp_item.setFont(0, self._bold_layer_font)

            self._add_field(udp_item, "Puerto origen", str(sp))
            self._add_field(udp_item, "Puerto destino", str(dp))
            self._add_field(udp_item, "Longitud", str(udp.get('length', 0)))
            self._add_field(udp_item, "Checksum", f"0x{udp.get('checksum', 0):04x}")

        # ── Capa ICMP ──
        if packet.get('has_icmp'):
            layers_added += 1
            icmp_item = QTreeWidgetItem(self._tree)
            icmp_item.setText(0, "▸  ICMP   Internet Control Message Protocol")
            icmp_item.setForeground(0, QColor(LAYER_COLORS['icmp']))
            icmp_item.setFont(0, self._bold_layer_font)

        # ── Capa ARP ──
        if packet.get('has_arp'):
            layers_added += 1
            arp_item = QTreeWidgetItem(self._tree)
            arp_item.setText(0, "▸  ARP   Address Resolution Protocol")
            arp_item.setForeground(0, QColor(LAYER_COLORS['arp']))
            arp_item.setFont(0, self._bold_layer_font)

        # Expandir todas las capas
        self._tree.expandAll()

        # Actualizar badge de capas
        self._layer_count_label.setText(f"{layers_added} capas")
        self._layer_count_label.setVisible(True)

    def clear(self):
        """Limpia el panel."""
        self._tree.clear()
        self._layer_count_label.setText("")
        self._layer_count_label.setVisible(False)
        self._stack.setCurrentIndex(1)

    def _add_field(self, parent: QTreeWidgetItem, name: str, value: str):
        """Agrega un campo hijo al nodo padre con formato premium."""
        item = QTreeWidgetItem(parent)
        item.setFont(0, self._mono_font)
        # Formato: nombre en muted, valor en texto primario
        item.setText(0, f"  {name:<22} {value}")
        item.setForeground(0, QColor('#8892a8'))  # Color semántico de campo, coherente en ambos temas

    def _decode_tcp_flags(self, flags: int) -> str:
        """Decodifica los flags TCP a string legible."""
        names = []
        if flags & 0x01: names.append("FIN")
        if flags & 0x02: names.append("SYN")
        if flags & 0x04: names.append("RST")
        if flags & 0x08: names.append("PSH")
        if flags & 0x10: names.append("ACK")
        if flags & 0x20: names.append("URG")
        return f"[{' '.join(names)}]" if names else "[ ]"

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Maneja clic en un item para highlight en hex view."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and isinstance(data, tuple) and len(data) == 3:
            layer_name, start, end = data
            self.field_selected.emit(start, end, layer_name)
