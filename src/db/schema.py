# src/db/schema.py
"""Exporta el SQL del esquema para ejecución en Supabase."""
from pathlib import Path

_SCHEMA_FILE = Path(__file__).parent / "schema.sql"
SCHEMA_SQL = _SCHEMA_FILE.read_text(encoding="utf-8") if _SCHEMA_FILE.exists() else ""
