# scripts/truncate_supabase.py
"""Vacía las tablas de datos en Supabase (empezar de cero). Requiere políticas DELETE o service_role."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import get_supabase_client


def main():
    sb = get_supabase_client()
    if not sb:
        print("Supabase no configurado (.env)")
        return
    # Supabase REST no permite TRUNCATE directo; hay que borrar por filas o usar SQL.
    # Opción 1: ejecutar SQL si el cliente lo soporta (supabase-py no expone .rpc('exec_sql') fácil).
    # Opción 2: borrar en lotes con .delete() (necesita política DELETE).
    tables = ["primas_mensuales", "margen_solvencia", "series_historicas", "exchange_rates", "entities"]
    for table in tables:
        try:
            while True:
                r = sb.table(table).select("id", count="exact").limit(1000).execute()
                if not r.data or len(r.data) == 0:
                    print(f"  {table}: ya vacía")
                    break
                ids = [row["id"] for row in r.data]
                sb.table(table).delete().in_("id", ids).execute()
                print(f"  {table}: borradas {len(ids)} filas...")
        except Exception as e:
            print(f"  {table}: {e}")
            print("  Si no tienes política DELETE, ejecuta en SQL Editor: src/db/truncate_all.sql")
    print("Listo. Ejecuta run_etl_to_supabase.py para cargar desde cero.")


if __name__ == "__main__":
    main()
