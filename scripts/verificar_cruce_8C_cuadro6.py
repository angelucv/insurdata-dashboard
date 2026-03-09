# scripts/verificar_cruce_8C_cuadro6.py
"""
Verifica que el Cuadro 8-C (Siniestros Obligacionales por ramo/empresa, pág 34 y 35)
coincida por ramo con el Cuadro 6 (Siniestros por ramo – 8 ramos Seguros Obligacionales).
- Pág 34: 5 ramos (R.C. Automóvil, R.C. Patronal, R.C. General, R.C. Profesional, Fianzas).
- Pág 35: 3 ramos + TOTAL (Fidelidad de Empleados, R.C. de Productos, Seguros de Crédito, TOTAL).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED
from scripts.verificar_cruce_5C_cuadro3 import RAMOS_SEG_OBLIGACIONALES

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 50


def _normalizar(s: str) -> str:
    return s.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def _valor_cuadro6_ramo(df6, nombre_ramo: str) -> float | None:
    """Devuelve SEGURO DIRECTO del ramo en Cuadro 6. Coincidencia exacta normalizada."""
    col_ramo = df6.iloc[:, 0]
    n = _normalizar(nombre_ramo.strip())
    for i in range(len(df6)):
        r = _normalizar(str(col_ramo.iloc[i]).strip())
        if r == n:
            return float(df6["SEGURO DIRECTO"].iloc[i])
    return None


def run_verificacion(anio: int = 2023) -> bool:
    """Compara sumas por columna del Cuadro 8-C con valores del Cuadro 6."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path6 = carpeta / "cuadro_06_siniestros_pagados_por_ramo.csv"
    path_p34 = carpeta / "cuadro_08C_pag34_5_ramos.csv"
    path_p35 = carpeta / "cuadro_08C_pag35_3_ramos_total.csv"
    if not path6.exists() or not path_p34.exists() or not path_p35.exists():
        print("[ERROR] Faltan cuadro_06 o cuadro_08C en {}.".format(carpeta))
        return False
    df6 = pd.read_csv(path6, sep=SEP, encoding=ENCODING)
    df34 = pd.read_csv(path_p34, sep=SEP, encoding=ENCODING)
    df35 = pd.read_csv(path_p35, sep=SEP, encoding=ENCODING)

    for df in (df34, df35):
        df.drop(df[df.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"].index, inplace=True)

    ok = True
    print("")
    print("  Cuadro 8-C vs Cuadro 6 – Siniestros Obligacionales (8 ramos)")
    print("")

    for idx, col in enumerate(RAMOS_SEG_OBLIGACIONALES):
        if idx < 5:
            sum_8c = df34[col].sum()
        else:
            sum_8c = df35[col].sum()
        nombre_c6 = col.replace("Automóvil", "Automovil").replace("Crédito", "Credito")
        val_c6 = _valor_cuadro6_ramo(df6, nombre_c6)
        if val_c6 is None:
            val_c6 = _valor_cuadro6_ramo(df6, col)
        c6 = val_c6 if val_c6 is not None else 0
        diff = abs(sum_8c - c6)
        coincide = diff <= TOLERANCIA
        if not coincide:
            ok = False
        print("    {:40s}  8-C: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
            col[:40], sum_8c, c6, "OK" if coincide else "NO COINCIDE", "(diff {:.0f})".format(diff) if not coincide else ""))

    total_8c = df34[[RAMOS_SEG_OBLIGACIONALES[i] for i in range(5)]].sum().sum()
    total_8c += df35[[RAMOS_SEG_OBLIGACIONALES[i] for i in range(5, 8)]].sum().sum()
    total_c6 = _valor_cuadro6_ramo(df6, "SEGUROS OBLIGACIONALES Y/O DE RESPONSABILIDAD")
    if total_c6 is None:
        for i in range(len(df6)):
            r = str(df6.iloc[i, 0]).strip().upper()
            if "OBLIGACIONALES" in r and "PATRIMONIALES" not in r:
                total_c6 = float(df6["SEGURO DIRECTO"].iloc[i])
                break
    total_c6 = total_c6 if total_c6 is not None else 0
    diff_total = abs(total_8c - total_c6)
    coincide_total = diff_total <= TOLERANCIA
    if not coincide_total:
        ok = False
    print("    {:40s}  8-C: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
        "SUBTOTAL OBLIGACIONALES", total_8c, total_c6, "OK" if coincide_total else "NO COINCIDE", "(diff {:.0f})".format(diff_total) if not coincide_total else ""))
    print("")
    if ok:
        print("  Resultado: COINCIDE (totales 8-C = Cuadro 6, salvo redondeo).")
    else:
        print("  Resultado: HAY DIFERENCIAS.")
    print("")
    return ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 8-C vs Cuadro 6 (siniestros Obligacionales)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
