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
                'sep':    QColor('#3f4b66'), # Un poco más claro para mejor visibilidad
            }
        else:
            return {
                'offset': QColor('#64748b'),
                'hex':    QColor('#1e293b'),
                'ascii':  QColor('#0ea5e9'),
                'sep':    QColor('#94a3b8'), # Slate para modo claro
            }

    def _render(self):
        """Renderiza los datos en formato hex dump ultra-ordenado con segmentación clara."""
        if not self._raw_data:
            self._text_edit.clear()
            return

        self._text_edit.clear()
        cursor = self._text_edit.textCursor()
        colors = self._get_theme_colors()
        
        # Tipografía monospace robusta
        font = QFont("JetBrains Mono", 11)
        if not font.exactMatch():
            font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self._text_edit.setFont(font)

        # Formatos predefinidos
        fmt_offset = QTextCharFormat()
        fmt_offset.setForeground(colors['offset'])
        fmt_offset.setFontWeight(QFont.Weight.Bold)
        fmt_offset.setFont(font)

        fmt_hex = QTextCharFormat()
        fmt_hex.setForeground(colors['hex'])
        fmt_hex.setFont(font)

        fmt_ascii = QTextCharFormat()
        fmt_ascii.setForeground(colors['ascii'])
        fmt_ascii.setFont(font)

        fmt_sep = QTextCharFormat()
        fmt_sep.setForeground(colors['sep'])
        fmt_sep.setFont(font)

        # Formato de resaltado (capas)
        highlight_fmt = QTextCharFormat()
        highlight_fmt.setFont(font)
        if self._highlighted_range:
            layer = self._highlighted_range[2]
            h_color = self.LAYER_COLORS.get(layer, QColor('#0db9f2'))
            highlight_fmt.setForeground(h_color)
            # Fondo sutil para destacar el bloque
            bg_color = QColor(h_color.red(), h_color.green(), h_color.blue(), 50)
            highlight_fmt.setBackground(bg_color)
            highlight_fmt.setFontWeight(QFont.Weight.Bold)

        bytes_per_line = 16
        data = self._raw_data

        for offset in range(0, len(data), bytes_per_line):
            chunk = data[offset:offset + bytes_per_line]

            # 1. Offset
            cursor.insertText(f"{offset:04X} ", fmt_offset)
            
            # 2. Separador visual inicial
            cursor.insertText("│ ", fmt_sep)

            # 3. Hex Bytes (segmentados cada 8)
            for i in range(bytes_per_line):
                if i == 8:
                    cursor.insertText(" ", fmt_sep) # Gap central
                
                if i < len(chunk):
                    byte_val = chunk[i]
                    byte_idx = offset + i
                    is_h = (self._highlighted_range and 
                            self._highlighted_range[0] <= byte_idx < self._highlighted_range[1])
                    
                    fmt = highlight_fmt if is_h else fmt_hex
                    cursor.insertText(f"{byte_val:02X} ", fmt)
                else:
                    cursor.insertText("   ", fmt_hex) # Padding

            # 4. Separador visual central
            cursor.insertText("│ ", fmt_sep)

            # 5. Representación ASCII
            for i in range(bytes_per_line):
                if i == 8:
                    cursor.insertText(" ", fmt_sep) # Mantenemos gap para alineación vertical
                
                if i < len(chunk):
                    byte_val = chunk[i]
                    byte_idx = offset + i
                    is_h = (self._highlighted_range and 
                            self._highlighted_range[0] <= byte_idx < self._highlighted_range[1])
                    
                    char = chr(byte_val) if 32 <= byte_val < 127 else "·"
                    fmt = highlight_fmt if is_h else fmt_ascii
                    cursor.insertText(char, fmt)
                else:
                    cursor.insertText(" ", fmt_ascii) # Padding ASCII

            cursor.insertText("\n")

        self._text_edit.setTextCursor(cursor)
