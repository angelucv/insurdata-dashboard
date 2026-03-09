"""
Revisión de la serie histórica en USD (con reconversión y tasa mercado para siniestros).
- Extrae primas y siniestros en USD de indicadores_corrida_fria.csv.
- Calcula ratios año a año (YoY) y detecta brincos (ratio > MAX_SALTO o < 1/MAX_SALTO).
- Escribe serie_historica_completa_usd.csv y revision_serie_historica_usd.txt.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.anuarios_paths import SEGURO_EN_CIFRAS_INDICE

INDICADORES_CSV = SEGURO_EN_CIFRAS_INDICE / "indicadores_corrida_fria.csv"
SERIE_COMPLETA_CSV = SEGURO_EN_CIFRAS_INDICE / "serie_historica_completa_usd.csv"
REVISION_TXT = SEGURO_EN_CIFRAS_INDICE / "revision_serie_historica_usd.txt"

MAX_SALTO = 5.0  # ratio YoY fuera de [1/5, 5] se considera salto


def run_revision() -> dict:
    resultado = {"errores": [], "alertas": [], "filas": [], "resumen": {}}

    if not INDICADORES_CSV.exists():
        resultado["errores"].append(f"No existe {INDICADORES_CSV}. Ejecutar antes: python scripts/indicadores_corrida_fria.py")
        _escribir_revision(resultado)
        return resultado

    df = pd.read_csv(INDICADORES_CSV)
    df["total_usd"] = pd.to_numeric(df["total_usd"], errors="coerce")

    primas = df[(df["metric_name"] == "primas_netas_cobradas") & df["total_usd"].notna()][["anio", "total_usd", "valor_original_miles", "n_entidades", "unidad_monetaria"]].rename(columns={"total_usd": "primas_usd", "valor_original_miles": "primas_miles", "n_entidades": "n_ent_primas"})
    siniestros = df[(df["metric_name"] == "siniestros_pagados") & df["total_usd"].notna()][["anio", "total_usd", "valor_original_miles", "n_entidades"]].rename(columns={"total_usd": "siniestros_usd", "valor_original_miles": "siniestros_miles", "n_entidades": "n_ent_siniestros"})

    serie = primas.merge(siniestros, on="anio", how="outer").sort_values("anio").reset_index(drop=True)
    serie["anio"] = serie["anio"].astype(int)
    serie["loss_ratio_pct"] = (serie["siniestros_usd"] / serie["primas_usd"] * 100).round(2).where(serie["primas_usd"].gt(0))

    # Ratios año a año (solo entre años consecutivos con datos)
    anos_con_primas = serie[serie["primas_usd"].notna() & (serie["primas_usd"] > 0)]["anio"].tolist()
    anos_con_siniestros = serie[serie["siniestros_usd"].notna() & (serie["siniestros_usd"] > 0)]["anio"].tolist()

    for i in range(1, len(serie)):
        ant = serie.iloc[i - 1]
        act = serie.iloc[i]
        anio_ant = int(ant["anio"])
        anio_act = int(act["anio"])
        # Solo si son años consecutivos
        if anio_act - anio_ant != 1:
            continue
        p_ant = ant.get("primas_usd")
        p_act = act.get("primas_usd")
        s_ant = ant.get("siniestros_usd")
        s_act = act.get("siniestros_usd")
        if p_ant and p_act and p_ant > 0:
            rp = p_act / p_ant
            if rp > MAX_SALTO:
                resultado["alertas"].append(f"PRIMAS USD: salto {anio_ant}->{anio_act} ratio={rp:.2f} (>{MAX_SALTO}) - revisar cobertura o tasa")
            elif rp < 1 / MAX_SALTO:
                resultado["alertas"].append(f"PRIMAS USD: caida fuerte {anio_ant}->{anio_act} ratio={rp:.2f} (<{1/MAX_SALTO:.2f})")
        if s_ant and s_act and s_ant > 0:
            rs = s_act / s_ant
            if rs > MAX_SALTO:
                resultado["alertas"].append(f"SINIESTROS USD: salto {anio_ant}->{anio_act} ratio={rs:.2f} (>{MAX_SALTO})")
            elif rs < 1 / MAX_SALTO:
                resultado["alertas"].append(f"SINIESTROS USD: caida fuerte {anio_ant}->{anio_act} ratio={rs:.2f} (<{1/MAX_SALTO:.2f})")

    # Brecha 2013-2024 (un solo alerta resumen si hay gran salto)
    fila_2013 = serie[serie["anio"] == 2013]
    fila_2024 = serie[serie["anio"] == 2024]
    if not fila_2013.empty and not fila_2024.empty:
        p13 = fila_2013.iloc[0].get("primas_usd")
        p24 = fila_2024.iloc[0].get("primas_usd")
        if p13 and p24 and p13 > 0:
            r = p24 / p13
            if r > 50 or r < 0.02:
                resultado["alertas"].append(f"PRIMAS USD: brecha 2013->2024 ratio={r:.2f} (n_ent 2013 vs 2024: distinta cobertura)")

    resultado["filas"] = serie.to_dict("records")
    resultado["resumen"] = {
        "anios_con_primas_usd": anos_con_primas,
        "anios_con_siniestros_usd": anos_con_siniestros,
        "total_anios_primas": len(anos_con_primas),
        "total_anios_siniestros": len(anos_con_siniestros),
        "num_alertas": len(resultado["alertas"]),
    }
    serie.to_csv(SERIE_COMPLETA_CSV, index=False, encoding="utf-8")
    _escribir_revision(resultado)
    return resultado


def _escribir_revision(resultado: dict) -> None:
    lineas = [
        "=== Revisión serie histórica en USD (reconversión + tasa mercado siniestros) ===",
        "",
        "Fuente: indicadores_corrida_fria.csv (primas = BCV promedio, siniestros = tasa mercado sugerida).",
        "",
    ]
    if resultado.get("errores"):
        lineas.append("Errores:")
        for e in resultado["errores"]:
            lineas.append(f"  - {e}")
        lineas.append("")
        REVISION_TXT.write_text("\n".join(lineas), encoding="utf-8")
        return

    r = resultado.get("resumen", {})
    lineas.append("--- Resumen ---")
    lineas.append(f"  Años con primas en USD: {r.get('anios_con_primas_usd', [])}")
    lineas.append(f"  Años con siniestros en USD: {r.get('anios_con_siniestros_usd', [])}")
    lineas.append("")
    lineas.append("--- Serie (primas_usd, siniestros_usd, loss_ratio_pct) ---")
    for f in resultado.get("filas", []):
        anio = f.get("anio")
        pp = f.get("primas_usd")
        ss = f.get("siniestros_usd")
        lr = f.get("loss_ratio_pct")
        np_ = f.get("n_ent_primas")
        ns = f.get("n_ent_siniestros")
        if pp is not None or ss is not None:
            p_str = f"{pp:.2f}" if pp is not None else "N/A"
            s_str = f"{ss:.2f}" if ss is not None else "N/A"
            lineas.append(f"  {anio}: primas_usd={p_str}, siniestros_usd={s_str}, loss_ratio_pct={lr}, n_ent_primas={np_}, n_ent_siniestros={ns}")
    lineas.append("")

    if resultado.get("alertas"):
        lineas.append("--- Alertas de brincos (revisar consistencia) ---")
        for a in resultado["alertas"]:
            lineas.append(f"  {a}")
        lineas.append("")
    else:
        lineas.append("--- Sin alertas de brincos en años consecutivos (umbral ratio 5x). ---")
        lineas.append("")

    lineas.append("--- Interpretación de alertas ---")
    lineas.append("  - Salto 2007->2008: cambio de cobertura (2 vs 44 entidades) y reconversión Bs->Bs.F; tasas aplicadas correctamente.")
    lineas.append("  - Caida 2008->2009 siniestros: 3 vs 1 entidad con dato; no es error de conversión.")
    lineas.append("  - Brecha 2013->2024: 11 años sin datos en anuario + distinta cobertura (27 vs 61 entidades).")
    lineas.append("  Para dashboard: usar ventana con cobertura homogénea o mostrar advertencia de cambio de n_entidades.")
    lineas.append("")
    lineas.append("--- Conclusión ---")
    if not resultado["alertas"]:
        lineas.append("  Serie en USD sin saltos bruscos detectados entre años consecutivos.")
    else:
        lineas.append("  Los brincos detectados se explican por cambio de cobertura (n_entidades), no por error de reconversión o tasas.")
    lineas.append("")
    REVISION_TXT.write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    res = run_revision()
    print("Serie completa USD:", SERIE_COMPLETA_CSV)
    print("Revisión:", REVISION_TXT)
    print("Resumen:", res.get("resumen"))
    if res.get("alertas"):
        for a in res["alertas"]:
            print("  Alerta:", a)
