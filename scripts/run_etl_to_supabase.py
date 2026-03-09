# scripts/run_etl_to_supabase.py
"""ETL: procesa data/raw (incl. data/raw/xlsx) y carga a Supabase. Modo depuración por año."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW, ETL_TARGET_YEAR, ETL_DEBUG
from src.etl.sudeaseg_to_supabase import run_full_pipeline


def main():
    parser = argparse.ArgumentParser(description="ETL: data/raw -> Supabase (depurar un año con --year y --debug)")
    parser.add_argument("--year", type=int, default=None, help="Procesar solo este año (ej: 2023). Sustituye --year-min/max.")
    parser.add_argument("--year-min", type=int, default=None, help="Rango: año mínimo (con --year-max)")
    parser.add_argument("--year-max", type=int, default=None, help="Rango: año máximo (con --year-min)")
    parser.add_argument("--debug", action="store_true", help="Modo depuración: listar archivo, loader y filas por archivo")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar archivos a procesar, sin conectar a Supabase")
    args = parser.parse_args()

    target_year = args.year or ETL_TARGET_YEAR
    year_min = year_max = None
    if target_year is not None:
        year_min, year_max = target_year, target_year
        print(f"ETL: modo un solo año = {target_year} (depuración).")
    elif args.year_min is not None and args.year_max is not None:
        year_min, year_max = args.year_min, args.year_max
        print(f"ETL: rango de años [{year_min}, {year_max}].")
    elif (args.year_min is not None) != (args.year_max is not None):
        print("Indica ambos --year-min y --year-max, o usa --year 2023.")
        return

    debug = args.debug or (target_year is not None and ETL_DEBUG)
    if debug:
        print("  [DEBUG] Verbose: se listará cada archivo, loader y filas.\n")

    stats = run_full_pipeline(
        DATA_RAW,
        year_min=year_min,
        year_max=year_max,
        target_year=target_year,
        debug=debug,
        dry_run=args.dry_run,
    )
    print(f"\nResumen: {stats['excel']} Excel, {stats['pdf']} PDF -> {stats['primas_rows']} filas en primas_mensuales.")
    if stats.get("primas_rows"):
        print("Refresca el dashboard para ver los datos.")


if __name__ == "__main__":
    main()
