"""
packet_model.py — Modelo de tabla para paquetes capturados (zero-copy).

QAbstractTableModel que alimenta el QTableView principal.
Color-coded por protocolo para identificación visual rápida.

Optimización v1.2: Los paquetes se almacenan como objetos PacketData
de C++ (pybind11). Los atributos solo se leen bajo demanda (display),
eliminando la creación masiva de dicts en el loop de captura.
"""

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QFont
from typing import List, Any


# ══════════════════════════════════════════════════════════════
# Colores por protocolo (inspirados en Stitch NexusSniff)
# ══════════════════════════════════════════════════════════════

PROTOCOL_COLORS = {
    'TCP':     QColor('#0db9f2'),   # Cyan
    'UDP':     QColor('#10b981'),   # Verde
    'ICMP':    QColor('#f59e0b'),   # Amber
    'DNS':     QColor('#f97316'),   # Naranja
    'HTTP':    QColor('#8b5cf6'),   # Violeta
    'HTTPS':   QColor('#06b6d4'),   # Cyan claro
    'SSH':     QColor('#ec4899'),   # Rosa
    'ARP':     QColor('#ec4899'),   # Rosa
    'FTP':     QColor('#84cc16'),   # Lima
    'SMTP':    QColor('#a855f7'),   # Púrpura
    'DHCP':    QColor('#14b8a6'),   # Teal
    'SNMP':    QColor('#64748b'),   # Gris
    'Telnet':  QColor('#f43f5e'),   # Rojo
    'ICMPv6':  QColor('#eab308'),   # Amarillo
    'IPv6':    QColor('#6366f1'),   # Indigo
    'Unknown': QColor('#475569'),   # Gris oscuro
}

# ══════════════════════════════════════════════════════════════
# Columnas de la tabla
# ══════════════════════════════════════════════════════════════

COLUMNS = [
    ('Nº',        'number',    60),
    ('Tiempo',    'timestamp', 100),
    ('Origen',    'src_ip',    140),
    ('Destino',   'dst_ip',    140),
    ('Protocolo', 'protocol',  90),
    ('Longitud',  'length',    80),
    ('Info',      'info',      400),
]


def _get_attr(packet, key, default=''):
    """Lee un atributo de un PacketData C++ o un dict Python."""
    if isinstance(packet, dict):
        return packet.get(key, default)
    return getattr(packet, key, default)


class PacketTableModel(QAbstractTableModel):
    """
    Modelo de tabla para paquetes de red (soporta PacketData C++ y dicts).

    Soporta hasta ~100k paquetes en memoria con rendimiento fluido.
    Los paquetes pueden ser objetos PacketData de C++ (zero-copy) o
    diccionarios Python (compatibilidad con exportación).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._packets: List[Any] = []
        self._first_timestamp: float = 0.0
        self._max_packets = 100_000

        # Font monospace para datos técnicos
        self._mono_font = QFont("JetBrains Mono", 10)
        self._mono_font.setStyleHint(QFont.StyleHint.Monospace)

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._packets)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return COLUMNS[section][0]
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont("Segoe UI", 10)
                font.setBold(True)
                return font
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._packets):
            return None

        packet = self._packets[index.row()]
        col_key = COLUMNS[index.column()][1]

        if role == Qt.ItemDataRole.DisplayRole:
            if col_key == 'timestamp':
                # Mostrar tiempo relativo desde el primer paquete
                if self._first_timestamp == 0.0:
                    return "0.000000"
                ts = _get_attr(packet, 'timestamp', 0)
                relative = ts - self._first_timestamp
                return f"{relative:.6f}"
            elif col_key == 'number':
                return str(_get_attr(packet, 'number', ''))
            elif col_key == 'length':
                return str(_get_attr(packet, 'length', ''))
            elif col_key == 'src_ip':
                src = _get_attr(packet, 'src_ip_str' if not isinstance(packet, dict) else 'src_ip', '')
                port = _get_attr(packet, 'src_port', 0)
                if port and port > 0:
                    return f"{src}:{port}"
                return src
            elif col_key == 'dst_ip':
                dst = _get_attr(packet, 'dst_ip_str' if not isinstance(packet, dict) else 'dst_ip', '')
                port = _get_attr(packet, 'dst_port', 0)
                if port and port > 0:
                    return f"{dst}:{port}"
                return dst
            elif col_key == 'protocol':
                if isinstance(packet, dict):
                    return str(packet.get('protocol', ''))
                return str(getattr(packet, 'protocol_name', ''))
            else:
                return str(_get_attr(packet, col_key, ''))

        elif role == Qt.ItemDataRole.ForegroundRole:
            # Color por protocolo
            if isinstance(packet, dict):
                protocol = packet.get('protocol', 'Unknown')
            else:
                protocol = getattr(packet, 'protocol_name', 'Unknown')
            return PROTOCOL_COLORS.get(protocol, PROTOCOL_COLORS['Unknown'])

        elif role == Qt.ItemDataRole.FontRole:
            # Monospace para columnas técnicas
            if col_key in ('src_ip', 'dst_ip', 'timestamp', 'number', 'length'):
                return self._mono_font

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col_key in ('number', 'length'):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            elif col_key == 'protocol':
                return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.UserRole:
            # Devolver el objeto PacketData o dict completo
            return packet

        return None

    def add_packets(self, packets: list):
        """Agrega nuevos paquetes al modelo (PacketData C++ o dicts)."""
        if not packets:
            return

        # Establecer timestamp base
        if self._first_timestamp == 0.0 and packets:
            first = packets[0]
            self._first_timestamp = _get_attr(first, 'timestamp', 0.0)

        # Limitar el número total de paquetes en memoria
        if len(self._packets) + len(packets) > self._max_packets:
            # Eliminar paquetes más antiguos
            excess = len(self._packets) + len(packets) - self._max_packets
            self.beginRemoveRows(QModelIndex(), 0, excess - 1)
            self._packets = self._packets[excess:]
            self.endRemoveRows()

        # Insertar los nuevos paquetes
        first_row = len(self._packets)
        last_row = first_row + len(packets) - 1
        self.beginInsertRows(QModelIndex(), first_row, last_row)
        self._packets.extend(packets)
        self.endInsertRows()

    def get_packet(self, row: int):
        """Obtiene un paquete por su fila (PacketData C++ o dict)."""
        if 0 <= row < len(self._packets):
            return self._packets[row]
        return None

    def clear(self):
        """Limpia todos los paquetes."""
        self.beginResetModel()
        self._packets.clear()
        self._first_timestamp = 0.0
        self.endResetModel()

    def packet_count(self) -> int:
        """Número total de paquetes en el modelo."""
        return len(self._packets)
