"""Rutas de la réplica local de la base de datos (mismo esquema que Supabase)."""
from pathlib import Path

from config.settings import DATA_REPLICA

# Archivos por tabla (Parquet para consistencia con clean/ y fácil lectura en pandas)
REPLICA_ENTITIES = DATA_REPLICA / "entities.parquet"
REPLICA_PRIMAS_MENSUALES = DATA_REPLICA / "primas_mensuales.parquet"
REPLICA_EXCHANGE_RATES = DATA_REPLICA / "exchange_rates.parquet"
REPLICA_MARGEN_SOLVENCIA = DATA_REPLICA / "margen_solvencia.parquet"
REPLICA_SERIES_HISTORICAS = DATA_REPLICA / "series_historicas.parquet"

# Manifest y reporte de auditoría de la réplica
REPLICA_MANIFEST_JSON = DATA_REPLICA / "manifest_replica.json"
REPLICA_AUDITORIA_TXT = DATA_REPLICA / "auditoria_replica.txt"

# Lista de tablas y sus rutas (para iterar)
REPLICA_TABLES = {
    "entities": REPLICA_ENTITIES,
    "primas_mensuales": REPLICA_PRIMAS_MENSUALES,
    "exchange_rates": REPLICA_EXCHANGE_RATES,
    "margen_solvencia": REPLICA_MARGEN_SOLVENCIA,
    "series_historicas": REPLICA_SERIES_HISTORICAS,
}


def ensure_replica_dir() -> None:
    """Crea el directorio de la réplica si no existe."""
    DATA_REPLICA.mkdir(parents=True, exist_ok=True)
