# scripts/verificar_numericos.py
"""Verifica que los valores numéricos estén cargados correctamente en primas_mensuales."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import get_supabase_client

NUMERIC_COLS = [
    "primas_netas_ves",
    "primas_netas_usd",
    "siniestros_pagados_ves",
    "siniestros_pagados_usd",
    "gastos_operativos_ves",
    "gastos_operativos_usd",
]


def main():
    sb = get_supabase_client()
    if not sb:
        print("Supabase no configurado.")
        return
    print("=== Verificación de columnas numéricas en primas_mensuales ===\n")
    # Paginar para obtener todos los registros (Supabase limita a 1000 por request)
    all_rows = []
    offset = 0
    page_size = 1000
    while True:
        r = sb.table("primas_mensuales").select("id," + ",".join(NUMERIC_COLS)).range(offset, offset + page_size - 1).execute()
        chunk = r.data or []
        if not chunk:
            break
        all_rows.extend(chunk)
        if len(chunk) < page_size:
            break
        offset += page_size
    total = len(all_rows)
    print(f"Total registros analizados: {total}\n")
    print("Columnas numéricas - conteo de valores NO NULOS:")
    print("-" * 50)
    for col in NUMERIC_COLS:
        non_null = sum(1 for x in all_rows if x.get(col) is not None)
        pct = (100 * non_null / total) if total else 0
        status = "OK" if non_null > 0 else "VACÍO"
        print(f"  {col}: {non_null}/{total} ({pct:.1f}%) [{status}]")
        if non_null > 0:
            vals = [x[col] for x in all_rows if x.get(col) is not None]
            print(f"    -> Suma: {sum(vals):,.2f} | Min: {min(vals):,.2f} | Max: {max(vals):,.2f}")
    print("-" * 50)
    if total and all_rows[0].get("primas_netas_ves") is not None:
        print("\nConclusión: primas_netas_ves está cargado. USD/siniestros/gastos se llenan con Resumen por empresa o conversión BCV.")


if __name__ == "__main__":
    main()
