"""
Verifica Cuadro 31-B (Primas netas cobradas - Prestaciones y siniestros pagados 1990-2023) contra otras tablas.

Solo se cruza la **última línea (año 2023)**:
- PRIMAS_NETAS_COBRADAS (2023) = Total primas del ejercicio → Cuadro 4 (suma TOTAL) o Cuadro 31-A (fila Total PRIMAS_2023).
- PRESTACIONES_SINIESTROS_PAGADOS (2023) = Total siniestros → Cuadro 6 (fila TOTAL).

Nota: La serie 31-B está en año base 2007; los valores antiguos están cercanos a cero. La indexación se corregirá al recopilar más anuarios.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 500.0  # redondeo


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path31b = carpeta / "cuadro_31B_primas_prestaciones_siniestros_1990_2023.csv"
    path4 = carpeta / "cuadro_04_primas_por_ramo_empresa.csv"
    path31a = carpeta / "cuadro_31A_primas_netas_cobradas_2023_vs_2022.csv"
    path6 = carpeta / "cuadro_06_siniestros_pagados_por_ramo.csv"

    for p in (path31b, path4, path6):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df31b = pd.read_csv(path31b, sep=SEP, encoding=ENCODING)
    df4 = pd.read_csv(path4, sep=SEP, encoding=ENCODING)
    df6 = pd.read_csv(path6, sep=SEP, encoding=ENCODING)

    fila_2023 = df31b[df31b["AÑO"] == 2023]
    if fila_2023.empty:
        print("[ERROR] No se encontró el año 2023 en Cuadro 31-B.")
        return False
    primas_31b = float(fila_2023["PRIMAS_NETAS_COBRADAS"].iloc[0])
    siniestros_31b = float(fila_2023["PRESTACIONES_SINIESTROS_PAGADOS"].iloc[0])

    total_primas_c4 = df4["TOTAL"].sum()
    total_siniestros_c6 = df6[df6["RAMO DE SEGUROS"].astype(str).str.strip().str.upper() == "TOTAL"]["TOTAL"].iloc[0]
    if path31a.exists():
        df31a = pd.read_csv(path31a, sep=SEP, encoding=ENCODING)
        fila_total_31a = df31a[df31a["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL"]
        total_primas_31a = float(fila_total_31a["PRIMAS_2023"].iloc[0]) if len(fila_total_31a) > 0 else None
    else:
        total_primas_31a = None

    todo_ok = True
    print("")
    print("  Cuadro 31-B – Cruce de la última línea (2023) con C4/C31-A y C6")
    print("")

    ref_primas = total_primas_31a if total_primas_31a is not None else total_primas_c4
    if abs(primas_31b - ref_primas) <= TOLERANCIA:
        print("  OK  Primas Netas Cobradas (2023) C31-B = {:,.0f}   Referencia (C31-A Total / C4) = {:,.0f}".format(primas_31b, ref_primas))
    else:
        print("  FALLO  Primas (2023) C31-B = {:,.0f}   C4 sum = {:,.0f}   C31-A Total = {}".format(
            primas_31b, total_primas_c4, total_primas_31a))
        todo_ok = False

    if abs(siniestros_31b - total_siniestros_c6) <= TOLERANCIA:
        print("  OK  Prestaciones y Siniestros Pagados (2023) C31-B = {:,.0f}   C6 TOTAL = {:,.0f}".format(
            siniestros_31b, total_siniestros_c6))
    else:
        print("  FALLO  Siniestros (2023) C31-B = {:,.0f}   C6 TOTAL = {:,.0f}".format(
            siniestros_31b, total_siniestros_c6))
        todo_ok = False
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
