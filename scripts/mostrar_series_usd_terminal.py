"""
Muestra en terminal las series 2014-2024 de campos convertidos a USD (mercado agregado por año)
para verificación de consistencia. Ventana fija: serie histórica 2014 a 2024.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.anuarios_paths import SEGURO_EN_CIFRAS_INDICE

INDICADORES_CSV = SEGURO_EN_CIFRAS_INDICE / "indicadores_corrida_fria.csv"

ANIO_INICIO = 2014
ANIO_FIN = 2024
VENTANA_ANIOS = list(range(ANIO_INICIO, ANIO_FIN + 1))


def main() -> None:
    if not INDICADORES_CSV.exists():
        print("No existe", INDICADORES_CSV, "- ejecutar antes: python scripts/indicadores_corrida_fria.py")
        return

    df = pd.read_csv(INDICADORES_CSV)
    df["total_usd"] = pd.to_numeric(df["total_usd"], errors="coerce")
    # Filtrar solo ventana 2014-2024
    df = df[df["anio"].between(ANIO_INICIO, ANIO_FIN)]
    con_usd = df[df["total_usd"].notna() & (df["total_usd"] > 0)].copy()
    con_usd["anio"] = con_usd["anio"].astype(int)

    # Pivot: filas = anio, columnas = metric_name
    pivot = con_usd.pivot_table(index="anio", columns="metric_name", values="total_usd", aggfunc="first")
    pivot = pivot.round(2)

    # Reindexar para que aparezcan TODOS los años 2014-2024 (aunque no tengan dato)
    pivot = pivot.reindex(VENTANA_ANIOS)

    # Orden de columnas
    preferido = [
        "primas_netas_cobradas", "primas_netas_por_ramo", "siniestros_pagados",
        "reservas_primas", "reservas_tecnicas", "capital_garantia", "capital_pagado",
        "garantia_deposito", "resultados_economicos", "comisiones_gastos_adquisicion",
        "ingresos_netos", "gastos_operativos", "activo_total", "pasivo_total",
    ]
    cols = [c for c in preferido if c in pivot.columns]
    cols += [c for c in pivot.columns if c not in cols]
    pivot = pivot[cols]

    print("=" * 80)
    print("SERIE HISTORICA 2014-2024 - MERCADO AGREGADO EN USD")
    print("Fuente: indicadores_corrida_fria.csv (BCV / tasa mercado siniestros)")
    print("=" * 80)
    print()
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.float_format", lambda x: f"{x:,.2f}" if pd.notna(x) else "")
    print(pivot.to_string())
    print()
    print("--- Anos con dato por campo (solo ventana 2014-2024) ---")
    for c in pivot.columns:
        n = pivot[c].notna().sum()
        anos = pivot.index[pivot[c].notna()].tolist()
        print(f"  {c}: {n} anos {anos}")
    print()
    print("--- Suma de campos con USD por ano (solo 2014-2024) ---")
    suma = pivot.sum(axis=1)
    for anio in VENTANA_ANIOS:
        val = suma.get(anio)
        s = f"{val:,.2f}" if pd.notna(val) and val != 0 else "-"
        print(f"  {anio}: {s} USD")
    print()
    print("Nota: Si 2014-2023 aparecen vacios, aun no hay metricas en USD para esos anos")
    print("      en el vaciado/matriz. Cargar anuarios 2014-2023 para completar la serie.")
    print()


if __name__ == "__main__":
    main()
