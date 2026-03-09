"""
Arqueo: verifica que los campos compilados en la estructura espejo tengan valores.
Lee data/audit/mirror/*.csv y data/audit/by_source, y reporta cobertura por campo.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.audit_paths import (
    MIRROR_PRIMAS_CSV,
    MIRROR_ENTITIES_CSV,
    MANIFEST_INDEX_JSON,
    DATA_AUDIT_BY_SOURCE,
    MIRROR_ENTITIES,
    MIRROR_PRIMAS,
)


def main():
    print("=== Arqueo: verificación de campos compilados (estructura espejo) ===\n")

    # Manifest
    if MANIFEST_INDEX_JSON.exists():
        import json
        with open(MANIFEST_INDEX_JSON, encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"Manifest: {manifest.get('generated_at', 'N/A')}")
        print(f"  Total filas primas: {manifest.get('total_primas_rows', 0)}")
        print(f"  Total entidades: {manifest.get('total_entities', 0)}")
        print(f"  Fuentes Excel: {len([s for s in manifest.get('sources', []) if s.get('type') == 'excel'])}")
        print(f"  Fuentes PDF: {len([s for s in manifest.get('sources', []) if s.get('type') == 'pdf'])}")
        errors = [s for s in manifest.get('sources', []) if s.get("error")]
        if errors:
            print(f"  Errores en fuentes: {len(errors)}")
            for e in errors[:5]:
                print(f"    - {e.get('file')}: {e.get('error')}")
    else:
        print("No se encontró manifest. Ejecuta primero: python scripts/audit_local_pipeline.py")

    # primas_mensuales (espejo)
    if not MIRROR_PRIMAS_CSV.exists():
        print("\nNo existe mirror primas_mensuales. Ejecuta audit_local_pipeline.py")
        return
    df = pd.read_csv(MIRROR_PRIMAS_CSV)
    total = len(df)
    print(f"\n--- Mirror primas_mensuales ({total} filas) ---")
    numeric_cols = ["primas_netas_ves", "siniestros_pagados_ves", "gastos_operativos_ves"]
    for col in numeric_cols:
        if col not in df.columns:
            print(f"  {col}: columna ausente")
            continue
        non_null = df[col].notna().sum()
        pct = 100.0 * non_null / total if total else 0
        status = "OK" if non_null > 0 else "VACÍO"
        print(f"  {col}: {non_null}/{total} ({pct:.1f}%) [{status}]")
        if non_null > 0:
            print(f"    -> Suma: {df[col].sum():,.2f} | Min: {df[col].min()} | Max: {df[col].max()}")

    # entity_normalized_name / periodo
    for col in ("entity_normalized_name", "periodo"):
        if col in df.columns:
            non_null = df[col].notna().sum()
            print(f"  {col}: {non_null}/{total} ({100.0 * non_null / total if total else 0:.1f}%)")

    # Entidades
    if MIRROR_ENTITIES_CSV.exists():
        ent = pd.read_csv(MIRROR_ENTITIES_CSV)
        print(f"\n--- Mirror entities ({len(ent)} filas) ---")
        print(f"  normalized_name: {ent['normalized_name'].notna().sum()}/{len(ent)}")
        print(f"  canonical_name: {ent['canonical_name'].notna().sum()}/{len(ent)}")

    # By-source: resumen de archivos generados
    if DATA_AUDIT_BY_SOURCE.exists():
        by_source = list(DATA_AUDIT_BY_SOURCE.glob("*.csv"))
        print(f"\n--- By-source: {len(by_source)} archivos extraídos ---")
        for p in sorted(by_source)[:15]:
            try:
                d = pd.read_csv(p, nrows=0)
                cols = list(d.columns)
            except Exception:
                cols = []
            print(f"  {p.name}: {len(cols)} columnas")
        if len(by_source) > 15:
            print(f"  ... y {len(by_source) - 15} más")

    print("\n--- Conclusión ---")
    if total > 0:
        filled = sum(1 for _, r in df.iterrows() if pd.notna(r.get("primas_netas_ves")))
        print(f"Filas con primas_netas_ves: {filled}/{total}. Revisa by_source y manifest para trazabilidad.")
    else:
        print("No hay filas en el espejo. Ejecuta audit_local_pipeline.py y/o descarga más datos (anuarios).")


if __name__ == "__main__":
    main()
