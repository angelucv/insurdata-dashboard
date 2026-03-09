# scripts/verificar_estructura_carpetas.py
"""
Verifica la estructura de carpetas del ETL: qué existe, qué está vacío y resumen de data/raw/.
Ejecutar desde la raíz del proyecto: python scripts/verificar_estructura_carpetas.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import (
    DATA_RAW,
    DATA_PROCESSED,
    DATA_STAGED,
    DATA_CLEAN,
    DATA_AUDIT,
    DATA_REPLICA,
    DATA_AUDIT_MIRROR,
    DATA_AUDIT_BY_SOURCE,
    DATA_AUDIT_MANIFEST,
)


def count_files(p: Path) -> int:
    """Cuenta archivos en un directorio (recursivo)."""
    if not p.exists() or not p.is_dir():
        return 0
    return sum(1 for f in p.rglob("*") if f.is_file())


def main():
    print("=== VERIFICACIÓN DE ESTRUCTURA DE CARPETAS ===\n")

    # Carpetas de datos
    folders = [
        ("data/raw", DATA_RAW, "Fuente base (PDF, XLSX) - no se borra en reset"),
        ("data/processed", DATA_PROCESSED, "Salida lista para dashboard / Supabase"),
        ("data/staged", DATA_STAGED, "Una salida por archivo fuente, por año"),
        ("data/clean", DATA_CLEAN, "Compilado por año, validado"),
        ("data/audit", DATA_AUDIT, "Trazabilidad (by_source, manifest)"),
        ("data/replica_db", DATA_REPLICA, "Replica local de la BD (auditar antes de subir)"),
    ]
    for name, path, desc in folders:
        n = count_files(path)
        status = "OK (con archivos)" if n > 0 else "vacía"
        print(f"  {name:22} {n:>5} archivos  [{status}]  — {desc}")

    # Subcarpetas de raw (resumen)
    print("\n--- Contenido de data/raw/ ---")
    if DATA_RAW.exists():
        for sub in sorted(DATA_RAW.iterdir()):
            if sub.is_dir():
                n = count_files(sub)
                ext = " (solo PDF/XLSX aquí)" if sub.name in ("pdf", "xlsx") else ""
                print(f"  raw/{sub.name}/   {n:>4} archivos{ext}")
        root_files = [f for f in DATA_RAW.iterdir() if f.is_file()]
        if root_files:
            print(f"  raw/ (raíz)        {len(root_files):>4} archivos")
    else:
        print("  data/raw no existe.")

    # Subcarpetas de audit
    print("\n--- Subcarpetas de data/audit/ ---")
    if DATA_AUDIT.exists():
        for sub in [DATA_AUDIT_MIRROR, DATA_AUDIT_BY_SOURCE, DATA_AUDIT_MANIFEST]:
            rel = sub.relative_to(DATA_AUDIT) if sub.exists() else sub.name
            n = count_files(sub) if sub.exists() else 0
            print(f"  audit/{rel}   {n:>4} archivos")
    else:
        print("  data/audit no existe.")

    print("\n  Para reset (dejar solo raw): python scripts/reset_etl_mantener_raw.py")
    print("  Proceso con auditoria:        docs/PROPUESTA_ETL_AUDITORIA_Y_REPLICA_LOCAL.md")


if __name__ == "__main__":
    main()
