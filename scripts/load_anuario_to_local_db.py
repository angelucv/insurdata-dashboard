# scripts/load_anuario_to_local_db.py
"""
Carga los CSV del anuario "Seguro en Cifras" (data/staged/{año}/verificadas/) en una
base SQLite local (data/db/local/anuario.db). Una tabla por archivo CSV, con columna
'anio' para poder mezclar varios años en el futuro.

Usa la misma lista de archivos que el índice: scripts/verificar_indice_anuario.py.

Uso: python scripts/load_anuario_to_local_db.py [--year 2023]
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_DB_LOCAL, DATA_STAGED
from scripts.verificar_indice_anuario import INDICE_CSV_POR_CUADRO, ORDEN_CUADROS

DB_PATH = DATA_DB_LOCAL / "anuario.db"
MANIFEST_PATH = DATA_DB_LOCAL / "manifest_carga.json"
SEP = ";"
ENCODING = "utf-8-sig"


def _nombre_tabla(nombre_csv: str) -> str:
    """Nombre de tabla SQL: nombre del CSV sin .csv, solo caracteres válidos."""
    base = nombre_csv.removesuffix(".csv").strip()
    return re.sub(r"[^\w]", "_", base).strip("_") or "tabla"


def _nombre_columna(raw: str) -> str:
    """Convierte cabecera CSV a nombre de columna SQL válido."""
    s = (raw or "").strip().strip('"')
    s = s.replace(" ", "_").replace("%", "pct").replace(".", "_")
    s = re.sub(r"[^\w]", "_", s).strip("_")
    return s or "col"


def _normalizar_columnas(headers: list[str]) -> list[str]:
    """Normaliza y desduplica nombres de columnas."""
    out = []
    seen = set()
    for h in headers:
        name = _nombre_columna(h)
        if name in seen:
            i = 1
            while f"{name}_{i}" in seen:
                i += 1
            name = f"{name}_{i}"
        seen.add(name)
        out.append(name)
    return out


def cargar_csv_en_sqlite(
    conn: sqlite3.Connection,
    csv_path: Path,
    tabla: str,
    anio: int,
) -> int:
    """Crea la tabla si no existe, inserta filas con columna anio. Retorna número de filas."""
    with open(csv_path, encoding=ENCODING, newline="") as f:
        reader = csv.reader(f, delimiter=SEP)
        headers = next(reader, [])
    if not headers:
        return 0
    col_names = _normalizar_columnas(headers)
    cols_sql = ["anio INTEGER NOT NULL"] + [f'"{c}" TEXT' for c in col_names]
    placeholders = ", ".join(["?"] * (1 + len(col_names)))
    columns_insert = "anio, " + ", ".join(f'"{c}"' for c in col_names)

    conn.execute(
        f'CREATE TABLE IF NOT EXISTS "{tabla}" ({", ".join(cols_sql)})'
    )
    conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{tabla}_anio ON "{tabla}"(anio)')
    conn.execute(f'DELETE FROM "{tabla}" WHERE anio = ?', (anio,))

    n = 0
    with open(csv_path, encoding=ENCODING, newline="") as f:
        reader = csv.reader(f, delimiter=SEP)
        next(reader, None)
        cur = conn.cursor()
        for row in reader:
            if len(row) != len(col_names):
                row = row + [""] * (len(col_names) - len(row)) if len(row) < len(col_names) else row[: len(col_names)]
            cur.execute(
                f'INSERT INTO "{tabla}" ({columns_insert}) VALUES ({placeholders})',
                [anio] + [r.strip('"').strip() if isinstance(r, str) else r for r in row],
            )
            n += 1
    return n


def run(anio: int = 2023) -> bool:
    verificadas = DATA_STAGED / str(anio) / "verificadas"
    if not verificadas.exists():
        print(f"[ERROR] No existe {verificadas}")
        return False

    archivos = [
        f for cid in ORDEN_CUADROS for f in INDICE_CSV_POR_CUADRO.get(cid, []) if f
    ]
    manifest = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "anio": anio,
        "origen": str(verificadas),
        "archivos": [],
        "total_tablas": 0,
        "total_filas": 0,
    }

    conn = sqlite3.connect(DB_PATH)
    try:
        for nombre_csv in archivos:
            path = verificadas / nombre_csv
            if not path.exists():
                print(f"  [SKIP] No existe: {nombre_csv}")
                manifest["archivos"].append({"archivo": nombre_csv, "filas": 0, "error": "no_existe"})
                continue
            tabla = _nombre_tabla(nombre_csv)
            try:
                filas = cargar_csv_en_sqlite(conn, path, tabla, anio)
                manifest["archivos"].append({"archivo": nombre_csv, "tabla": tabla, "filas": filas})
                manifest["total_filas"] += filas
                print(f"  {tabla}: {filas} filas")
            except Exception as e:
                print(f"  [ERROR] {nombre_csv}: {e}")
                manifest["archivos"].append({"archivo": nombre_csv, "tabla": tabla, "filas": 0, "error": str(e)})
        conn.commit()
        manifest["total_tablas"] = len([a for a in manifest["archivos"] if a.get("filas", 0) > 0 or a.get("tabla")])
    finally:
        conn.close()

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n  Base: {DB_PATH}")
    print(f"  Manifest: {MANIFEST_PATH}")
    print(f"  Total filas insertadas: {manifest['total_filas']}")
    return True


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Cargar CSV del anuario en SQLite local")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    sys.exit(0 if run(args.year) else 1)
