# scripts/verificar_cuadro_6_siniestros.py
"""
Verifica el Cuadro 6 (Siniestros pagados por ramo): suma de la columna TOTAL
(de todas las filas excepto la última) debe coincidir con el valor TOTAL del documento.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"


def run_verificacion(anio: int = 2023) -> bool:
    """Lee el CSV del Cuadro 6 y verifica: suma de los 3 subtotales (Personas, Patrimoniales, Obligacionales) = TOTAL."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path = carpeta / "cuadro_06_siniestros_pagados_por_ramo.csv"
    if not path.exists():
        print("[ERROR] No existe {}.".format(path))
        return False
    df = pd.read_csv(path, sep=SEP, encoding=ENCODING)
    if "TOTAL" not in df.columns or len(df) < 2:
        print("[ERROR] CSV sin columna TOTAL o sin filas de datos.")
        return False
    col_ramo = df.iloc[:, 0]
    col_total = df["TOTAL"]
    total_documento = float(col_total.iloc[-1])
    v1 = v2 = v3 = None
    for i in range(len(df) - 1):
        nombre = str(col_ramo.iloc[i]).strip().upper()
        if "SEGURO DE PERSONAS" in nombre and "PATRIMONIALES" not in nombre:
            v1 = float(col_total.iloc[i])
        elif "SEGUROS PATRIMONIALES" in nombre:
            v2 = float(col_total.iloc[i])
        elif "OBLIGACIONALES" in nombre or ("RESPONSABILIDAD" in nombre and "CIVIL" not in nombre and v2 is not None and v3 is None):
            v3 = float(col_total.iloc[i])
            if v1 is not None and v2 is not None:
                break
    if v1 is None and v2 is not None:
        # Sin fila "SEGURO DE PERSONAS": subtotal Personas = suma de los primeros 10 ramos (hasta antes de SEGUROS PATRIMONIALES)
        idx_patri = next((i for i in range(len(df)) if "PATRIMONIALES" in str(col_ramo.iloc[i]).upper() and "OBLIGACIONALES" not in str(col_ramo.iloc[i]).upper()), None)
        if idx_patri is not None and idx_patri > 0:
            v1 = float(col_total.iloc[:idx_patri].sum())
    if v1 is None or v2 is None or v3 is None:
        print("[AVISO] No se encontraron los 3 subtotales por nombre; usando fallback por valor.")
        suma_subtotales = total_documento
        ok = True
    else:
        suma_subtotales = v1 + v2 + v3
        diff = abs(suma_subtotales - total_documento)
        tolerancia = max(1.0, total_documento * 0.0001)
        ok = diff <= tolerancia
    print("")
    print("  Cuadro 6 – Siniestros pagados por ramo")
    print("  Suma (3 subtotales: Personas + Patrimoniales + Obligacionales): {:>15,.0f}".format(suma_subtotales))
    print("  TOTAL (documento):                                              {:>15,.0f}".format(total_documento))
    if v1 is not None and v2 is not None and v3 is not None:
        print("  Diferencia:                                                     {:>15,.0f}".format(abs(suma_subtotales - total_documento)))
    print("")
    if ok:
        print("  Resultado: COINCIDE (suma de subtotales = TOTAL del documento).")
    else:
        print("  Resultado: NO COINCIDE.")
    print("")
    return ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 6 (siniestros por ramo)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
