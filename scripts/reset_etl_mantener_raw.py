# scripts/reset_etl_mantener_raw.py
"""
Reinicia el ETL desde cero: borra todos los datos procesados y salidas intermedias,
manteniendo intactos los datos crudos en data/raw/.

Elimina:
  - data/processed/   (Parquet de salida para dashboard/Supabase)
  - data/staged/      (CSV/Parquet por archivo fuente, por año)
  - data/clean/       (Compilado por año listo para cargar)
  - data/audit/       (by_source, manifest)
  - data/replica_db/  (réplica local de la BD; se borra para rehacer desde clean)

No toca:
  - data/raw/         (PDF, XLSX crudos — se conservan)

Para vaciar también Supabase (cuando el proyecto esté activo):
  1. En Supabase Dashboard → SQL Editor, ejecutar src/db/truncate_all.sql
  2. O: python scripts/truncate_supabase.py (si las políticas lo permiten)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW, DATA_PROCESSED, DATA_STAGED, DATA_CLEAN, DATA_AUDIT, DATA_REPLICA


def rm_tree(p: Path) -> int:
    """Borra el contenido de un directorio (y sus subdirectorios). No borra el directorio raíz. Devuelve nº de items eliminados."""
    if not p.is_dir():
        return 0
    count = 0
    for child in list(p.iterdir()):
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
            count += 1
        else:
            try:
                child.unlink()
                count += 1
            except OSError:
                pass
    return count


def main():
    print("=== RESET ETL — Mantener solo datos crudos (data/raw/) ===\n")

    # Resumen de raw (no se toca)
    raw_files = list(DATA_RAW.rglob("*"))
    raw_files = [f for f in raw_files if f.is_file()]
    print(f"  data/raw/ (NO se modifica): {len(raw_files)} archivos")
    for f in sorted(raw_files)[:15]:
        print(f"    - {f.relative_to(DATA_RAW)}")
    if len(raw_files) > 15:
        print(f"    ... y {len(raw_files) - 15} más")

    dirs_to_clear = [
        ("data/processed", DATA_PROCESSED),
        ("data/staged", DATA_STAGED),
        ("data/clean", DATA_CLEAN),
        ("data/audit", DATA_AUDIT),
        ("data/replica_db", DATA_REPLICA),
    ]
    total_removed = 0
    for name, path in dirs_to_clear:
        if not path.exists():
            print(f"\n  {name}: (no existe)")
            continue
        n = rm_tree(path)
        total_removed += n
        print(f"\n  {name}: eliminados {n} archivos/carpetas")

    print(f"\n  Total eliminado: {total_removed} elementos.")
    print("\n  Las carpetas processed, staged, clean, audit y replica_db quedan vacias.")
    print("  Proceso recomendado (con auditoria y replica local):")
    print("    Ver docs/PROPUESTA_ETL_AUDITORIA_Y_REPLICA_LOCAL.md")
    print("    1. raw -> audit/by_source -> staged -> clean -> replica_db -> auditar -> Supabase")


if __name__ == "__main__":
    main()
