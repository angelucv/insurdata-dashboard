# Solo lectura: muestra la estructura de data/db/local/anuario.db
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "db" / "local" / "anuario.db"
if not DB.exists():
    print("No existe anuario.db. Ejecuta: python scripts/load_anuario_to_local_db.py --year 2023")
    exit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"Total tablas: {len(tables)}\n")
for t in tables:
    cur.execute(f'PRAGMA table_info("{t}")')
    cols = [r[1] for r in cur.fetchall()]
    print(f"  {t}")
    print(f"    columnas: {cols}\n")
conn.close()
