"""
capture_worker.py — Hilo de captura en segundo plano optimizado.

Usa QThread para invocar nexus_engine.PacketCapturer sin bloquear
la interfaz PyQt6. Emite señales cuando hay nuevos paquetes o
actualizaciones de estadísticas.

Optimizaciones v1.2 (Zero-Copy):
- Los PacketData de C++ se pasan directamente como objetos opacos
- Solo se convierten a dict bajo demanda (detail_panel, export)
- get_stats() solo se llama cuando va a emitir (4x/seg)
- msleep(10) tras procesar batch para ceder CPU
"""

from PyQt6.QtCore import QThread, pyqtSignal
import logging
import time

logger = logging.getLogger(__name__)


def packet_to_dict(pkt) -> dict:
    """Convierte un PacketData C++ a dict Python — solo bajo demanda."""
    packet_dict = {
        'number':       pkt.number,
        'timestamp':    pkt.timestamp,
        'length':       pkt.length,
        'protocol':     pkt.protocol_name,
        'src_ip':       pkt.src_ip_str,
        'dst_ip':       pkt.dst_ip_str,
        'src_port':     pkt.src_port,
        'dst_port':     pkt.dst_port,
        'src_mac':      pkt.src_mac_str,
        'dst_mac':      pkt.dst_mac_str,
        'info':         pkt.info,
        'raw_data':     bytes(pkt.raw_data),
        'has_ethernet': pkt.has_ethernet,
        'has_ipv4':     pkt.has_ipv4,
        'has_tcp':      pkt.has_tcp,
        'has_udp':      pkt.has_udp,
        'has_icmp':     pkt.has_icmp,
        'has_arp':      pkt.has_arp,
    }

    # Añadir capas decodificadas solo si existen
    if pkt.has_ethernet:
        packet_dict['ethernet'] = {
            'ethertype': pkt.ethernet.ethertype,
        }
    if pkt.has_ipv4:
        packet_dict['ipv4'] = {
            'version':        pkt.ipv4.version,
            'ihl':            pkt.ipv4.ihl,
            'ttl':            pkt.ipv4.ttl,
            'total_length':   pkt.ipv4.total_length,
            'identification': pkt.ipv4.identification,
            'protocol':       pkt.ipv4.protocol,
            'checksum':       pkt.ipv4.checksum,
        }
    if pkt.has_tcp:
        packet_dict['tcp'] = {
            'src_port':    pkt.tcp.src_port,
            'dst_port':    pkt.tcp.dst_port,
            'seq_number':  pkt.tcp.seq_number,
            'ack_number':  pkt.tcp.ack_number,
            'flags':       pkt.tcp.flags,
            'window_size': pkt.tcp.window_size,
            'checksum':    pkt.tcp.checksum,
        }
    if pkt.has_udp:
        packet_dict['udp'] = {
            'src_port': pkt.udp.src_port,
            'dst_port': pkt.udp.dst_port,
            'length':   pkt.udp.length,
            'checksum': pkt.udp.checksum,
        }
    if pkt.has_icmp:
        packet_dict['icmp'] = {
            'type':     pkt.icmp.type,
            'code':     pkt.icmp.code,
            'checksum': pkt.icmp.checksum,
        }

    return packet_dict


class CaptureWorker(QThread):
    """
    Worker thread para captura de paquetes de red.

    Señales:
        new_packets: Lista de objetos PacketData C++ (zero-copy).
        stats_updated: Diccionario con estadísticas de captura.
        capture_error: Mensaje de error si falla la captura.
        capture_started: Emitida cuando la captura comienza exitosamente.
        capture_stopped: Emitida cuando la captura se detiene.
    """

    new_packets    = pyqtSignal(list)
    stats_updated  = pyqtSignal(dict)
    capture_error  = pyqtSignal(str)
    capture_started = pyqtSignal()
    capture_stopped = pyqtSignal()

    # Intervalos de tiempo en segundos
    BATCH_EMIT_INTERVAL = 0.10   # Emitir batch cada 100ms máximo
    STATS_EMIT_INTERVAL = 0.25   # Emitir stats cada 250ms
    BATCH_MAX_SIZE      = 500    # Emitir si el batch supera este tamaño
    POLL_SLEEP_MS       = 20     # ms a dormir cuando no hay paquetes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capturer = None
        self._interface_name = ""
        self._bpf_filter = ""
        self._is_running = False

    def configure(self, interface_name: str, bpf_filter: str = ""):
        """Configura la interfaz y filtro antes de iniciar."""
        self._interface_name = interface_name
        self._bpf_filter = bpf_filter

    @property
    def is_running(self) -> bool:
        return self._is_running

    def run(self):
        """Loop principal del hilo de captura — zero-copy optimizado."""
        try:
            # Importar el módulo C++ compilado
            try:
                import app.nexus_engine as nexus_engine
            except ImportError:
                self.capture_error.emit(
                    "No se pudo cargar app.nexus_engine.pyd. "
                    "¿Has compilado el motor C++?"
                )
                return

            # Crear capturador e iniciar
            self._capturer = nexus_engine.PacketCapturer()
            success = self._capturer.start(
                self._interface_name,
                self._bpf_filter
            )

            if not success:
                error = self._capturer.get_last_error()
                self.capture_error.emit(f"Error iniciando captura: {error}")
                return

            self._is_running = True
            self.capture_started.emit()

            # ── Loop de polling optimizado (zero-copy) ──
            packet_batch = []
            last_batch_time = time.monotonic()
            last_stats_time = time.monotonic()

            while self._is_running and self._capturer.is_capturing():
                # Obtener paquetes del ring buffer (hasta 500 por iteración)
                # Los PacketData se pasan directamente como objetos C++
                raw_packets = self._capturer.get_packets(500)

                if raw_packets:
                    # Zero-copy: pasar los objetos PacketData directamente
                    packet_batch.extend(raw_packets)

                now = time.monotonic()

                # Emitir batch si se superó el intervalo o el tamaño máximo
                if packet_batch and (
                    len(packet_batch) >= self.BATCH_MAX_SIZE
                    or (now - last_batch_time) >= self.BATCH_EMIT_INTERVAL
                ):
                    self.new_packets.emit(packet_batch)
                    packet_batch = []
                    last_batch_time = now

                # Emitir estadísticas a menor frecuencia (4x/seg)
                if (now - last_stats_time) >= self.STATS_EMIT_INTERVAL:
                    stats = self._capturer.get_stats()
                    stats_dict = {
                        'total_packets':       stats.total_packets,
                        'total_bytes':         stats.total_bytes,
                        'dropped_packets':     stats.dropped_packets,
                        'packets_per_sec':     stats.packets_per_sec,
                        'bytes_per_sec':       stats.bytes_per_sec,
                        'protocol_distribution': stats.get_protocol_distribution(),
                    }
                    self.stats_updated.emit(stats_dict)
                    last_stats_time = now

                # Ceder CPU cuando no hay paquetes disponibles
                if not raw_packets:
                    self.msleep(self.POLL_SLEEP_MS)
                else:
                    # Pequeño yield incluso con paquetes para evitar starvation de la GUI
                    self.msleep(1)

            # Emitir paquetes pendientes antes de terminar
            if packet_batch:
                self.new_packets.emit(packet_batch)

        except Exception as e:
            self.capture_error.emit(f"Error inesperado: {str(e)}")
        finally:
            self._is_running = False
            if self._capturer:
                try:
                    self._capturer.stop()
                except Exception as e:
                    logger.warning("Error al detener captura en finally: %s", e)
            self.capture_stopped.emit()

    def stop_capture(self):
        """Solicita detener la captura de forma segura."""
        self._is_running = False
        if self._capturer:
            try:
                self._capturer.stop()
            except Exception as e:
                logger.warning("Error al detener captura: %s", e)
