"""
db_manager.py — Conexiones a bases de datos.

Gestiona conexiones a PostgreSQL (sesiones, filtros),
ClickHouse (paquetes históricos) y Redis (cache de stats).
"""

import os
from typing import Optional, Dict, Any, List

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


class DatabaseManager:
    """Gestor centralizado de conexiones a base de datos."""

    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or DB_CONFIG
        self._pg_conn = None
        self._ch_client = None
        self._redis_client = None

    def connect_postgres(self):
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
            return True
        except Exception as e:
            print(f"[DB] Error conectando a PostgreSQL: {e}")
            return False

    def connect_clickhouse(self):
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
            return True
        except Exception as e:
            print(f"[DB] Error conectando a ClickHouse: {e}")
            return False

    def connect_redis(self):
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
            return True
        except Exception as e:
            print(f"[DB] Error conectando a Redis: {e}")
            return False

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

    def save_packets_batch(self, session_id: str, packets: List[Dict[str, Any]]):
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

        self._ch_client.execute(
            'INSERT INTO packets VALUES',
            rows
        )

    def close(self):
        """Cierra todas las conexiones."""
        if self._pg_conn:
            self._pg_conn.close()
        if self._redis_client:
            self._redis_client.close()
