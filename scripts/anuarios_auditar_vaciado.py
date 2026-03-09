"""
Audita el vaciado de anuarios: verifica que todos los campos definidos
tengan informacion y genera un reporte de cobertura por campo y por archivo.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.anuarios_paths import (
    ensure_anuarios_dirs,
    VACIADO_ENTIDADES_CSV,
    METRICAS_CSV,
    SEGURO_EN_CIFRAS_INDICE,
    SEGURO_EN_CIFRAS_VARIABLES,
)


# Campos requeridos por tabla (no deben estar vacios)
CAMPOS_ENTIDADES = ["anio", "source_file", "entity_name", "entity_normalized_name"]
CAMPOS_METRICAS = ["anio", "source_file", "cuadro_or_seccion", "entity_name", "metric_name", "value", "unit", "ramo_opcional"]


def _pct(n: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{100 * n / total:.1f}%"


def auditar_entidades(df: pd.DataFrame) -> list[dict]:
    """Audita anuario_entidades: cobertura por campo."""
    report = []
    total = len(df)
    for col in CAMPOS_ENTIDADES:
        if col not in df.columns:
            report.append({"tabla": "anuario_entidades", "campo": col, "total": total, "no_nulo": 0, "nulo": total, "pct_lleno": "0%", "ok": False})
            continue
        no_nulo = df[col].notna().sum()
        # Considerar vacio: NaN o string vacio
        no_nulo = (df[col].notna() & (df[col].astype(str).str.strip() != "")).sum()
        nulo = total - no_nulo
        pct = _pct(no_nulo, total)
        report.append({
            "tabla": "anuario_entidades",
            "campo": col,
            "total": total,
            "no_nulo": int(no_nulo),
            "nulo": int(nulo),
            "pct_lleno": pct,
            "ok": nulo == 0,
        })
    return report


def auditar_metricas(df: pd.DataFrame, canonico: set[str]) -> list[dict]:
    """Audita anuario_metricas: cobertura por campo y metric_name vs canonico."""
    report = []
    total = len(df)

    for col in CAMPOS_METRICAS:
        if col not in df.columns:
            report.append({"tabla": "anuario_metricas", "campo": col, "total": total, "no_nulo": 0, "nulo": total, "pct_lleno": "0%", "ok": False})
            continue
        if col == "value":
            # value debe ser numerico (no vacio para filas de dato)
            no_nulo = pd.to_numeric(df[col], errors="coerce").notna().sum()
        elif col == "ramo_opcional":
            # ramo es opcional
            no_nulo = df[col].notna().sum()
            no_nulo = (df[col].notna() & (df[col].astype(str).str.strip() != "")).sum()
        else:
            no_nulo = (df[col].notna() & (df[col].astype(str).str.strip() != "")).sum()
        nulo = total - no_nulo
        pct = _pct(no_nulo, total)
        # value: aceptar >= 99% como OK (pueden quedar celdas vacias en origen)
        ok = (nulo == 0) if col != "ramo_opcional" else True
        if col == "value" and no_nulo > 0 and total > 0:
            ok = (100 * no_nulo / total) >= 99.0
        report.append({
            "tabla": "anuario_metricas",
            "campo": col,
            "total": total,
            "no_nulo": int(no_nulo),
            "nulo": int(nulo),
            "pct_lleno": pct,
            "ok": ok,
        })

    # Resumen metric_name: cobertura vs canonico
    if "metric_name" in df.columns:
        presentes = set(df["metric_name"].dropna().unique())
        no_canonico = presentes - canonico
        # metric_name_en_canonico: solo informativo; no fallar si hay metricas validas no listadas en canonico
        aceptados_extras = {"otro", "porcentaje", "porcentaje_ramo", "total", "valor_numerico", "capital_pagado", "garantia_deposito"}
        extras = no_canonico - aceptados_extras - canonico
        report.append({
            "tabla": "anuario_metricas",
            "campo": "metric_name_en_canonico",
            "total": total,
            "no_nulo": len(presentes),
            "nulo": len(no_canonico),
            "pct_lleno": _pct(len(presentes), len(canonico)) if canonico else "N/A",
            "ok": len(extras) == 0,
        })
    return report


def main():
    ensure_anuarios_dirs()
    reportes = []

    # Variables canonicas
    canonico_path = SEGURO_EN_CIFRAS_VARIABLES / "canonico.csv"
    canonico = set()
    if canonico_path.exists():
        try:
            cv = pd.read_csv(canonico_path)
            if "metric_name" in cv.columns:
                canonico = set(cv["metric_name"].dropna().astype(str).str.strip())
        except Exception:
            pass

    # --- Entidades ---
    if not VACIADO_ENTIDADES_CSV.exists():
        print("AVISO: No existe", VACIADO_ENTIDADES_CSV)
        reportes.append({"tabla": "anuario_entidades", "campo": "_archivo", "total": 0, "no_nulo": 0, "nulo": 0, "pct_lleno": "0%", "ok": False})
    else:
        df_ent = pd.read_csv(VACIADO_ENTIDADES_CSV)
        reportes.extend(auditar_entidades(df_ent))

    # --- Metricas ---
    if not METRICAS_CSV.exists():
        print("AVISO: No existe", METRICAS_CSV)
        reportes.append({"tabla": "anuario_metricas", "campo": "_archivo", "total": 0, "no_nulo": 0, "nulo": 0, "pct_lleno": "0%", "ok": False})
    else:
        df_met = pd.read_csv(METRICAS_CSV)
        reportes.extend(auditar_metricas(df_met, canonico))

    # Resumen por anio (entidades y metricas)
    resumen_anio = []
    if VACIADO_ENTIDADES_CSV.exists():
        df_ent = pd.read_csv(VACIADO_ENTIDADES_CSV)
        for anio, g in df_ent.groupby("anio"):
            resumen_anio.append({"anio": anio, "tipo": "entidades", "registros": len(g), "entidades_unicas": g["entity_normalized_name"].nunique()})
    if METRICAS_CSV.exists():
        df_met = pd.read_csv(METRICAS_CSV)
        for anio, g in df_met.groupby("anio"):
            resumen_anio.append({"anio": anio, "tipo": "metricas", "registros": len(g), "cuadros": g["cuadro_or_seccion"].nunique() if "cuadro_or_seccion" in g.columns else 0})

    # Escribir reporte CSV
    out_csv = SEGURO_EN_CIFRAS_INDICE / "auditoria_vaciado.csv"
    pd.DataFrame(reportes).to_csv(out_csv, index=False, encoding="utf-8-sig")

    resumen_csv = SEGURO_EN_CIFRAS_INDICE / "auditoria_vaciado_resumen_anio.csv"
    if resumen_anio:
        pd.DataFrame(resumen_anio).to_csv(resumen_csv, index=False, encoding="utf-8-sig")

    # Consola
    print("Auditoria del vaciado - Seguro en Cifras")
    print("=" * 55)
    for r in reportes:
        ok_str = "OK" if r.get("ok", True) else "FALTA"
        print(f"  {r['tabla']}.{r['campo']}: {r['no_nulo']}/{r['total']} ({r['pct_lleno']}) {ok_str}")
    print()
    if resumen_anio:
        print("Resumen por anio:")
        for r in resumen_anio:
            print(f"  {r['anio']} {r['tipo']}: {r['registros']} registros" + (f", {r.get('entidades_unicas', r.get('cuadros', ''))} ent/cuadros" if r.get("entidades_unicas") or r.get("cuadros") else ""))
    print()
    print("Reporte guardado:", out_csv)
    if resumen_anio:
        print("Resumen por anio:", resumen_csv)

    # Exit con error si algun campo critico falla
    fallos = [r for r in reportes if r.get("ok") is False]
    if fallos:
        print("\nCampos con datos faltantes:", [f"{r['tabla']}.{r['campo']}" for r in fallos])
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
