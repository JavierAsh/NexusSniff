"""
test_export_manager.py — Tests para el gestor de exportación.

Verifica que CSV y JSON se exportan correctamente con
manejo de errores para disco lleno o rutas inválidas.
"""

import pytest
import csv
import json
import os
from pathlib import Path
from unittest.mock import patch

from app.core.export_manager import ExportManager


def _make_packets(count: int = 5) -> list:
    """Genera una lista de paquetes de prueba."""
    return [
        {
            'number': i,
            'timestamp': 1000.0 + i * 0.001,
            'length': 64 + i,
            'protocol': 'TCP' if i % 2 == 0 else 'UDP',
            'src_ip': '192.168.1.1',
            'dst_ip': '10.0.0.1',
            'src_port': 12345 + i,
            'dst_port': 80,
            'src_mac': 'aa:bb:cc:dd:ee:ff',
            'dst_mac': '11:22:33:44:55:66',
            'info': f'Packet {i}',
            'raw_data': b'\x00' * (64 + i),
        }
        for i in range(count)
    ]


class TestExportCSV:
    """Tests para exportación CSV."""

    def test_csv_creates_file(self, tmp_path):
        """export_csv crea un archivo CSV válido."""
        filepath = str(tmp_path / "test_export.csv")
        packets = _make_packets(3)

        with patch('app.core.export_manager.QFileDialog.getSaveFileName',
                   return_value=(filepath, '')):
            result = ExportManager.export_csv(packets)

        assert result is True
        assert os.path.exists(filepath)

        # Verificar contenido
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]['protocol'] == 'TCP'
        assert rows[1]['protocol'] == 'UDP'

    def test_csv_cancelled(self):
        """Si el usuario cancela, retorna False."""
        with patch('app.core.export_manager.QFileDialog.getSaveFileName',
                   return_value=('', '')):
            result = ExportManager.export_csv([])
        assert result is False

    def test_csv_invalid_path(self):
        """Error de escritura muestra mensaje (no crash)."""
        with patch('app.core.export_manager.QFileDialog.getSaveFileName',
                   return_value=('/invalid/path/that/does/not/exist/file.csv', '')):
            with patch('app.core.export_manager.QMessageBox'):
                result = ExportManager.export_csv(_make_packets())
        assert result is False


class TestExportJSON:
    """Tests para exportación JSON."""

    def test_json_creates_file(self, tmp_path):
        """export_json crea un archivo JSON válido."""
        filepath = str(tmp_path / "test_export.json")
        packets = _make_packets(3)

        with patch('app.core.export_manager.QFileDialog.getSaveFileName',
                   return_value=(filepath, '')):
            result = ExportManager.export_json(packets)

        assert result is True
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]['protocol'] == 'TCP'
        # raw_data debe estar excluido
        assert 'raw_data' not in data[0]

    def test_json_cancelled(self):
        """Si el usuario cancela, retorna False."""
        with patch('app.core.export_manager.QFileDialog.getSaveFileName',
                   return_value=('', '')):
            result = ExportManager.export_json([])
        assert result is False
