"""
Serie histórica 2014-2024 en USD para el dashboard.
- Primas: tasa BCV promedio (oficial).
- Siniestros: tasa mercado sugerida (siniestralidad real).
- USD equivalente 2024: normaliza a unidad 2024 (÷10^11 o ÷10^6) y convierte con tasa 2024 (evita saltos por reconversión).
- Fuentes: matriz_base_madre_2014_2024.csv (ventana 10y) y anuario_metricas.csv (complemento).
- Verifica consistencia: alerta si hay saltos bruscos año a año.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.anuarios_paths import SEGURO_EN_CIFRAS_INDICE, SEGURO_EN_CIFRAS_VACIADO
from config.anuarios_paths import ensure_anuarios_dirs
from src.etl.tasas_cambio import (
    convertir_con_valor_original,
    convert_miles_to_usd_equivalente_2024,
    get_tasa_cierre,
)

ANUARIO_METRICAS_CSV = SEGURO_EN_CIFRAS_VACIADO / "anuario_metricas.csv"
MATRIZ_CSV = SEGURO_EN_CIFRAS_VACIADO / "matriz_base_madre_2014_2024.csv"
SERIE_10Y_CSV = SEGURO_EN_CIFRAS_INDICE / "serie_historica_10y_usd.csv"
ANALISIS_SERIE_TXT = SEGURO_EN_CIFRAS_INDICE / "analisis_consistencia_serie_10y.txt"

ANOS_VENTANA = list(range(2014, 2025))  # 2014-2024
MAX_SALTO = 5.0


def _cargar_totales_por_anio() -> pd.DataFrame:
    """Carga totales primas/siniestros por año desde matriz (2014-2024) y anuario_metricas (todos)."""
    # Desde matriz: columnas primas_netas_cobradas, siniestros_pagados por (entity, anio)
    rows = []
    if MATRIZ_CSV.exists():
        mat = pd.read_csv(MATRIZ_CSV)
        mat["anio"] = pd.to_numeric(mat["anio"], errors="coerce")
        mat["primas_netas_cobradas"] = pd.to_numeric(mat["primas_netas_cobradas"], errors="coerce")
        mat["siniestros_pagados"] = pd.to_numeric(mat["siniestros_pagados"], errors="coerce")
        for anio in ANOS_VENTANA:
            sub = mat[mat["anio"] == anio]
            p = sub["primas_netas_cobradas"].sum()
            s = sub["siniestros_pagados"].sum()
            np_ = (sub["primas_netas_cobradas"].notna() & (sub["primas_netas_cobradas"] > 0)).sum()
            ns_ = (sub["siniestros_pagados"].notna() & (sub["siniestros_pagados"] > 0)).sum()
            rows.append({"anio": anio, "primas_miles": p, "siniestros_miles": s, "n_primas": np_, "n_siniestros": ns_, "fuente": "matriz"})
    # Desde anuario_metricas: para años en ventana, sumar si no tenemos datos en matriz (o siempre como respaldo)
    if ANUARIO_METRICAS_CSV.exists():
        df = pd.read_csv(ANUARIO_METRICAS_CSV)
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df[df["value"].notna() & (df["value"] >= 0)]
        for anio in ANOS_VENTANA:
            primas = df[(df["anio"] == anio) & (df["metric_name"] == "primas_netas_cobradas")]
            siniestros = df[(df["anio"] == anio) & (df["metric_name"] == "siniestros_pagados")]
            sp = primas["value"].sum()
            ss = siniestros["value"].sum()
            np_ = primas["entity_name"].nunique() if not primas.empty else 0
            ns_ = siniestros["entity_name"].nunique() if not siniestros.empty else 0
            # Si ya tenemos fila de matriz y tiene datos, no sobrescribir. Si matriz tiene 0, usar anuario.
            existente = next((r for r in rows if r["anio"] == anio), None)
            if existente and (existente["primas_miles"] > 0 or existente["siniestros_miles"] > 0):
                continue
            if existente:
                existente["primas_miles"] = sp
                existente["siniestros_miles"] = ss
                existente["n_primas"] = int(np_)
                existente["n_siniestros"] = int(ns_)
                existente["fuente"] = "anuario" if (sp > 0 or ss > 0) else "matriz"
            else:
                rows.append({"anio": anio, "primas_miles": sp, "siniestros_miles": ss, "n_primas": int(np_), "n_siniestros": int(ns_), "fuente": "anuario"})
    out = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["anio", "primas_miles", "siniestros_miles", "n_primas", "n_siniestros", "fuente"])
    # Asegurar una fila por cada año de la ventana
    for anio in ANOS_VENTANA:
        if out.empty or anio not in out["anio"].values:
            out = pd.concat([out, pd.DataFrame([{"anio": anio, "primas_miles": 0, "siniestros_miles": 0, "n_primas": 0, "n_siniestros": 0, "fuente": ""}])], ignore_index=True)
    out = out.sort_values("anio").reset_index(drop=True)
    return out


def run_serie_10y() -> dict:
    """Construye serie 2014-2024 en USD y USD equiv. 2024; verifica consistencia."""
    ensure_anuarios_dirs()
    SEGURO_EN_CIFRAS_INDICE.mkdir(parents=True, exist_ok=True)

    resultado = {"errores": [], "alertas_salto": [], "filas": []}

    totals = _cargar_totales_por_anio()
    if totals.empty:
        resultado["errores"].append("No se pudo cargar matriz ni anuario_metricas.")
        _escribir_analisis(resultado, [])
        return resultado

    tasa_2024 = get_tasa_cierre(2024)
    filas = []
    for _, row in totals.iterrows():
        anio = int(row["anio"])
        sum_primas = row["primas_miles"]
        sum_siniestros = row["siniestros_miles"]
        n_ent_primas = int(row.get("n_primas", 0))
        n_ent_siniestros = int(row.get("n_siniestros", 0))

        res_p = convertir_con_valor_original(float(sum_primas), anio, "primas_netas_cobradas") if sum_primas else None
        res_s = convertir_con_valor_original(float(sum_siniestros), anio, "siniestros_pagados") if sum_siniestros else None

        primas_usd = res_p.valor_usd if res_p else None
        siniestros_usd = res_s.valor_usd if res_s else None
        primas_usd_2024 = convert_miles_to_usd_equivalente_2024(sum_primas, anio, tasa_2024) if sum_primas else None
        siniestros_usd_2024 = convert_miles_to_usd_equivalente_2024(sum_siniestros, anio, tasa_2024) if sum_siniestros else None

        loss_ratio = (siniestros_usd / primas_usd * 100) if (primas_usd and siniestros_usd and primas_usd > 0) else None

        filas.append({
            "anio": anio,
            "primas_miles": round(float(sum_primas), 4),
            "siniestros_miles": round(float(sum_siniestros), 4),
            "primas_usd": round(primas_usd, 4) if primas_usd is not None else None,
            "siniestros_usd": round(siniestros_usd, 4) if siniestros_usd is not None else None,
            "primas_usd_equiv_2024": round(primas_usd_2024, 4) if primas_usd_2024 is not None else None,
            "siniestros_usd_equiv_2024": round(siniestros_usd_2024, 4) if siniestros_usd_2024 is not None else None,
            "n_entidades_primas": int(n_ent_primas),
            "n_entidades_siniestros": int(n_ent_siniestros),
            "loss_ratio_pct": round(loss_ratio, 2) if loss_ratio is not None else None,
        })
    resultado["filas"] = filas

    out = pd.DataFrame(filas)
    out.to_csv(SERIE_10Y_CSV, index=False, encoding="utf-8")

    # Verificación de saltos en USD equivalente 2024 (serie homogénea)
    col_p = "primas_usd_equiv_2024"
    col_s = "siniestros_usd_equiv_2024"
    for i in range(1, len(filas)):
        prev = filas[i - 1]
        curr = filas[i]
        anio_prev = prev["anio"]
        anio_curr = curr["anio"]
        for col, nombre in ((col_p, "Primas"), (col_s, "Siniestros")):
            v_prev = prev.get(col)
            v_curr = curr.get(col)
            if v_prev is None or v_curr is None or v_prev <= 0:
                continue
            ratio = v_curr / v_prev
            if ratio > MAX_SALTO:
                resultado["alertas_salto"].append(
                    f"{nombre} USD equiv.2024: salto {anio_prev}→{anio_curr} ratio={ratio:.2f} (>{MAX_SALTO})"
                )
            elif ratio < 1 / MAX_SALTO:
                resultado["alertas_salto"].append(
                    f"{nombre} USD equiv.2024: caída fuerte {anio_prev}→{anio_curr} ratio={ratio:.2f} (<{1/MAX_SALTO:.2f})"
                )

    _escribir_analisis(resultado, filas)
    return resultado


def _escribir_analisis(resultado: dict, filas: list[dict]) -> None:
    lineas = [
        "=== Análisis de consistencia - Serie histórica 10 años (2014-2024) en USD ===",
        "",
        "Metodología: Primas con tasa BCV (promedio). Siniestros con tasa mercado sugerida (siniestralidad real).",
        "USD equiv. 2024: valor normalizado a unidad 2024 (÷10^11 o ÷10^6) y convertido con tasa cierre 2024.",
        "",
    ]
    if resultado.get("errores"):
        lineas.append("Errores:")
        for e in resultado["errores"]:
            lineas.append(f"  - {e}")
        lineas.append("")
    if resultado.get("alertas_salto"):
        lineas.append("--- Alertas de saltos (revisar cobertura o datos) ---")
        for a in resultado["alertas_salto"]:
            lineas.append(f"  {a}")
        lineas.append("")
    lineas.append("--- Serie USD equivalente 2024 (evita saltos por reconversión) ---")
    for f in filas:
        p = f.get("primas_usd_equiv_2024")
        s = f.get("siniestros_usd_equiv_2024")
        n = f.get("n_entidades_primas", 0)
        lineas.append(f"  {f['anio']}: primas_equiv_2024={p}, siniestros_equiv_2024={s}, n_ent_primas={n}")
    lineas.append("")
    anios_con_datos = [f["anio"] for f in filas if (f.get("primas_usd") or f.get("siniestros_usd"))]
    lineas.append("--- Años con datos (primas o siniestros en USD) ---")
    lineas.append(f"  {anios_con_datos}. Sin datos: no vaciados aún en matriz/anuario para ese año.")
    lineas.append("")
    lineas.append("--- Conclusión ---")
    if not resultado.get("alertas_salto") and not resultado.get("errores"):
        if len(anios_con_datos) >= 2:
            lineas.append("  Serie consistente para uso en dashboard (sin saltos bruscos detectados).")
        else:
            lineas.append("  Metodología lista; faltan años con datos en la ventana 2014-2024 para serie completa.")
    else:
        lineas.append("  Revisar alertas antes de dar por válida la serie para el dashboard.")
    lineas.append("")
    ANALISIS_SERIE_TXT.write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    res = run_serie_10y()
    print("Serie 10y USD generada:", SERIE_10Y_CSV)
    print("Análisis:", ANALISIS_SERIE_TXT)
    if res.get("alertas_salto"):
        print("Alertas:", res["alertas_salto"])
    if res.get("errores"):
        print("Errores:", res["errores"])
