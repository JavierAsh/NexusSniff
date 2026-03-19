"""
test_packet_model.py — Tests para el modelo de tabla de paquetes.

Verifica la inserción, eliminación, formateo y el límite de paquetes
del PacketTableModel.
"""

import pytest
from PyQt6.QtCore import QModelIndex
from app.core.packet_model import PacketTableModel, COLUMNS


@pytest.fixture
def model(qapp):
    """Crea un PacketTableModel limpio para cada test."""
    return PacketTableModel()


def _make_packet(number: int = 1, **overrides) -> dict:
    """Construye un dict de paquete base para testing."""
    pkt = {
        'number': number,
        'timestamp': 1000.0 + number * 0.001,
        'length': 64,
        'protocol': 'TCP',
        'src_ip': '192.168.1.1',
        'dst_ip': '10.0.0.1',
        'src_port': 12345,
        'dst_port': 80,
        'src_mac': 'aa:bb:cc:dd:ee:ff',
        'dst_mac': '11:22:33:44:55:66',
        'info': 'SYN',
        'raw_data': b'\x00' * 64,
        'has_ethernet': True,
        'has_ipv4': True,
        'has_tcp': True,
        'has_udp': False,
        'has_icmp': False,
        'has_arp': False,
    }
    pkt.update(overrides)
    return pkt


class TestPacketTableModel:
    """Tests para PacketTableModel."""

    def test_empty_model(self, model):
        """Un modelo recién creado está vacío."""
        assert model.rowCount() == 0
        assert model.columnCount() == len(COLUMNS)
        assert model.packet_count() == 0

    def test_add_single_packet(self, model):
        """Insertar un paquete incrementa el conteo."""
        model.add_packets([_make_packet(1)])
        assert model.rowCount() == 1
        assert model.packet_count() == 1

    def test_add_batch(self, model):
        """Insertar un batch de paquetes a la vez."""
        packets = [_make_packet(i) for i in range(50)]
        model.add_packets(packets)
        assert model.packet_count() == 50

    def test_clear(self, model):
        """clear() vacía el modelo completamente."""
        model.add_packets([_make_packet(i) for i in range(10)])
        model.clear()
        assert model.packet_count() == 0

    def test_get_packet(self, model):
        """get_packet devuelve el paquete correcto."""
        pkt = _make_packet(42, protocol='DNS')
        model.add_packets([pkt])
        result = model.get_packet(0)
        assert result is not None
        assert result['number'] == 42
        assert result['protocol'] == 'DNS'

    def test_get_packet_out_of_range(self, model):
        """get_packet con índice fuera de rango devuelve None."""
        assert model.get_packet(0) is None
        assert model.get_packet(-1) is None
        assert model.get_packet(999) is None

    def test_display_role_protocol(self, model):
        """La columna de protocolo muestra el nombre correcto."""
        model.add_packets([_make_packet(1, protocol='UDP')])
        from PyQt6.QtCore import Qt
        proto_col = next(i for i, c in enumerate(COLUMNS) if c[1] == 'protocol')
        idx = model.index(0, proto_col)
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value == 'UDP'

    def test_display_role_ip_with_port(self, model):
        """Las columnas de IP muestran IP:puerto."""
        model.add_packets([_make_packet(1, src_ip='1.2.3.4', src_port=443)])
        from PyQt6.QtCore import Qt
        src_col = next(i for i, c in enumerate(COLUMNS) if c[1] == 'src_ip')
        idx = model.index(0, src_col)
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value == '1.2.3.4:443'

    def test_max_packets_eviction(self, model):
        """Al exceder el límite, los paquetes viejos se eliminan."""
        model._max_packets = 100
        packets = [_make_packet(i) for i in range(150)]
        model.add_packets(packets)
        assert model.packet_count() == 100
        # El primer paquete debería ser el #50 (se eliminaron 0-49)
        first = model.get_packet(0)
        assert first['number'] == 50

    def test_relative_timestamp(self, model):
        """El timestamp mostrado es relativo al primer paquete."""
        from PyQt6.QtCore import Qt
        model.add_packets([
            _make_packet(1, timestamp=1000.0),
            _make_packet(2, timestamp=1001.5),
        ])
        ts_col = next(i for i, c in enumerate(COLUMNS) if c[1] == 'timestamp')
        # Segundo paquete
        idx = model.index(1, ts_col)
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value == '1.500000'

    def test_foreground_color_per_protocol(self, model):
        """Cada protocolo tiene un color de foreground distinto."""
        from PyQt6.QtCore import Qt
        from app.core.packet_model import PROTOCOL_COLORS
        model.add_packets([_make_packet(1, protocol='HTTP')])
        idx = model.index(0, 0)
        color = model.data(idx, Qt.ItemDataRole.ForegroundRole)
        assert color == PROTOCOL_COLORS['HTTP']
