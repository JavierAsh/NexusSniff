"""
test_capture_worker.py — Tests para el worker de captura.

Verifica la función packet_to_dict y la lógica del CaptureWorker.
"""

import pytest
from app.core.capture_worker import packet_to_dict


class MockEthernet:
    ethertype = 0x0800


class MockIPv4:
    version = 4
    ihl = 5
    ttl = 64
    total_length = 60
    identification = 0x1234
    protocol = 6
    checksum = 0xABCD


class MockTcp:
    src_port = 443
    dst_port = 80
    seq_number = 100
    ack_number = 200
    flags = 0x02
    window_size = 65535
    checksum = 0x1111


class MockUdp:
    src_port = 53
    dst_port = 1024
    length = 30
    checksum = 0x2222


class MockIcmp:
    type = 8
    code = 0
    checksum = 0x3333


class MockPacketData:
    """Mock de un objeto PacketData de C++ para testing."""

    def __init__(self, **kwargs):
        self.number = kwargs.get('number', 1)
        self.timestamp = kwargs.get('timestamp', 1000.0)
        self.length = kwargs.get('length', 64)
        self.protocol_name = kwargs.get('protocol_name', 'TCP')
        self.src_ip_str = kwargs.get('src_ip_str', '192.168.1.1')
        self.dst_ip_str = kwargs.get('dst_ip_str', '10.0.0.1')
        self.src_port = kwargs.get('src_port', 12345)
        self.dst_port = kwargs.get('dst_port', 80)
        self.src_mac_str = kwargs.get('src_mac_str', 'aa:bb:cc:dd:ee:ff')
        self.dst_mac_str = kwargs.get('dst_mac_str', '11:22:33:44:55:66')
        self.info = kwargs.get('info', 'SYN')
        self.raw_data = kwargs.get('raw_data', b'\x00' * 64)
        self.has_ethernet = kwargs.get('has_ethernet', True)
        self.has_ipv4 = kwargs.get('has_ipv4', True)
        self.has_tcp = kwargs.get('has_tcp', True)
        self.has_udp = kwargs.get('has_udp', False)
        self.has_icmp = kwargs.get('has_icmp', False)
        self.has_arp = kwargs.get('has_arp', False)
        self.ethernet = MockEthernet()
        self.ipv4 = MockIPv4()
        self.tcp = MockTcp()
        self.udp = MockUdp()
        self.icmp = MockIcmp()


class TestPacketToDict:
    """Tests para la función packet_to_dict."""

    def test_basic_conversion(self):
        """Convierte campos básicos correctamente."""
        pkt = MockPacketData(number=42, protocol_name='DNS')
        result = packet_to_dict(pkt)

        assert result['number'] == 42
        assert result['protocol'] == 'DNS'
        assert result['src_ip'] == '192.168.1.1'
        assert result['dst_ip'] == '10.0.0.1'
        assert result['src_port'] == 12345

    def test_ethernet_layer(self):
        """Incluye datos de la capa Ethernet."""
        pkt = MockPacketData(has_ethernet=True)
        result = packet_to_dict(pkt)

        assert 'ethernet' in result
        assert result['ethernet']['ethertype'] == 0x0800

    def test_ipv4_layer(self):
        """Incluye datos de la capa IPv4."""
        pkt = MockPacketData(has_ipv4=True)
        result = packet_to_dict(pkt)

        assert 'ipv4' in result
        assert result['ipv4']['version'] == 4
        assert result['ipv4']['ttl'] == 64

    def test_tcp_layer(self):
        """Incluye datos de la capa TCP."""
        pkt = MockPacketData(has_tcp=True)
        result = packet_to_dict(pkt)

        assert 'tcp' in result
        assert result['tcp']['src_port'] == 443
        assert result['tcp']['flags'] == 0x02

    def test_no_optional_layers(self):
        """Omite capas no presentes."""
        pkt = MockPacketData(
            has_ethernet=False,
            has_ipv4=False,
            has_tcp=False,
            has_udp=False,
            has_icmp=False,
        )
        result = packet_to_dict(pkt)

        assert 'ethernet' not in result
        assert 'ipv4' not in result
        assert 'tcp' not in result
        assert 'udp' not in result
        assert 'icmp' not in result

    def test_raw_data_is_bytes(self):
        """raw_data siempre es bytes."""
        pkt = MockPacketData(raw_data=b'\xDE\xAD\xBE\xEF')
        result = packet_to_dict(pkt)
        assert isinstance(result['raw_data'], bytes)
        assert result['raw_data'] == b'\xDE\xAD\xBE\xEF'
