# scripts/verificar_cruce_cuadro11_cuadro10.py
"""
Verifica el Cuadro 11 (Reservas de prima por empresa, pág 38) contra el Cuadro 10 (Reservas por ramo):
- Por línea en Cuadro 11: RETENCION_PROPIA + A_CARGO_REASEGURADORES = TOTAL.
- Suma de todas las empresas (excluyendo fila TOTAL) debe coincidir con la fila TOTAL del Cuadro 10
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
    """Verifica Cuadro 11: suma por línea y suma empresas = Cuadro 10 TOTAL."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path10 = carpeta / "cuadro_10_reservas_prima_por_ramo.csv"
    path11 = carpeta / "cuadro_11_reservas_prima_por_empresa.csv"
    if not path10.exists() or not path11.exists():
        print("[ERROR] Faltan cuadro_10 o cuadro_11 en {}.".format(carpeta))
        return False
    df10 = pd.read_csv(path10, sep=SEP, encoding=ENCODING)
    df11 = pd.read_csv(path11, sep=SEP, encoding=ENCODING)
    # Cuadro 10: fila TOTAL (última)
    total_10 = df10[df10["RAMO_DE_SEGUROS"].astype(str).str.strip().str.upper() == "TOTAL"].iloc[-1]
    ret_10 = float(total_10["RETENCION_PROPIA"])
    reas_10 = float(total_10["A_CARGO_REASEGURADORES"])
    tot_10 = float(total_10["TOTAL"])
    # Cuadro 11: excluir fila TOTAL, sumar empresas
    df11_emp = df11[df11["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"]
    sum_ret = df11_emp["RETENCION_PROPIA"].sum()
    sum_reas = df11_emp["A_CARGO_REASEGURADORES"].sum()
    sum_tot = df11_emp["TOTAL"].sum()
    todo_ok = True
    print("")
    print("  Cuadro 11 vs Cuadro 10 – Reservas de prima por empresa")
    print("")
    # Por línea
    for i in range(len(df11)):
        r = df11["RETENCION_PROPIA"].iloc[i] + df11["A_CARGO_REASEGURADORES"].iloc[i]
        if abs(r - df11["TOTAL"].iloc[i]) > TOLERANCIA:
            todo_ok = False
            break
    if todo_ok:
        print("  Por linea: Retencion + Reaseguradores = Total  OK")
    diff_ret = abs(sum_ret - ret_10)
    diff_reas = abs(sum_reas - reas_10)
    diff_tot = abs(sum_tot - tot_10)
    if diff_ret > TOLERANCIA or diff_reas > TOLERANCIA or diff_tot > TOLERANCIA:
        todo_ok = False
        print("  [Cruce 11 vs 10] Suma empresas vs Cuadro 10 TOTAL:")
        print("    Retencion:   {:,.0f} (C11) vs {:,.0f} (C10)  diff {:,.0f}".format(sum_ret, ret_10, diff_ret))
        print("    Reaseguro:   {:,.0f} (C11) vs {:,.0f} (C10)  diff {:,.0f}".format(sum_reas, reas_10, diff_reas))
        print("    Total:       {:,.0f} (C11) vs {:,.0f} (C10)  diff {:,.0f}".format(sum_tot, tot_10, diff_tot))
    else:
        print("  Suma empresas (Cuadro 11) = TOTAL Cuadro 10  OK (Retencion, Reaseguro, Total)")
    print("")
    if todo_ok:
        print("  Resultado: COINCIDE.")
    else:
        print("  Resultado: HAY DISCREPANCIAS.")
    print("")
    return todo_ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 11 vs Cuadro 10 (reservas prima por empresa)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
