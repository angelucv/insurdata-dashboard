# scripts/run_etl_2023.py
"""
ETL solo año 2023: depuración paso a paso.
Procesa únicamente archivos de data/raw (y data/raw/xlsx) cuyo año sea 2023,
con salida verbose (archivo, loader, filas por archivo).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW
from src.etl.sudeaseg_to_supabase import run_full_pipeline

TARGET_YEAR = 2023


def main():
    parser = argparse.ArgumentParser(description=f"ETL solo año {TARGET_YEAR} (depuración)")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar archivos que se procesarían, sin conectar a Supabase")
    args = parser.parse_args()

    print("=" * 60)
    print(f"ETL — Depuración año {TARGET_YEAR} (solo archivos 2023)")
    print("=" * 60)
    print(f"\nOrigen: {DATA_RAW} (incl. subcarpeta xlsx/)\n")
    if args.dry_run:
        print("  [Modo dry-run: no se cargará a Supabase]\n")

    stats = run_full_pipeline(
        DATA_RAW,
        target_year=TARGET_YEAR,
        debug=True,
        dry_run=args.dry_run,
    )

    print("\n" + "-" * 60)
    print("RESUMEN 2023")
    print("-" * 60)
    print(f"  Archivos Excel procesados: {stats['excel']}")
    print(f"  Archivos PDF procesados:   {stats['pdf']}")
    print(f"  Total filas primas_mensuales cargadas: {stats['primas_rows']}")
    print()
    if stats["primas_rows"] == 0:
        print("  Si no se cargaron filas, revisa que en data/raw/xlsx existan")
        print("  archivos con '2023' en el nombre (ej. resumen-por-empresa-2023.xlsx).")
    print()


if __name__ == "__main__":
    main()
