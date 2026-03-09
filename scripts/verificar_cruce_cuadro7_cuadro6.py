# scripts/verificar_cruce_cuadro7_cuadro6.py
"""
Verifica que los totales del Cuadro 7 (siniestros por ramo/empresa, pág 28)
coincidan con los valores del Cuadro 6 (siniestros por ramo): Hospitalización Individual,
Hospitalización Colectivo, Automóvil Casco, Resto de Ramos y TOTAL.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"


def _valor_cuadro6_por_ramo(df6, nombre_ramo: str, col: str = "SEGURO DIRECTO") -> float | None:
    """Devuelve el valor de la columna col para la fila cuyo ramo contiene nombre_ramo."""
    col_ramo = df6.iloc[:, 0]
    for i in range(len(df6)):
        if nombre_ramo.upper() in str(col_ramo.iloc[i]).upper():
            return float(df6[col].iloc[i])
    return None


def run_verificacion(anio: int = 2023) -> bool:
    """Compara totales Cuadro 7 vs Cuadro 6."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path6 = carpeta / "cuadro_06_siniestros_pagados_por_ramo.csv"
    path7 = carpeta / "cuadro_07_siniestros_por_ramo_empresa.csv"
    if not path6.exists() or not path7.exists():
        print("[ERROR] Faltan cuadro_06 o cuadro_07 en {}.".format(carpeta))
        return False
    df6 = pd.read_csv(path6, sep=SEP, encoding=ENCODING)
    df7 = pd.read_csv(path7, sep=SEP, encoding=ENCODING)
    # Cuadro 7: fila TOTAL es la última; o sumamos todas las filas excepto TOTAL
    df7_sin_total = df7[df7.iloc[:, 0].astype(str).str.strip().str.upper() != "TOTAL"]
    total_hosp_ind = df7_sin_total["Hospitalizacion Individual"].sum()
    total_hosp_col = df7_sin_total["Hospitalizacion Colectivo"].sum()
    total_auto = df7_sin_total["Automovil Casco"].sum()
    total_resto = df7_sin_total["Resto de Ramos"].sum()
    total_gral = df7_sin_total["TOTAL"].sum()
    # Cuadro 6: valores por ramo
    v_hosp_ind = _valor_cuadro6_por_ramo(df6, "Hospitalización Individual")
    v_hosp_col = _valor_cuadro6_por_ramo(df6, "Hospitalización Colectivo")
    v_auto = _valor_cuadro6_por_ramo(df6, "Automóvil casco")
    total_c6 = _valor_cuadro6_por_ramo(df6, "TOTAL")
    if total_c6 is None:
        total_c6 = float(df6["TOTAL"].iloc[-1])
    # Resto en Cuadro 6 = TOTAL - Hosp Ind - Hosp Col - Auto
    resto_c6 = total_c6 - (v_hosp_ind or 0) - (v_hosp_col or 0) - (v_auto or 0)
    tolerancia = max(1.0, total_gral * 0.0001)
    ok = True
    print("")
    print("  Cuadro 7 vs Cuadro 6 – Siniestros pagados")
    print("  Suma por columnas (Cuadro 7, sin fila TOTAL) vs valor en Cuadro 6:")
    for nombre, sum_c7, val_c6 in [
        ("Hospitalizacion Individual", total_hosp_ind, v_hosp_ind),
        ("Hospitalizacion Colectivo", total_hosp_col, v_hosp_col),
        ("Automovil Casco", total_auto, v_auto),
        ("Resto de Ramos", total_resto, resto_c6),
        ("TOTAL", total_gral, total_c6),
    ]:
        val_c6 = val_c6 if val_c6 is not None else 0
        diff = abs(sum_c7 - val_c6)
        coincide = diff <= tolerancia
        if not coincide:
            ok = False
        print("    {:30s}  C7: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
            nombre, sum_c7, val_c6, "OK" if coincide else "NO COINCIDE", "(diff {:.0f})".format(diff) if not coincide else ""))
    print("")
    if ok:
        print("  Resultado: COINCIDE (totales Cuadro 7 = Cuadro 6).")
    else:
        print("  Resultado: HAY DIFERENCIAS.")
    print("")
    return ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 7 vs Cuadro 6 (siniestros)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
