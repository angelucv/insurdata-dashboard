"""
Verifica Cuadro 35 (Devolución de primas por ramo/empresa: Personas + Generales):

Consistencia interna: la suma de las filas por empresa (excl. TOTAL) debe coincidir con la fila TOTAL
en cada una de las 6 columnas.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 500.0  # diferencias de redondeo en totales


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path35 = carpeta / "cuadro_35_devolucion_primas_personas_generales_por_empresa.csv"
    if not path35.exists():
        print("[ERROR] No existe {}.".format(path35))
        return False
    df35 = pd.read_csv(path35, sep=SEP, encoding=ENCODING)

    df35_emp = df35[
        df35["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"
    ].copy()
    total_row = df35[df35["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL"]
    if total_row.empty:
        print("[ERROR] Cuadro 35: no se encontró fila TOTAL.")
        return False
    total_row = total_row.iloc[0]
    cols = [
        "PERSONAS_SEGURO_DIRECTO",
        "PERSONAS_REASEGURO_ACEPTADO",
        "PERSONAS_TOTAL",
        "GENERALES_SEGURO_DIRECTO",
        "GENERALES_REASEGURO_ACEPTADO",
        "GENERALES_TOTAL",
    ]
    todo_ok = True
    print("")
    print("  Cuadro 35 – Consistencia interna (suma empresas = TOTAL)")
    print("")
    for c in cols:
        suma = df35_emp[c].astype(float).sum()
        ref = float(total_row[c])
        diff = abs(suma - ref)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  {}: suma={:.0f} TOTAL={:.0f} diff={:.0f} {}".format(
            c, suma, ref, diff, "OK" if ok else "FAIL"
        ))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
