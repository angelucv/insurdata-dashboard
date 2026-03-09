# scripts/crear_replica_local_anuario_tematico.py
"""
Crea la réplica local SQLite con la estructura temática (anuario_cuadros + 23 tablas).
Ejecuta el DDL en data/db/schema/sqlite/001_anuario_local.sql sobre data/db/local/anuario_tematico.db.

Uso: python scripts/crear_replica_local_anuario_tematico.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DDL = ROOT / "data" / "db" / "schema" / "sqlite" / "001_anuario_local.sql"
DB = ROOT / "data" / "db" / "local" / "anuario_tematico.db"

def main() -> int:
    if not DDL.exists():
        print(f"No se encuentra {DDL}")
        return 1
    DB.parent.mkdir(parents=True, exist_ok=True)
    sql = DDL.read_text(encoding="utf-8")
    conn = sqlite3.connect(DB)
    try:
        conn.executescript(sql)
        conn.commit()
        cur = conn.execute("SELECT count(*) FROM anuario_cuadros")
        n = cur.fetchone()[0]
        print(f"Réplica local creada: {DB}")
        print(f"  anuario_cuadros: {n} filas")
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'anuario_%' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        print(f"  Tablas temáticas: {len(tables)}")
    finally:
        conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
