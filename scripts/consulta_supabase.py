# scripts/consulta_supabase.py
"""Consulta Supabase y muestra conteos + muestra de datos para verificar la carga."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import get_supabase_client


def get_count(sb, table: str) -> int | str:
    """Obtiene el total de filas de una tabla. Devuelve int o mensaje de error."""
    try:
        r = sb.table(table).select("id", count="exact").limit(1).execute()
        count = getattr(r, "count", None)
        if count is not None:
            return count
        r = sb.table(table).select("id").limit(10000).execute()
        return len(r.data or [])
    except Exception as e:
        return f"Error: {e}"


def main():
    sb = get_supabase_client()
    if not sb:
        print("ERROR: No se pudo conectar a Supabase. Revisa .env (SUPABASE_URL, SUPABASE_KEY).")
        return
    print("=== VERIFICACIÓN DE CARGA EN SUPABASE ===\n")

    tables = [
        "entities",
        "primas_mensuales",
        "exchange_rates",
        "margen_solvencia",
        "series_historicas",
    ]
    counts = {}
    for table in tables:
        n = get_count(sb, table)
        counts[table] = n
        if isinstance(n, int):
            print(f"  {table:22} {n:>10} registros")
        else:
            print(f"  {table:22} {n}")

    n_primas = counts.get("primas_mensuales")
    if isinstance(n_primas, int) and n_primas > 0:
        print("\n--- Muestra primas_mensuales (5 primeras por periodo) ---")
        r = sb.table("primas_mensuales").select("periodo, primas_netas_ves, entity_id").order("periodo").limit(5).execute()
        for row in r.data or []:
            eid = str(row.get("entity_id") or "")[:8]
            print(f"  {row.get('periodo')} | primas_ves: {row.get('primas_netas_ves')} | entity_id: {eid}...")
        r2 = sb.table("primas_mensuales").select("periodo").order("periodo", desc=True).limit(1).execute()
        if r2.data:
            print(f"  Último periodo en BD: {r2.data[0].get('periodo')}")

    n_entities = counts.get("entities")
    if isinstance(n_entities, int) and n_entities > 0:
        print("\n--- Muestra entities (hasta 5 nombres) ---")
        r = sb.table("entities").select("canonical_name, normalized_name").limit(10).execute()
        for row in (r.data or [])[:5]:
            name = row.get("canonical_name") or row.get("normalized_name")
            if name:
                print(f"  {name}")

    print("\n--- Cómo revisar en la consola ---")
    print("  1. Entra a tu proyecto en https://supabase.com/dashboard")
    print("  2. Table Editor -> primas_mensuales / entities / exchange_rates / etc.")
    print("  3. Comprueba que la URL del proyecto coincida con SUPABASE_URL en .env")


if __name__ == "__main__":
    main()
