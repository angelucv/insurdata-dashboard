# scripts/seed_datos_prueba.py
"""Inserta datos de prueba en Supabase (entities + primas_mensuales) para ver el dashboard con datos.
   Nota: con la publishable key y RLS solo-lectura, los INSERT pueden fallar.
   En ese caso inserta los datos desde Supabase -> Table Editor, o añade políticas INSERT para anon."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import get_supabase_client


def main():
    sb = get_supabase_client()
    if not sb:
        print("Configura SUPABASE_URL y SUPABASE_KEY en .env")
        return

    # 1. Insertar una entidad de prueba
    entities = [
        {"normalized_name": "aseguradora_demo_a", "canonical_name": "Aseguradora Demo A"},
    ]
    print("Insertando entidades...")
    try:
        r = sb.table("entities").insert(entities).execute()
        data = r.data if hasattr(r, "data") else []
        entity_id = data[0]["id"] if data else None
    except Exception as e:
        print(f"  Error insertando entities (¿RLS?): {e}")
        print("  Inserta manualmente una fila en Table Editor -> entities y anota el id (UUID).")
        return
    if not entity_id:
        r = sb.table("entities").select("id").eq("normalized_name", "aseguradora_demo_a").execute()
        entity_id = (r.data or [{}])[0].get("id") if r.data else None
    if not entity_id:
        print("No se pudo obtener entity_id.")
        return

    # 2. Insertar primas mensuales de prueba
    primas = [
        {"entity_id": entity_id, "periodo": "2024-01-01", "primas_netas_usd": 150000.50, "siniestros_pagados_usd": 80000},
        {"entity_id": entity_id, "periodo": "2024-02-01", "primas_netas_usd": 162000.00, "siniestros_pagados_usd": 85000},
        {"entity_id": entity_id, "periodo": "2024-03-01", "primas_netas_usd": 158000.25, "siniestros_pagados_usd": 82000},
    ]
    print("Insertando primas_mensuales...")
    try:
        sb.table("primas_mensuales").insert(primas).execute()
        print("Datos de prueba insertados.")
    except Exception as e:
        print(f"  Error: {e}")
        print("  Puedes insertar filas manualmente en Table Editor -> primas_mensuales (entity_id = UUID de una entidad).")

    print("\nSiguiente paso: streamlit run app.py")


if __name__ == "__main__":
    main()
