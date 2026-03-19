import pytest
from unittest.mock import MagicMock, patch
from app.core.capture_worker import packet_to_dict, CaptureWorker

# ==========================================
# Fixtures compartidas
# ==========================================
@pytest.fixture
def paquete_valido_mock():
    """Mock de un paquete C++ válido devuelto por el motor Nexus."""
    pkt = MagicMock()
    pkt.number = 1
    pkt.timestamp = 1622543210.123
    pkt.length = 64
    pkt.protocol_name = "TCP"
    pkt.src_ip_str = "192.168.1.10"
    pkt.dst_ip_str = "10.0.0.1"
    pkt.src_port = 443
    pkt.dst_port = 54321
    pkt.src_mac_str = "00:11:22:33:44:55"
    pkt.dst_mac_str = "AA:BB:CC:DD:EE:FF"
    pkt.info = "TCP Port 443"
    pkt.raw_data = [255, 255, 255] # bytes() valid iterables
    
    # Flags booleanos
    pkt.has_ethernet = True
    pkt.has_ipv4 = True
    pkt.has_tcp = True
    pkt.has_udp = False
    pkt.has_icmp = False
    pkt.has_arp = False
    
    # Capas internas anidadas
    pkt.ethernet = MagicMock(ethertype=0x0800)
    pkt.ipv4 = MagicMock(version=4, ihl=5, ttl=64, total_length=50, identification=123, protocol=6, checksum=0x1111)
    pkt.tcp = MagicMock(src_port=443, dst_port=54321, seq_number=1000, ack_number=2000, flags=0x02, window_size=8192, checksum=0x2222)
    return pkt


# ==========================================
# Categoría 1: Happy path
# ==========================================
class TestHappyPath:
    """Pruebas del flujo normal esperado (Happy path)"""
    
    def test_deberia_convertir_paquete_valido_a_diccionario_correctamente(self, paquete_valido_mock):
        """Verifica que el mapeador convierte los atributos correctamente cuando el paquete está bien formado."""
        resultado = packet_to_dict(paquete_valido_mock)
        
        assert resultado['number'] == 1
        assert resultado['protocol'] == "TCP"
        assert resultado['raw_data'] == bytes([255, 255, 255])
        assert resultado['tcp']['dst_port'] == 54321
        assert resultado['ipv4']['version'] == 4
        # Capas UDP e ICMP no deberían estar ya que sus flags son Falsos
        assert 'udp' not in resultado
        assert 'icmp' not in resultado

    def test_deberia_configurar_parametros_del_worker_correctamente(self):
        """Un worker recién configurado debería almacenar su interfaz y su filtro."""
        worker = CaptureWorker()
        worker.configure("eth0", "tcp port 80")
        
        assert worker._interface_name == "eth0"
        assert worker._bpf_filter == "tcp port 80"
        assert worker.is_running is False


# ==========================================
# Categoría 2: Edge cases
# ==========================================
class TestEdgeCases:
    """Pruebas extremas, nulos, vacíos y caracteres inusuales."""
    
    def test_deberia_manejar_paquete_sin_capas_ni_datos(self):
        """Verifica que un paquete vacío o corrupto que no tiene protocolos válidos no rompe la conversión."""
        pkt = MagicMock()
        pkt.number = 0
        pkt.timestamp = 0.0
        pkt.length = 0
        pkt.protocol_name = ""
        pkt.src_ip_str = ""
        pkt.dst_ip_str = ""
        pkt.src_port = 0
        pkt.dst_port = 0
        pkt.src_mac_str = ""
        pkt.dst_mac_str = ""
        pkt.info = ""
        pkt.raw_data = [] # Data vacía
        pkt.has_ethernet = False
        pkt.has_ipv4 = False
        pkt.has_tcp = False
        pkt.has_udp = False
        pkt.has_icmp = False
        pkt.has_arp = False
        
        resultado = packet_to_dict(pkt)
        
        assert resultado['number'] == 0
        assert resultado['protocol'] == ""
        assert len(resultado['raw_data']) == 0
        assert 'ethernet' not in resultado
        assert 'ipv4' not in resultado

    def test_deberia_manejar_paquete_con_caracteres_especiales_y_valores_extremos(self):
        """Inyecta emojis, caracteres de control, longitudes imposibles y negativos."""
        pkt = MagicMock()
        pkt.number = 999999999999  # Integer extremandamente grande
        pkt.timestamp = -1.5
        pkt.length = 65535
        pkt.protocol_name = "X" * 1000  # String largo
        pkt.src_ip_str = "255.255.255.255"
        pkt.dst_ip_str = "0.0.0.0"
        pkt.src_port = 65535
        pkt.dst_port = -1           # Puerto negativo inválido
        pkt.src_mac_str = "FF:FF:FF:FF:FF:FF"
        pkt.dst_mac_str = "00:00:00:00:00:00"
        pkt.info = "👾¡Të$t!👾\n\t <script>alert(1)</script>" # Inyección / especial
        pkt.raw_data = [65] * 10485  # ~10KB limit
        
        pkt.has_ethernet = False; pkt.has_ipv4 = False; pkt.has_tcp = False
        pkt.has_udp = False; pkt.has_icmp = False; pkt.has_arp = False

        resultado = packet_to_dict(pkt)
        
        assert resultado['number'] == 999999999999
        assert "👾¡Të$t!👾" in resultado['info']
        assert len(resultado['protocol']) == 1000
        assert len(resultado['raw_data']) == 10485
        assert resultado['dst_port'] == -1

    def test_deberia_ignorar_objetos_presentes_si_las_banderas_booleanas_indican_falso(self):
        """Aun si pkt.udp existe en memoria, si has_udp es falso, la capa no se debe serializar."""
        pkt = MagicMock()
        pkt.has_ethernet = False; pkt.has_ipv4 = False; pkt.has_tcp = False
        pkt.has_udp = False; pkt.has_icmp = False; pkt.has_arp = False
        
        # Simulamos que C++ tiene la capa asignada accidentalmente
        pkt.udp = MagicMock(src_port=1, dst_port=2, length=3, checksum=4)
        
        resultado = packet_to_dict(pkt)
        
        # El validador Python debe de guiarse estrictamente por los booleanos
        assert 'udp' not in resultado


# ==========================================
# Categoría 3: Gestión de errores
# ==========================================
class TestErrorHandling:
    """El sistema falla controladamente donde y cuando es necesario."""

    def test_deberia_arrojar_excepcion_al_procesar_nulo_o_tipo_incorrecto(self):
        """packet_to_dict no valida tipos internamente por rendimiento. Debería arrojar AttributeError."""
        # Se asume que no hay checks null antes (para acelerar rendimiento) 
        # y que se confía ciegamente en AttributeError si llega un None.
        with pytest.raises(AttributeError):
            packet_to_dict(None)
            
        with pytest.raises(AttributeError):
            packet_to_dict("este_no_es_un_objeto_struct")

    def test_deberia_emitir_signal_error_si_motor_c_estalla_en_carga(self):
        """Verifica que capture_error reacciona sin matar el GUI si nexus_engine.pyd falta."""
        worker = CaptureWorker()
        worker.capture_error = MagicMock()
        
        # Ocultamos temporalmente el módulo C++
        with patch.dict('sys.modules', {'app.nexus_engine': None}):
            worker.run()
            
        # El hilo nunca debió bloquear la app. Debió atrapar el ImportError vía signal
        worker.capture_error.emit.assert_called_once()
        error_msg = worker.capture_error.emit.call_args[0][0]
        assert "No se pudo cargar app.nexus_engine.pyd" in error_msg


# ==========================================
# Categoría 4: Integraciones (Mocks)
# ==========================================
class TestIntegracionExterna:
    """Se reemplaza el backend de C++ por completo para observar transacciones IPC."""

    @patch('app.core.capture_worker.CaptureWorker.msleep')
    @patch('app.core.capture_worker.time.monotonic', side_effect=[1.0, 1.0, 2.0, 2.0]) 
    def test_deberia_lanzar_motor_c_vincular_señales_y_extraer_batch_exitosamente(self, mock_monotonic, mock_msleep):
        """Simula la integración entre CaptureWorker (PyQt) y nexus_engine (cpp)."""
        worker = CaptureWorker()
        
        # Mocks para señales de PyQt6
        worker.capture_error = MagicMock()
        worker.capture_started = MagicMock()
        worker.capture_stopped = MagicMock()
        worker.new_packets = MagicMock()
        worker.stats_updated = MagicMock()
        worker.configure("eth1", "udp port 53")
        
        # Estructura e instanciación de dependencias externas (Nexus Engine C++)
        mock_engine = MagicMock()
        mock_capturer_instance = MagicMock()
        
        # Comportamientos del motor simulados
        mock_capturer_instance.start.return_value = True
        mock_capturer_instance.is_capturing.side_effect = [True, False] # Ejecuta un loop y cierra
        mock_capturer_instance.get_packets.return_value = ["mock_pkt1", "mock_pkt2"]
        mock_engine.PacketCapturer.return_value = mock_capturer_instance
        
        with patch.dict('sys.modules', {'app.nexus_engine': mock_engine}):
            worker.run()
            
        # 1. Asegurar que configuró correctamente C++
        mock_capturer_instance.start.assert_called_once_with("eth1", "udp port 53")
        # 2. Asegurar que extrae lotes
        mock_capturer_instance.get_packets.assert_called_with(500)
        # 3. Asegurar que no hubo problemas
        worker.capture_error.emit.assert_not_called()
        worker.capture_started.emit.assert_called_once()
        worker.capture_stopped.emit.assert_called_once()
        
        # 4. Asegurar que emitió los paquetes recolectados al GUI
        worker.new_packets.emit.assert_called_once_with(["mock_pkt1", "mock_pkt2"])
        
    @patch('app.core.capture_worker.CaptureWorker.msleep')
    def test_deberia_detener_motor_c_apropiadamente(self, mock_msleep):
        """Verifica que el método stop_capture notifique limpiamente a C++ y setee su bandera is_running a falso."""
        worker = CaptureWorker()
        worker._capturer = MagicMock()
        worker._is_running = True
        
        # Acción
        worker.stop_capture()
        
        # Validación integral
        assert worker._is_running is False
        worker._capturer.stop.assert_called_once() 
