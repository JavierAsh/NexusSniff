"""
db_manager.py — Conexiones a bases de datos con flush asíncrono.

Gestiona conexiones opcionales a PostgreSQL (sesiones, filtros),
ClickHouse (paquetes históricos) y Redis (cache de stats).

La persistencia se activa si las variables de entorno DB están
configuradas. El flush a ClickHouse corre en un hilo background
para no bloquear la captura ni la UI.
"""

import os
import logging
import threading
import queue
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Configuración leída de variables de entorno para evitar exposición de secrets
DB_CONFIG = {
    'postgres': {
        'host': os.getenv('NEXUS_PG_HOST', 'localhost'),
        'port': int(os.getenv('NEXUS_PG_PORT', '5432')),
        'database': os.getenv('NEXUS_PG_DB', 'nexussniff'),
        'user': os.getenv('NEXUS_PG_USER', 'nexus'),
        'password': os.getenv('NEXUS_PG_PASSWORD', ''),
    },
    'clickhouse': {
        'host': os.getenv('NEXUS_CH_HOST', 'localhost'),
        'port': int(os.getenv('NEXUS_CH_PORT', '9000')),
        'database': os.getenv('NEXUS_CH_DB', 'nexussniff'),
        'user': os.getenv('NEXUS_CH_USER', 'nexus'),
        'password': os.getenv('NEXUS_CH_PASSWORD', ''),
    },
    'redis': {
        'host': os.getenv('NEXUS_REDIS_HOST', 'localhost'),
        'port': int(os.getenv('NEXUS_REDIS_PORT', '6379')),
        'password': os.getenv('NEXUS_REDIS_PASSWORD', ''),
        'db': int(os.getenv('NEXUS_REDIS_DB', '0')),
    }
}

# Habilitar persistencia si alguna DB está configurada explícitamente
DB_ENABLED = bool(os.getenv('NEXUS_PG_HOST') or os.getenv('NEXUS_CH_HOST'))


class DatabaseManager:
    """
    Gestor centralizado de conexiones a base de datos.

    Incluye un hilo de flush asíncrono para enviar batches de paquetes
    a ClickHouse sin bloquear la captura.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or DB_CONFIG
        self._pg_conn = None
        self._ch_client = None
        self._redis_client = None

        # Flush queue para ClickHouse (thread-safe)
        self._flush_queue: queue.Queue = queue.Queue(maxsize=100)
        self._flush_thread: Optional[threading.Thread] = None
        self._flush_running = False

    # ─────────────────────────────────────────────────────
    # Conexiones
    # ─────────────────────────────────────────────────────

    def connect_postgres(self) -> bool:
        """Conecta a PostgreSQL."""
        try:
            import psycopg2
            cfg = self._config['postgres']
            self._pg_conn = psycopg2.connect(
                host=cfg['host'],
                port=cfg['port'],
                dbname=cfg['database'],
                user=cfg['user'],
                password=cfg['password']
            )
            self._pg_conn.autocommit = True
            self._init_postgres_schema()
            logger.info("Conectado a PostgreSQL en %s:%s", cfg['host'], cfg['port'])
            return True
        except Exception as e:
            logger.error("Error conectando a PostgreSQL: %s", e)
            return False

    def connect_clickhouse(self) -> bool:
        """Conecta a ClickHouse."""
        try:
            from clickhouse_driver import Client
            cfg = self._config['clickhouse']
            self._ch_client = Client(
                host=cfg['host'],
                port=cfg['port'],
                database=cfg['database'],
                user=cfg['user'],
                password=cfg['password']
            )
            self._init_clickhouse_schema()
            logger.info("Conectado a ClickHouse en %s:%s", cfg['host'], cfg['port'])
            return True
        except Exception as e:
            logger.error("Error conectando a ClickHouse: %s", e)
            return False

    def connect_redis(self) -> bool:
        """Conecta a Redis."""
        try:
            import redis
            cfg = self._config['redis']
            self._redis_client = redis.Redis(
                host=cfg['host'],
                port=cfg['port'],
                password=cfg['password'],
                db=cfg['db'],
                decode_responses=True
            )
            self._redis_client.ping()
            logger.info("Conectado a Redis en %s:%s", cfg['host'], cfg['port'])
            return True
        except Exception as e:
            logger.error("Error conectando a Redis: %s", e)
            return False

    # ─────────────────────────────────────────────────────
    # Esquemas
    # ─────────────────────────────────────────────────────

    def _init_postgres_schema(self):
        """Crea las tablas en PostgreSQL si no existen."""
        if not self._pg_conn:
            return

        with self._pg_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS capture_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    interface_name VARCHAR(255),
                    bpf_filter TEXT,
                    started_at TIMESTAMP DEFAULT NOW(),
                    ended_at TIMESTAMP,
                    total_packets BIGINT DEFAULT 0,
                    total_bytes BIGINT DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'running'
                );

                CREATE TABLE IF NOT EXISTS filter_rules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    bpf_expression TEXT,
                    display_filter TEXT,
                    color_tag VARCHAR(7),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

    def _init_clickhouse_schema(self):
        """Crea las tablas en ClickHouse si no existen."""
        if not self._ch_client:
            return

        self._ch_client.execute("""
            CREATE TABLE IF NOT EXISTS packets (
                id UInt64,
                session_id String,
                timestamp DateTime64(6),
                length UInt32,
                src_mac String,
                dst_mac String,
                src_ip String,
                dst_ip String,
                src_port UInt16,
                dst_port UInt16,
                protocol String,
                info String
            ) ENGINE = MergeTree()
            ORDER BY (session_id, timestamp)
        """)

    # ─────────────────────────────────────────────────────
    # Flush asíncrono (background thread)
    # ─────────────────────────────────────────────────────

    def start_async_flush(self):
        """Inicia el hilo de flush asíncrono para ClickHouse."""
        if self._flush_running:
            return
        self._flush_running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            name="NexusDB-Flush",
            daemon=True
        )
        self._flush_thread.start()
        logger.info("Hilo de flush asíncrono iniciado")

    def stop_async_flush(self):
        """Detiene el hilo de flush y procesa los pendientes."""
        self._flush_running = False
        if self._flush_thread and self._flush_thread.is_alive():
            # Enviar sentinel para despertar el hilo
            self._flush_queue.put(None)
            self._flush_thread.join(timeout=5.0)
            logger.info("Hilo de flush asíncrono detenido")

    def enqueue_packets(self, session_id: str, packets: List[Dict[str, Any]]):
        """Encola un batch de paquetes para flush asíncrono."""
        if not self._flush_running:
            return
        try:
            self._flush_queue.put_nowait((session_id, packets))
        except queue.Full:
            logger.warning("Cola de flush llena, descartando batch de %d paquetes", len(packets))

    def _flush_loop(self):
        """Loop del hilo de flush — procesa batches de la cola."""
        while self._flush_running:
            try:
                item = self._flush_queue.get(timeout=1.0)
                if item is None:
                    break  # Sentinel de parada
                session_id, packets = item
                self._save_packets_batch(session_id, packets)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error en flush asíncrono: %s", e)

        # Vaciar cola restante antes de salir
        while not self._flush_queue.empty():
            try:
                item = self._flush_queue.get_nowait()
                if item is not None:
                    session_id, packets = item
                    self._save_packets_batch(session_id, packets)
            except (queue.Empty, Exception):
                break

    def _save_packets_batch(self, session_id: str, packets: List[Dict[str, Any]]):
        """Guarda un batch de paquetes en ClickHouse."""
        if not self._ch_client or not packets:
            return

        rows = []
        for pkt in packets:
            rows.append({
                'id': pkt.get('number', 0),
                'session_id': session_id,
                'timestamp': pkt.get('timestamp', 0),
                'length': pkt.get('length', 0),
                'src_mac': pkt.get('src_mac', ''),
                'dst_mac': pkt.get('dst_mac', ''),
                'src_ip': pkt.get('src_ip', ''),
                'dst_ip': pkt.get('dst_ip', ''),
                'src_port': pkt.get('src_port', 0),
                'dst_port': pkt.get('dst_port', 0),
                'protocol': pkt.get('protocol', 'Unknown'),
                'info': pkt.get('info', ''),
            })

        try:
            self._ch_client.execute(
                'INSERT INTO packets VALUES',
                rows
            )
        except Exception as e:
            logger.error("Error insertando batch en ClickHouse: %s", e)

    # ─────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────

    def close(self):
        """Cierra todas las conexiones y detiene el flush."""
        self.stop_async_flush()
        if self._pg_conn:
            try:
                self._pg_conn.close()
            except Exception:
                pass
        if self._redis_client:
            try:
                self._redis_client.close()
            except Exception:
                pass
        logger.info("DatabaseManager cerrado")
