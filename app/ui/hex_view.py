"""
hex_view.py — Vista hexadecimal de paquetes estilo Wireshark.

Muestra datos raw en formato: Offset | Hex Bytes | ASCII.
Soporta highlighting de rangos de bytes según la capa seleccionada.
Compatible con temas dark/light mediante objectName 'hexViewEditor'.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor, QPalette
from PyQt6.QtCore import Qt


class HexView(QWidget):
    """Vista hexadecimal con offset, bytes hex y representación ASCII."""

    # Colores semánticos para highlighting de capas (son colores de datos, no de UI)
    LAYER_COLORS = {
        'ethernet': QColor('#ec4899'),
        'ipv4':     QColor('#0db9f2'),
        'tcp':      QColor('#10b981'),
        'udp':      QColor('#22d3ee'),
        'icmp':     QColor('#f59e0b'),
        'arp':      QColor('#f97316'),
        'payload':  QColor('#8b5cf6'),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("hexViewWidget")
        self._setup_ui()
        self._raw_data = b''
        self._highlighted_range = None

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("detailPanelHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("⬡ Vista Hexadecimal")
        title.setObjectName("panelHeaderTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._byte_count_label = QLabel("")
        self._byte_count_label.setObjectName("panelHeaderBadge")
        self._byte_count_label.setVisible(False)
        header_layout.addWidget(self._byte_count_label)

        layout.addWidget(header)

        # Editor hex — usa objectName para que QSS controle colores
        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("hexViewEditor")
        self._text_edit.setReadOnly(True)
        
        # Tipografía más grande y espaciada
        font = QFont("JetBrains Mono", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._text_edit.setFont(font)
        
        layout.addWidget(self._text_edit)

    def set_data(self, raw_data: bytes):
        """Establece los datos raw a mostrar."""
        self._raw_data = raw_data
        self._byte_count_label.setText(f"{len(raw_data)} bytes")
        self._byte_count_label.setVisible(True)
        self._render()

    def highlight_range(self, start: int, end: int, layer: str = 'ipv4'):
        """Resalta un rango de bytes con el color de la capa."""
        self._highlighted_range = (start, end, layer)
        self._render()

    def clear_highlight(self):
        """Limpia el highlighting."""
        self._highlighted_range = None
        self._render()

    def clear(self):
        """Limpia la vista."""
        self._raw_data = b''
        self._highlighted_range = None
        self._byte_count_label.setText("")
        self._byte_count_label.setVisible(False)
        self._text_edit.clear()

    def _get_theme_colors(self):
        """Detecta el tema actual y devuelve los colores apropiados."""
        palette = self._text_edit.palette()
        bg = palette.color(QPalette.ColorRole.Base)
        is_dark = bg.lightness() < 128

        if is_dark:
            return {
                'offset': QColor('#5a6478'),
                'hex':    QColor('#c8cfe0'),
                'ascii':  QColor('#0db9f2'),
                'sep':    QColor('#2a3050'),
            }
        else:
            return {
                'offset': QColor('#64748b'),
                'hex':    QColor('#1e293b'),
                'ascii':  QColor('#0ea5e9'),
                'sep':    QColor('#cbd5e1'),
            }

    def _render(self):
        """Renderiza los datos en formato hex dump."""
        if not self._raw_data:
            self._text_edit.clear()
            return

        self._text_edit.clear()
        cursor = self._text_edit.textCursor()
        colors = self._get_theme_colors()

        # Formatos
        offset_fmt = QTextCharFormat()
        offset_fmt.setForeground(colors['offset'])
        offset_fmt.setFontWeight(QFont.Weight.Bold)

        hex_fmt = QTextCharFormat()
        hex_fmt.setForeground(colors['hex'])

        ascii_fmt = QTextCharFormat()
        ascii_fmt.setForeground(colors['ascii'])

        separator_fmt = QTextCharFormat()
        separator_fmt.setForeground(colors['sep'])

        highlight_fmt = QTextCharFormat()
        if self._highlighted_range:
            layer = self._highlighted_range[2]
            color = self.LAYER_COLORS.get(layer, QColor('#0db9f2'))
            highlight_fmt.setForeground(color)
            highlight_fmt.setBackground(QColor(color.red(), color.green(), color.blue(), 40))
            highlight_fmt.setFontWeight(QFont.Weight.Bold)

        bytes_per_line = 16
        data = self._raw_data

        for offset in range(0, len(data), bytes_per_line):
            chunk = data[offset:offset + bytes_per_line]

            # Offset (uppercase, 4 digits min)
            cursor.insertText(f"{offset:04X}", offset_fmt)
            cursor.insertText("    ", separator_fmt)

            # Hex bytes — con separador visual a los 8 bytes
            for i in range(bytes_per_line):
                if i == 8:
                    cursor.insertText(" ", separator_fmt)
                if i < len(chunk):
                    byte = chunk[i]
                    byte_offset = offset + i
                    is_highlighted = (
                        self._highlighted_range is not None
                        and self._highlighted_range[0] <= byte_offset < self._highlighted_range[1]
                    )
                    fmt = highlight_fmt if is_highlighted else hex_fmt
                    cursor.insertText(f"{byte:02X} ", fmt)
                else:
                    cursor.insertText("   ", hex_fmt)

            cursor.insertText("  ", separator_fmt)

            # ASCII — con separador visual a los 8 bytes
            for i in range(bytes_per_line):
                if i == 8:
                    cursor.insertText(" ", separator_fmt)
                if i < len(chunk):
                    byte = chunk[i]
                    byte_offset = offset + i
                    is_highlighted = (
                        self._highlighted_range is not None
                        and self._highlighted_range[0] <= byte_offset < self._highlighted_range[1]
                    )
                    char = chr(byte) if 32 <= byte < 127 else '·'
                    fmt = highlight_fmt if is_highlighted else ascii_fmt
                    cursor.insertText(char, fmt)
                else:
                    # Mantener ancho fijo de la columna ASCII incluso en la última línea.
                    cursor.insertText(" ", ascii_fmt)

            cursor.insertText("\n")

        self._text_edit.setTextCursor(cursor)
