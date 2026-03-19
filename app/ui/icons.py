"""
icons.py — Iconografía vectorial propietaria para NexusSniff.

Contiene:
- Widget icons (QWidget con paintEvent) para las StatCards del dashboard.
- create_vector_icon(): Fábrica de QIcon dibujados en memoria con QPainter.
  Usados en botones, sidebar y menús sin dependencias externas.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QPolygonF, QIcon, QPixmap, QFont, QPainterPath
)
import math


# ═══════════════════════════════════════════════════════════════
#  Widget Icons  (para StatCards del Dashboard)
# ═══════════════════════════════════════════════════════════════

class CubeIconWidget(QWidget):
    """Cubo minimalista para Total de Paquetes."""
    def __init__(self, size: int = 24, color: str = "#8892a8", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self._color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        cx, cy = self.width() / 2, self.height() / 2
        r = self.width() * 0.4

        pts = []
        for i in range(6):
            a = math.radians(60 * i + 30)
            pts.append(QPointF(cx + r * math.cos(a), cy + r * math.sin(a)))

        painter.drawPolygon(QPolygonF(pts))
        painter.drawLine(pts[1], QPointF(cx, cy))
        painter.drawLine(pts[3], QPointF(cx, cy))
        painter.drawLine(pts[5], QPointF(cx, cy))
        painter.end()


class DiskIconWidget(QWidget):
    """Unidad de disco estilizada para Bytes Totales."""
    def __init__(self, size: int = 24, color: str = "#8892a8", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self._color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        w, h = self.width() * 0.7, self.height() * 0.8
        x, y = (self.width() - w) / 2, (self.height() - h) / 2

        painter.drawRoundedRect(int(x), int(y), int(w), int(h), 3, 3)
        painter.drawLine(int(x + w * 0.2), int(y + h * 0.3), int(x + w * 0.8), int(y + h * 0.3))
        painter.drawLine(int(x + w * 0.2), int(y + h * 0.5), int(x + w * 0.8), int(y + h * 0.5))
        painter.drawEllipse(int(x + w * 0.5 - 2), int(y + h * 0.75 - 2), 4, 4)
        painter.end()


class PulseIconWidget(QWidget):
    """Onda de pulso eléctrica para Tráfico/Velocidad."""
    def __init__(self, size: int = 24, color: str = "#8892a8", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self._color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        w, h = self.width(), self.height()
        cy = h / 2

        pts = [
            QPointF(w * 0.1, cy),
            QPointF(w * 0.3, cy),
            QPointF(w * 0.45, h * 0.2),
            QPointF(w * 0.6, h * 0.8),
            QPointF(w * 0.75, cy),
            QPointF(w * 0.9, cy)
        ]
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])
        painter.end()


class AlertIconWidget(QWidget):
    """Triángulo de bordes redondeados para Alertas."""
    def __init__(self, size: int = 24, color: str = "#8892a8", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self._color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        w, h = self.width(), self.height()
        cy = h * 0.85
        cx = w / 2

        p1 = QPointF(cx, h * 0.15)
        p2 = QPointF(w * 0.15, cy)
        p3 = QPointF(w * 0.85, cy)
        painter.drawLine(p1, p2)
        painter.drawLine(p2, p3)
        painter.drawLine(p3, p1)

        painter.drawLine(QPointF(cx, h * 0.35), QPointF(cx, h * 0.55))
        painter.drawPoint(QPointF(cx, h * 0.65))
        painter.end()


class MetricIconWidget(QWidget):
    """Gráfico de barras estilizado."""
    def __init__(self, size: int = 24, color: str = "#8892a8", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)

        w, h = self.width(), self.height()
        painter.drawRoundedRect(int(w * 0.15), int(h * 0.5), int(w * 0.15), int(h * 0.35), 2, 2)
        painter.drawRoundedRect(int(w * 0.42), int(h * 0.2), int(w * 0.15), int(h * 0.65), 2, 2)
        painter.drawRoundedRect(int(w * 0.7), int(h * 0.4), int(w * 0.15), int(h * 0.45), 2, 2)
        painter.end()


# ═══════════════════════════════════════════════════════════════
#  QIcon Factory  (para botones, sidebar, menús)
# ═══════════════════════════════════════════════════════════════

def create_vector_icon(icon_type: str, color: str = "#c8d0e0", size: int = 20) -> QIcon:
    """
    Genera un QIcon dibujado con QPainter en un QPixmap transparente.
    Tipos: dashboard, capture, settings, network, play, stop, trash,
           folder, arrow_down, filter, hamburger, clear_x
    """
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QColor(color)
    pen = QPen(c, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    w = float(size)

    if icon_type == "dashboard":
        # Mini bar-chart
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawRoundedRect(QRectF(w * 0.1, w * 0.55, w * 0.2, w * 0.35), 2, 2)
        p.drawRoundedRect(QRectF(w * 0.4, w * 0.25, w * 0.2, w * 0.65), 2, 2)
        p.drawRoundedRect(QRectF(w * 0.7, w * 0.4, w * 0.2, w * 0.5), 2, 2)

    elif icon_type == "capture":
        # Magnifying glass
        r = w * 0.28
        cx, cy = w * 0.4, w * 0.4
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx + r * 0.7, cy + r * 0.7), QPointF(w * 0.85, w * 0.85))

    elif icon_type == "settings":
        # Gear
        cx, cy = w / 2, w / 2
        r_outer = w * 0.38
        r_inner = w * 0.22
        p.drawEllipse(QPointF(cx, cy), r_inner, r_inner)
        for i in range(6):
            a = math.radians(60 * i)
            p.drawLine(
                QPointF(cx + r_inner * math.cos(a), cy + r_inner * math.sin(a)),
                QPointF(cx + r_outer * math.cos(a), cy + r_outer * math.sin(a))
            )

    elif icon_type == "network":
        # Globe with arcs
        cx, cy, r = w / 2, w / 2, w * 0.35
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))
        p.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))

    elif icon_type == "play":
        # Play triangle
        path = QPainterPath()
        path.moveTo(w * 0.25, w * 0.15)
        path.lineTo(w * 0.8, w * 0.5)
        path.lineTo(w * 0.25, w * 0.85)
        path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawPath(path)

    elif icon_type == "stop":
        # Stop square
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawRoundedRect(QRectF(w * 0.2, w * 0.2, w * 0.6, w * 0.6), 3, 3)

    elif icon_type == "trash":
        # Trash can
        p.drawLine(QPointF(w * 0.25, w * 0.25), QPointF(w * 0.75, w * 0.25))
        p.drawLine(QPointF(w * 0.3, w * 0.25), QPointF(w * 0.3, w * 0.82))
        p.drawLine(QPointF(w * 0.7, w * 0.25), QPointF(w * 0.7, w * 0.82))
        p.drawLine(QPointF(w * 0.3, w * 0.82), QPointF(w * 0.7, w * 0.82))
        p.drawLine(QPointF(w * 0.4, w * 0.15), QPointF(w * 0.6, w * 0.15))
        p.drawLine(QPointF(w * 0.4, w * 0.15), QPointF(w * 0.4, w * 0.25))
        p.drawLine(QPointF(w * 0.6, w * 0.15), QPointF(w * 0.6, w * 0.25))

    elif icon_type == "folder":
        # Folder
        p.drawLine(QPointF(w * 0.1, w * 0.3), QPointF(w * 0.4, w * 0.3))
        p.drawLine(QPointF(w * 0.4, w * 0.3), QPointF(w * 0.5, w * 0.2))
        p.drawLine(QPointF(w * 0.1, w * 0.3), QPointF(w * 0.1, w * 0.8))
        p.drawLine(QPointF(w * 0.1, w * 0.8), QPointF(w * 0.9, w * 0.8))
        p.drawLine(QPointF(w * 0.9, w * 0.8), QPointF(w * 0.9, w * 0.35))
        p.drawLine(QPointF(w * 0.9, w * 0.35), QPointF(w * 0.5, w * 0.35))
        p.drawLine(QPointF(w * 0.5, w * 0.35), QPointF(w * 0.5, w * 0.2))
        p.drawLine(QPointF(w * 0.5, w * 0.2), QPointF(w * 0.4, w * 0.3))

    elif icon_type == "arrow_down":
        # Down arrow
        p.drawLine(QPointF(w * 0.5, w * 0.2), QPointF(w * 0.5, w * 0.7))
        p.drawLine(QPointF(w * 0.3, w * 0.55), QPointF(w * 0.5, w * 0.7))
        p.drawLine(QPointF(w * 0.7, w * 0.55), QPointF(w * 0.5, w * 0.7))

    elif icon_type == "filter":
        # Funnel
        p.drawLine(QPointF(w * 0.1, w * 0.2), QPointF(w * 0.9, w * 0.2))
        p.drawLine(QPointF(w * 0.1, w * 0.2), QPointF(w * 0.4, w * 0.6))
        p.drawLine(QPointF(w * 0.9, w * 0.2), QPointF(w * 0.6, w * 0.6))
        p.drawLine(QPointF(w * 0.4, w * 0.6), QPointF(w * 0.4, w * 0.85))
        p.drawLine(QPointF(w * 0.6, w * 0.6), QPointF(w * 0.6, w * 0.85))

    elif icon_type == "hamburger":
        # Three horizontal lines
        p.drawLine(QPointF(w * 0.2, w * 0.3), QPointF(w * 0.8, w * 0.3))
        p.drawLine(QPointF(w * 0.2, w * 0.5), QPointF(w * 0.8, w * 0.5))
        p.drawLine(QPointF(w * 0.2, w * 0.7), QPointF(w * 0.8, w * 0.7))

    elif icon_type == "clear_x":
        # X
        p.drawLine(QPointF(w * 0.25, w * 0.25), QPointF(w * 0.75, w * 0.75))
        p.drawLine(QPointF(w * 0.75, w * 0.25), QPointF(w * 0.25, w * 0.75))

    p.end()
    return QIcon(pix)
