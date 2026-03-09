# src/db/client.py
"""Cliente Supabase y utilidades de carga de datos."""
from typing import Any

import pandas as pd

from config.settings import SUPABASE_URL, SUPABASE_KEY


def get_supabase_client():
    """Devuelve el cliente de Supabase si hay URL y KEY configurados (schema public)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[DB] Error creando cliente Supabase: {e}")
        return None


def get_supabase_anuario_client():
    """Cliente Supabase con schema anuario (Seguro en Cifras). Requiere exponer schema anuario en API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        from supabase.lib.client_options import SyncClientOptions
        opts = SyncClientOptions(schema="anuario")
        return create_client(SUPABASE_URL, SUPABASE_KEY, options=opts)
    except Exception as e:
        print(f"[DB] Error creando cliente Supabase anuario: {e}")
        return None


def load_df_into_table(
    df: pd.DataFrame,
    table: str,
    client: Any | None = None,
    chunk_size: int = 500,
) -> int:
    """
    Inserta un DataFrame en una tabla de Supabase por lotes.
    Retorna número de filas insertadas.
    """
    sb = client or get_supabase_client()
    if sb is None:
        print("[DB] Supabase no configurado. No se cargaron datos.")
        return 0
    records = df.replace({pd.NA: None}).to_dict("records")
    if not records:
        return 0
    total = 0
    try:
        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            sb.table(table).insert(chunk).execute()
            total += len(chunk)
        return total
    except Exception as e:
        print(f"[DB] Error insertando en {table}: {e}")
        return total
