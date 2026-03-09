# scripts/verificar_cruce_cuadros18_19_cuadro15.py
"""
Verifica Cuadros 18 y 19 (reservas prestaciones/siniestros pendientes por empresa: Patrimoniales y Obligacionales)
contra el Cuadro 15 (por ramo):
- Suma empresas Cuadro 18 = fila "SEGUROS PATRIMONIALES" del Cuadro 15.
- Suma empresas Cuadro 19 = fila "SEGUROS DE RESPONSABILIDAD" del Cuadro 15.
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
    """Verifica: suma C18 = SEGUROS PATRIMONIALES (C15); suma C19 = SEGUROS DE RESPONSABILIDAD (C15)."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path15 = carpeta / "cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv"
    path18 = carpeta / "cuadro_18_reservas_prestaciones_siniestros_patrimoniales_por_empresa.csv"
    path19 = carpeta / "cuadro_19_reservas_prestaciones_siniestros_obligacionales_por_empresa.csv"
    for p in (path15, path18, path19):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df15 = pd.read_csv(path15, sep=SEP, encoding=ENCODING)
    df18 = pd.read_csv(path18, sep=SEP, encoding=ENCODING)
    df19 = pd.read_csv(path19, sep=SEP, encoding=ENCODING)
    ramo = df15["RAMO_DE_SEGUROS"].astype(str).str.strip().str.upper()
    todo_ok = True
    print("")
    print("  Cuadros 18, 19 vs Cuadro 15 – Reservas prestaciones/siniestros (Patrimoniales, Obligacionales) por empresa")
    print("")

    # Cuadro 18 = SEGUROS PATRIMONIALES
    idx = ramo[ramo == "SEGUROS PATRIMONIALES"].index
    if len(idx) == 0:
        print("  [ERROR] Cuadro 15 no tiene fila 'SEGUROS PATRIMONIALES'.")
        todo_ok = False
    else:
        fila = df15.loc[idx[0]]
        r15, re15, t15 = float(fila["RETENCION_PROPIA"]), float(fila["A_CARGO_REASEGURADORES"]), float(fila["TOTAL"])
        d18 = df18[df18["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"]
        s_ret, s_reas, s_tot = d18["RETENCION_PROPIA"].sum(), d18["A_CARGO_REASEGURADORES"].sum(), d18["TOTAL"].sum()
        if abs(s_ret - r15) <= TOLERANCIA and abs(s_reas - re15) <= TOLERANCIA and abs(s_tot - t15) <= TOLERANCIA:
            print("  Cuadro 18 (Patrimoniales)  suma empresas = SEGUROS PATRIMONIALES (C15)  OK")
        else:
            print("  Cuadro 18: suma Ret {:,.0f} Reas {:,.0f} Total {:,.0f} vs C15 {:,.0f} {:,.0f} {:,.0f}".format(s_ret, s_reas, s_tot, r15, re15, t15))
            todo_ok = False

    # Cuadro 19 = SEGUROS DE RESPONSABILIDAD
    idx = ramo[ramo == "SEGUROS DE RESPONSABILIDAD"].index
    if len(idx) == 0:
        print("  [ERROR] Cuadro 15 no tiene fila 'SEGUROS DE RESPONSABILIDAD'.")
        todo_ok = False
    else:
        fila = df15.loc[idx[0]]
        r15, re15, t15 = float(fila["RETENCION_PROPIA"]), float(fila["A_CARGO_REASEGURADORES"]), float(fila["TOTAL"])
        d19 = df19[df19["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"]
        s_ret, s_reas, s_tot = d19["RETENCION_PROPIA"].sum(), d19["A_CARGO_REASEGURADORES"].sum(), d19["TOTAL"].sum()
        if abs(s_ret - r15) <= TOLERANCIA and abs(s_reas - re15) <= TOLERANCIA and abs(s_tot - t15) <= TOLERANCIA:
            print("  Cuadro 19 (Obligacionales)  suma empresas = SEGUROS DE RESPONSABILIDAD (C15)  OK")
        else:
            print("  Cuadro 19: suma Ret {:,.0f} Reas {:,.0f} Total {:,.0f} vs C15 {:,.0f} {:,.0f} {:,.0f}".format(s_ret, s_reas, s_tot, r15, re15, t15))
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
    p = argparse.ArgumentParser(description="Verificar Cuadros 18, 19 vs Cuadro 15 (reservas prestaciones/siniestros por sección)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
