# scripts/verificar_cruce_cuadro17_cuadro15.py
"""
Verifica el Cuadro 17 (Reservas prestaciones/siniestros pendientes SEGUROS DE PERSONAS por empresa, pág 44)
contra el Cuadro 15 (por ramo):
- Suma de todas las empresas en Cuadro 17 (excl. fila TOTAL) debe coincidir con la fila "SEGURO DE PERSONAS" del Cuadro 15
  (RETENCION_PROPIA, A_CARGO_REASEGURADORES, TOTAL).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 5.0


def run_verificacion(anio: int = 2023) -> bool:
    """Verifica: suma empresas Cuadro 17 = fila SEGURO DE PERSONAS Cuadro 15."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path15 = carpeta / "cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv"
    path17 = carpeta / "cuadro_17_reservas_prestaciones_siniestros_personas_por_empresa.csv"
    if not path15.exists() or not path17.exists():
        print("[ERROR] Faltan cuadro_15 o cuadro_17 en {}.".format(carpeta))
        return False
    df15 = pd.read_csv(path15, sep=SEP, encoding=ENCODING)
    df17 = pd.read_csv(path17, sep=SEP, encoding=ENCODING)
    ramo = df15["RAMO_DE_SEGUROS"].astype(str).str.strip()
    idx = ramo[ramo.str.upper() == "SEGURO DE PERSONAS"].index
    if len(idx) == 0:
        print("[ERROR] Cuadro 15 no tiene fila 'SEGURO DE PERSONAS'.")
        return False
    fila_15 = df15.loc[idx[0]]
    ret_15 = float(fila_15["RETENCION_PROPIA"])
    reas_15 = float(fila_15["A_CARGO_REASEGURADORES"])
    tot_15 = float(fila_15["TOTAL"])
    df17_emp = df17[df17["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"]
    sum_ret = df17_emp["RETENCION_PROPIA"].sum()
    sum_reas = df17_emp["A_CARGO_REASEGURADORES"].sum()
    sum_tot = df17_emp["TOTAL"].sum()
    todo_ok = True
    print("")
    print("  Cuadro 17 vs Cuadro 15 – Reservas prestaciones/siniestros SEGUROS DE PERSONAS por empresa")
    print("")
    if abs(sum_ret - ret_15) <= TOLERANCIA and abs(sum_reas - reas_15) <= TOLERANCIA and abs(sum_tot - tot_15) <= TOLERANCIA:
        print("  Suma empresas (Cuadro 17) = SEGURO DE PERSONAS (Cuadro 15)  OK (Retencion, Reaseguro, Total)")
    else:
        print("  Suma C17: Ret {:,.0f}  Reas {:,.0f}  Total {:,.0f}".format(sum_ret, sum_reas, sum_tot))
        print("  SEGURO DE PERSONAS C15: Ret {:,.0f}  Reas {:,.0f}  Total {:,.0f}".format(ret_15, reas_15, tot_15))
        todo_ok = False
    print("")
    if todo_ok:
        print("  Resultado: COINCIDE.")
    else:
        print("  Resultado: HAY DISCREPANCIAS.")
    print("")
    return todo_ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 17 vs Cuadro 15 (reservas prestaciones/siniestros Personas por empresa)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
