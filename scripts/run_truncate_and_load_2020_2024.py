# scripts/run_truncate_and_load_2020_2024.py
"""
Vacía todas las tablas en Supabase y carga únicamente datos del periodo 2020-2024
para verificar consistencia de la conversión en ese rango.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW
from src.db import get_supabase_client
from src.etl.sudeaseg_to_supabase import run_full_pipeline

YEAR_MIN = 2020
YEAR_MAX = 2024


def truncate_all(sb) -> bool:
    """Vacía las tablas de datos en Supabase (borra por lotes)."""
    tables = ["primas_mensuales", "margen_solvencia", "series_historicas", "exchange_rates", "entities"]
    for table in tables:
        try:
            total_deleted = 0
            while True:
                r = sb.table(table).select("id", count="exact").limit(1000).execute()
                if not r.data or len(r.data) == 0:
                    break
                ids = [row["id"] for row in r.data]
                sb.table(table).delete().in_("id", ids).execute()
                total_deleted += len(ids)
            print(f"  {table}: vaciada" + (f" ({total_deleted} filas borradas)" if total_deleted else ""))
        except Exception as e:
            print(f"  {table}: error - {e}")
            print("  Si falla por políticas RLS, ejecuta en Supabase SQL Editor:")
            print("  Ver contenido de: src/db/truncate_all.sql")
            return False
    return True


def main():
    print("=" * 60)
    print("Vaciar BD y cargar solo periodo 2020-2024 (verificación)")
    print("=" * 60)

    sb = get_supabase_client()
    if not sb:
        print("\nSupabase no configurado. Define SUPABASE_URL y SUPABASE_KEY en .env")
        return

    print("\n1) Vaciar tablas en Supabase...")
    if not truncate_all(sb):
        print("No se pudo vaciar. Revisa políticas DELETE o ejecuta truncate_all.sql en el SQL Editor.")
        return

    print("\n2) Cargar solo archivos con año en [2020, 2024] desde data/raw...")
    stats = run_full_pipeline(DATA_RAW, year_min=YEAR_MIN, year_max=YEAR_MAX)
    print(f"\nResumen: {stats['excel']} Excel, {stats['pdf']} PDF -> {stats['primas_rows']} filas en primas_mensuales.")

    if stats["primas_rows"]:
        print("\n3) Siguiente paso: verificar consistencia con scripts/verificar_carga.py o verificar_consistencia_datos_convertidos.py")
    else:
        print("\nNo se cargaron filas. Comprueba que en data/raw haya Excel/PDF con 2020, 2021, 2022, 2023 o 2024 en el nombre del archivo.")
    print()


if __name__ == "__main__":
    main()
