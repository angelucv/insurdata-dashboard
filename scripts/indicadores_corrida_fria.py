"""
Corrida en frío de indicadores para verificar consistencia de datos (Seguro en Cifras).
- Usa anuario_metricas.csv y tasas de cambio anuales para convertir montos a USD.
- Genera indicadores por año y métrica (totales, promedios, cobertura) y un reporte.
- Datos Venezuela: reconversiones Bs -> BsF -> BsS -> VES; tasas en tasa_cambio_anual.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.anuarios_paths import (
    SEGURO_EN_CIFRAS_INDICE,
    SEGURO_EN_CIFRAS_VACIADO,
    SEGURO_EN_CIFRAS_VARIABLES,
)
from config.anuarios_paths import ensure_anuarios_dirs
from src.etl.tasas_cambio import (
    get_tasa_anio,
    convert_miles_local_to_usd,
    convertir_con_valor_original,
    load_tasas_anuales,
    load_tasas_bcv_cierre_promedio,
)

# Entradas
ANUARIO_METRICAS_CSV = SEGURO_EN_CIFRAS_VACIADO / "anuario_metricas.csv"
TASA_CAMBIO_CSV = SEGURO_EN_CIFRAS_VARIABLES / "tasa_cambio_anual.csv"

# Salidas
INDICADORES_CSV = SEGURO_EN_CIFRAS_INDICE / "indicadores_corrida_fria.csv"
REPORTE_TXT = SEGURO_EN_CIFRAS_INDICE / "reporte_corrida_fria.txt"

# Métricas en "miles de bolívares" que se convierten a USD
METRICAS_MONETARIAS = [
    "primas_netas_cobradas",
    "primas_netas_por_ramo",
    "siniestros_pagados",
    "reservas_tecnicas",
    "reservas_primas",
    "reservas_siniestros_pendientes",
    "gastos_administracion",
    "gastos_produccion",
    "capital_garantia",
    "capital_pagado",
    "garantia_deposito",
    "resultados_economicos",
    "inversiones_reservas",
    "comisiones_gastos_adquisicion",
    "ingresos_netos",
    "gastos_operativos",
    "balance_condensado",
    "activo_total",
    "pasivo_total",
]


def run_corrida_fria() -> dict:
    """Ejecuta la corrida en frío: indicadores por año/métrica y reporte de consistencia."""
    ensure_anuarios_dirs()
    SEGURO_EN_CIFRAS_INDICE.mkdir(parents=True, exist_ok=True)

    resultado = {
        "anios_con_datos": 0,
        "anios_sin_tasa": [],
        "metricas_procesadas": 0,
        "filas_indicadores": 0,
        "errores": [],
    }

    if not ANUARIO_METRICAS_CSV.exists():
        resultado["errores"].append(f"No existe {ANUARIO_METRICAS_CSV}")
        _escribir_reporte(resultado, [], [])
        return resultado

    df = pd.read_csv(ANUARIO_METRICAS_CSV)
    for col in ["anio", "metric_name", "value", "unit", "entity_name"]:
        if col not in df.columns:
            resultado["errores"].append(f"Falta columna: {col}")
            _escribir_reporte(resultado, [], [])
            return resultado

    # Coerce numeric
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["anio", "value"])
    df = df[df["value"].notna() & (df["value"] >= 0)]

    tasas_legacy = load_tasas_anuales()
    bcv = load_tasas_bcv_cierre_promedio()
    anios_en_datos = sorted(df["anio"].dropna().unique().astype(int).tolist())
    resultado["anios_con_datos"] = len(anios_en_datos)
    for anio in anios_en_datos:
        if anio not in bcv and anio not in tasas_legacy:
            resultado["anios_sin_tasa"].append(anio)

    # Indicadores por año y métrica (valor original + USD con lógica stock/flujo)
    filas = []
    for (anio, metric_name), grp in df.groupby(["anio", "metric_name"]):
        anio = int(anio)
        unit = grp["unit"].mode().iloc[0] if grp["unit"].notna().any() else ""
        total_miles = grp["value"].sum()
        n_obs = len(grp)
        n_entidades = grp["entity_name"].nunique()

        total_usd = None
        unidad_monetaria = ""
        tipo_tasa = ""
        if unit in ("miles_Bs", "miles_Bs o %") and metric_name in METRICAS_MONETARIAS:
            res = convertir_con_valor_original(float(total_miles), anio, metric_name)
            total_usd = res.valor_usd
            unidad_monetaria = res.unidad_monetaria
            tipo_tasa = "mercado" if getattr(res, "uso_tasa_mercado", False) else ("promedio" if res.es_flujo else "cierre")
        elif "%" in str(unit):
            pass  # porcentajes no se convierten

        filas.append({
            "anio": anio,
            "metric_name": metric_name,
            "unit": unit,
            "valor_original_miles": round(total_miles, 4),
            "valor_original_unidades_anio": round(total_miles * 1000, 4) if total_miles and unit in ("miles_Bs", "miles_Bs o %") else "",
            "unidad_monetaria": unidad_monetaria,
            "tipo_tasa_bcv": tipo_tasa,
            "total_usd": round(total_usd, 4) if total_usd is not None else "",
            "n_observaciones": n_obs,
            "n_entidades": n_entidades,
            "promedio_miles": round(total_miles / n_entidades, 4) if n_entidades else "",
        })
        resultado["metricas_procesadas"] += 1

    out = pd.DataFrame(filas)
    resultado["filas_indicadores"] = len(out)
    out.to_csv(INDICADORES_CSV, index=False, encoding="utf-8")

    # Resumen por año: n empresas (distintas entidades con al menos una métrica)
    entidades_por_anio = df.groupby("anio")["entity_name"].nunique().reset_index()
    entidades_por_anio.columns = ["anio", "n_entidades_unicas"]
    resumen_anios = entidades_por_anio.to_dict("records")

    _escribir_reporte(resultado, resumen_anios, filas)
    return resultado


def _escribir_reporte(
    resultado: dict,
    resumen_anios: list[dict],
    filas: list[dict],
) -> None:
    """Escribe reporte_corrida_fria.txt con resumen y advertencias."""
    lineas = [
        "=== Reporte corrida en frío - Indicadores Seguro en Cifras ===",
        "",
        f"Años con datos: {resultado.get('anios_con_datos', 0)}",
        f"Filas de indicadores generadas: {resultado.get('filas_indicadores', 0)}",
        "",
    ]
    if resultado.get("anios_sin_tasa"):
        lineas.append(f"Advertencia: años sin tasa de cambio (conversión USD nula): {resultado['anios_sin_tasa']}")
        lineas.append("  Actualizar tasa_cambio_anual.csv y/o tasa_cambio_bcv_2014_2024.csv con datos BCV.")
        lineas.append("")
    if resultado.get("errores"):
        lineas.append("Errores:")
        for e in resultado["errores"]:
            lineas.append(f"  - {e}")
        lineas.append("")
    lineas.append("--- Resumen por año (entidades con al menos una métrica) ---")
    for r in resumen_anios:
        lineas.append(f"  {r.get('anio', '')}: {r.get('n_entidades_unicas', 0)} entidades")
    lineas.append("")
    lineas.append("--- Totales primas y siniestros (muestra: valor original + USD) ---")
    for f in filas:
        if f.get("metric_name") in ("primas_netas_cobradas", "siniestros_pagados") and f.get("valor_original_miles") is not None:
            tm = f["valor_original_miles"]
            usd = f.get("total_usd") if f.get("total_usd") not in (None, "") else "N/A"
            unidad = f.get("unidad_monetaria") or "miles"
            lineas.append(f"  {f['anio']} {f['metric_name']}: valor_original={tm:.2f} miles {unidad}, total_usd={usd}")
    lineas.append("")
    lineas.append("Fin del reporte.")
    REPORTE_TXT.write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    res = run_corrida_fria()
    print("Corrida en frío terminada.")
    print(f"  Indicadores: {INDICADORES_CSV}")
    print(f"  Reporte: {REPORTE_TXT}")
    if res.get("anios_sin_tasa"):
        print("  Advertencia: hay años sin tasa; actualizar tasa_cambio_anual.csv.")
    if res.get("errores"):
        for e in res["errores"]:
            print("  Error:", e)
