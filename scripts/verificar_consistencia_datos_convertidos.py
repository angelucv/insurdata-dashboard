# scripts/verificar_consistencia_datos_convertidos.py
"""
Verificación de consistencia de los datos convertidos (CSV en by_source y espejo).
Comprueba: existencia de archivos, cobertura de campos, tipos numéricos y resumen por fuente.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_AUDIT
from config.audit_paths import (
    DATA_AUDIT_BY_SOURCE,
    MIRROR_PRIMAS_CSV,
    MIRROR_ENTITIES_CSV,
    MANIFEST_INDEX_JSON,
)


def _safe_numeric_series(s: pd.Series) -> tuple[int, float | None]:
    """Cuenta celdas que se pueden interpretar como número (incl. formato 1.234,56)."""
    if s.empty:
        return 0, None
    n_ok = 0
    vals = []
    for v in s.dropna():
        if pd.isna(v):
            continue
        vs = str(v).strip()
        if not vs:
            continue
        # Formato europeo: 1.868.606,33
        vs = vs.replace(".", "").replace(",", ".")
        try:
            vals.append(float(vs))
            n_ok += 1
        except ValueError:
            pass
    total = len(s)
    suma = sum(vals) if vals else None
    return n_ok, suma


def verificar_by_source() -> list[dict]:
    """Revisa todos los CSV en by_source: filas, columnas, celdas numéricas."""
    if not DATA_AUDIT_BY_SOURCE.exists():
        return [{"error": f"No existe directorio by_source: {DATA_AUDIT_BY_SOURCE}"}]
    csv_files = list(DATA_AUDIT_BY_SOURCE.glob("*.csv"))
    if not csv_files:
        return [{"info": "No hay archivos CSV en by_source."}]
    resultados = []
    for path in sorted(csv_files):
        try:
            df = pd.read_csv(path, encoding="utf-8-sig", on_bad_lines="warn", low_memory=False)
        except Exception as e:
            resultados.append({"archivo": path.name, "error_lectura": str(e)})
            continue
        n_rows, n_cols = len(df), len(df.columns)
        # Detectar columnas que parecen numéricas (por nombre o por contenido)
        numeric_count = 0
        sample_suma = None
        for c in df.columns:
            n_ok, suma = _safe_numeric_series(df[c])
            if n_ok > 0:
                numeric_count += n_ok
                if sample_suma is None and suma is not None:
                    sample_suma = suma
        resultados.append({
            "archivo": path.name,
            "filas": n_rows,
            "columnas": n_cols,
            "celdas_numericas": numeric_count,
            "ok_lectura": True,
        })
    return resultados


def verificar_mirror() -> dict:
    """Verifica el espejo (mirror): primas_mensuales y entities."""
    out = {"primas": None, "entities": None, "errores": []}
    if not MIRROR_PRIMAS_CSV.exists():
        out["errores"].append("No existe mirror primas_mensuales. Ejecutar: python scripts/audit_local_pipeline.py")
        return out
    try:
        df = pd.read_csv(MIRROR_PRIMAS_CSV, encoding="utf-8-sig")
        total = len(df)
        numeric_cols = ["primas_netas_ves", "siniestros_pagados_ves", "gastos_operativos_ves"]
        cobertura = {}
        for col in numeric_cols:
            if col not in df.columns:
                cobertura[col] = {"non_null": 0, "pct": 0.0, "suma": None}
                continue
            non_null = int(df[col].notna().sum())
            s = pd.to_numeric(df[col], errors="coerce")
            valid = s.notna().sum()
            suma = float(s.sum()) if valid else None
            cobertura[col] = {
                "non_null": int(valid),
                "pct": round(100.0 * valid / total, 1) if total else 0,
                "suma": round(suma, 2) if suma is not None else None,
            }
        out["primas"] = {"filas": total, "cobertura": cobertura}
    except Exception as e:
        out["errores"].append(f"Error leyendo mirror primas: {e}")
    if MIRROR_ENTITIES_CSV.exists():
        try:
            ent = pd.read_csv(MIRROR_ENTITIES_CSV, encoding="utf-8-sig")
            out["entities"] = {"filas": len(ent), "columnas": list(ent.columns)}
        except Exception as e:
            out["errores"].append(f"Error leyendo mirror entities: {e}")
    return out


def verificar_manifest() -> dict | None:
    """Lee el manifest y devuelve resumen si existe."""
    if not MANIFEST_INDEX_JSON.exists():
        return None
    try:
        with open(MANIFEST_INDEX_JSON, encoding="utf-8") as f:
            m = json.load(f)
        return {
            "generated_at": m.get("generated_at"),
            "total_primas_rows": m.get("total_primas_rows", 0),
            "total_entities": m.get("total_entities", 0),
            "sources": len(m.get("sources", [])),
            "errores_en_fuentes": len([s for s in m.get("sources", []) if s.get("error")]),
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=" * 60)
    print("Verificación de consistencia — datos convertidos (SUDEASEG)")
    print("=" * 60)
    print(f"\nDirectorio auditoría: {DATA_AUDIT}\n")

    # 1) By-source
    print("--- 1) Archivos por fuente (data/audit/by_source) ---")
    by_src = verificar_by_source()
    if by_src and "error" in by_src[0]:
        print(by_src[0]["error"])
    elif by_src and "info" in by_src[0]:
        print(by_src[0]["info"])
    else:
        total_filas = 0
        for r in by_src:
            if r.get("error_lectura"):
                print(f"  [ERROR] {r['archivo']}: {r['error_lectura']}")
            else:
                total_filas += r.get("filas", 0)
                print(f"  {r['archivo']}: {r['filas']} filas, {r['columnas']} columnas, ~{r.get('celdas_numericas', 0)} celdas numéricas")
        print(f"\n  Total archivos: {len(by_src)} | Total filas (suma): {total_filas}")

    # 2) Mirror
    print("\n--- 2) Estructura espejo (data/audit/mirror) ---")
    mirror = verificar_mirror()
    for e in mirror.get("errores", []):
        print(f"  {e}")
    if mirror.get("primas"):
        p = mirror["primas"]
        print(f"  primas_mensuales: {p['filas']} filas")
        for col, v in p.get("cobertura", {}).items():
            print(f"    {col}: {v['non_null']} no nulos ({v['pct']}%)" + (f" | suma={v['suma']}" if v.get("suma") is not None else ""))
    if mirror.get("entities"):
        e = mirror["entities"]
        print(f"  entities: {e['filas']} filas, columnas: {e['columnas']}")

    # 3) Manifest
    print("\n--- 3) Manifest (índice de extracción) ---")
    man = verificar_manifest()
    if man is None:
        print("  No existe manifest. Ejecutar: python scripts/audit_local_pipeline.py")
    elif man.get("error"):
        print(f"  Error: {man['error']}")
    else:
        print(f"  Generado: {man.get('generated_at', 'N/A')}")
        print(f"  Total filas primas: {man.get('total_primas_rows', 0)}")
        print(f"  Total entidades: {man.get('total_entities', 0)}")
        print(f"  Fuentes procesadas: {man.get('sources', 0)}")
        if man.get("errores_en_fuentes", 0) > 0:
            print(f"  [ALERTA] Fuentes con error: {man['errores_en_fuentes']}")

    # Conclusión
    print("\n--- Conclusión ---")
    if by_src and not any(r.get("error_lectura") for r in by_src if isinstance(r, dict)):
        if mirror.get("primas") and mirror["primas"]["filas"] > 0:
            print("  Los datos convertidos (by_source y espejo) están presentes y legibles.")
            print("  Revisa cobertura de columnas numéricas arriba para validar contenido.")
        elif by_src and len([r for r in by_src if isinstance(r, dict) and r.get("filas", 0) > 0]) > 0:
            print("  Hay CSV en by_source legibles. El espejo (mirror) puede estar vacío o no generado.")
            print("  Para compilar espejo desde data/raw: python scripts/audit_local_pipeline.py")
        else:
            print("  by_source tiene archivos pero sin filas o solo metadata. Revisar extracción.")
    else:
        print("  Hay errores de lectura en by_source o no hay datos. Revisar rutas y encoding.")
    print()


if __name__ == "__main__":
    main()
