"""
Lee indicadores_corrida_fria.csv y genera un informe de verificación de consistencia:
- Ratio siniestros/primas (loss ratio) por año cuando existen ambos.
- Cobertura por año (entidades); alertas por cobertura baja.
- Anomalías: años sin tasa, totales USD fuera de rango, suma de porcentajes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.anuarios_paths import SEGURO_EN_CIFRAS_INDICE

INDICADORES_CSV = SEGURO_EN_CIFRAS_INDICE / "indicadores_corrida_fria.csv"
VERIFICACION_TXT = SEGURO_EN_CIFRAS_INDICE / "verificacion_consistencia_corrida_fria.txt"

UMBRAL_COBERTURA_BAJA = 20  # menos de N entidades = cobertura dudosa para totales


def run_verificacion() -> list[str]:
    """Genera líneas del informe de verificación."""
    lineas = [
        "=== Verificación de consistencia - Corrida en frío ===",
        "",
    ]
    if not INDICADORES_CSV.exists():
        lineas.append("No existe indicadores_corrida_fria.csv. Ejecutar antes: python scripts/indicadores_corrida_fria.py")
        return lineas

    import pandas as pd
    df = pd.read_csv(INDICADORES_CSV)
    df["total_usd"] = pd.to_numeric(df["total_usd"], errors="coerce")
    df["valor_original_miles"] = pd.to_numeric(df.get("valor_original_miles", df.get("total_miles", pd.NA)), errors="coerce")

    # 1) Cobertura por año
    anios = df["anio"].dropna().unique()
    resumen_entidades = df.groupby("anio").agg(
        n_entidades_max=("n_entidades", "max"),
        n_metricas=("metric_name", "nunique"),
    ).reset_index()
    lineas.append("--- Cobertura (máx. entidades por año en cualquier métrica) ---")
    for _, r in resumen_entidades.iterrows():
        anio = int(r["anio"])
        n = int(r["n_entidades_max"])
        alerta = " [COBERTURA BAJA]" if n < UMBRAL_COBERTURA_BAJA else ""
        lineas.append(f"  {anio}: {n} entidades{alerta}")
    lineas.append("")

    # 2) Loss ratio (siniestros/primas) en USD cuando existan ambos
    primas = df[(df["metric_name"] == "primas_netas_cobradas") & df["total_usd"].notna()][["anio", "total_usd"]].rename(columns={"total_usd": "primas_usd"})
    siniestros = df[(df["metric_name"] == "siniestros_pagados") & df["total_usd"].notna()][["anio", "total_usd"]].rename(columns={"total_usd": "siniestros_usd"})
    merge = primas.merge(siniestros, on="anio", how="inner")
    merge["loss_ratio_pct"] = (merge["siniestros_usd"] / merge["primas_usd"] * 100).round(2)
    lineas.append("--- Ratio siniestros/primas (loss ratio) en USD ---")
    if merge.empty:
        lineas.append("  No hay años con primas y siniestros en USD.")
    else:
        for _, r in merge.iterrows():
            lineas.append(f"  {int(r['anio'])}: {r['loss_ratio_pct']}%  (primas={r['primas_usd']:.0f} USD, siniestros={r['siniestros_usd']:.0f} USD)")
    lineas.append("")

    # 3) Métricas en % que no deben interpretarse como totales
    pct = df[df["unit"].astype(str).str.contains("%", na=False)]
    if not pct.empty:
        lineas.append("--- Advertencia: métricas en % (la 'suma' no es un total válido) ---")
        for _, r in pct.iterrows():
            lineas.append(f"  {int(r['anio'])} {r['metric_name']}: valor_original_miles={r.get('valor_original_miles', r.get('total_miles', ''))} (no sumar entre entidades)")
        lineas.append("")

    # 4) Anomalías USD: comparar magnitud entre años
    primas_usd = df[(df["metric_name"] == "primas_netas_cobradas") & df["total_usd"].notna()].set_index("anio")["total_usd"]
    if len(primas_usd) >= 2:
        min_p, max_p = primas_usd.min(), primas_usd.max()
        anio_min, anio_max = primas_usd.idxmin(), primas_usd.idxmax()
        if max_p > 0 and min_p > 0 and (max_p / min_p) > 100:
            lineas.append("--- Anomalía: gran dispersión en total primas (USD) entre años ---")
            lineas.append(f"  Mín: {anio_min} = {min_p:.2f} USD; Máx: {anio_max} = {max_p:.2f} USD.")
            lineas.append("  Posibles causas: distinta cobertura de entidades, tasas de cambio de referencia, o unidad distinta por reconversión.")
        lineas.append("")

    lineas.append("--- Conclusión ---")
    lineas.append("  Revisar años con COBERTURA BAJA antes de comparar totales.")
    lineas.append("  Los totales en USD dependen de tasa_cambio_anual.csv; actualizar con BCV para mayor coherencia.")
    lineas.append("")
    return lineas


if __name__ == "__main__":
    lineas = run_verificacion()
    VERIFICACION_TXT.write_text("\n".join(lineas), encoding="utf-8")
    print(VERIFICACION_TXT)
    for L in lineas:
        print(L)
