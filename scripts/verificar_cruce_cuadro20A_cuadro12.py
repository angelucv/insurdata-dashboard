"""
Verifica Cuadro 20-A (reservas de prima por ramo/empresa SEGUROS DE PERSONAS) contra Cuadro 12:
- La suma por columnas de los 9 ramos en 20-A (pág 47: 5 ramos + pág 48: 4 ramos, sin columna TOTAL)
  debe coincidir con la columna "Por Retención propia de la Empresa" del Cuadro 12.
- Cuadro 12 tiene una fila por empresa; la suma de RETENCION_PROPIA (o la fila TOTAL) es el total
  a comparar con la suma de los 9 ramos en 20-A.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 10.0  # redondeos en miles


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path12 = carpeta / "cuadro_12_reservas_prima_personas_por_empresa.csv"
    path47 = carpeta / "cuadro_20A_pag47_5_ramos.csv"
    path48 = carpeta / "cuadro_20A_pag48_4_ramos_total.csv"
    for p in (path12, path47, path48):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df12 = pd.read_csv(path12, sep=SEP, encoding=ENCODING)
    df47 = pd.read_csv(path47, sep=SEP, encoding=ENCODING)
    df48 = pd.read_csv(path48, sep=SEP, encoding=ENCODING)

    # Cuadro 12: total "Por Retención propia" = suma empresas (excl. fila TOTAL) o fila TOTAL
    c12_sin_total = df12[df12.iloc[:, 0].astype(str).str.strip().str.upper() != "TOTAL"]
    total_c12 = c12_sin_total["RETENCION_PROPIA"].sum()
    fila_total_c12 = df12[df12.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"]
    if len(fila_total_c12) > 0:
        total_c12_fila = float(fila_total_c12["RETENCION_PROPIA"].iloc[0])
    else:
        total_c12_fila = total_c12

    # 20-A: suma de los 9 ramos (5 en p47 + 4 en p48, sin columna TOTAL)
    cols_ramos_p47 = [c for c in df47.columns if c != "Nombre Empresa"]
    cols_ramos_p48 = [c for c in df48.columns if c not in ("Nombre Empresa", "TOTAL")]
    sum_p47 = sum(df47[c].sum() for c in cols_ramos_p47)
    sum_p48_ramos = sum(df48[c].sum() for c in cols_ramos_p48)
    total_20a_9_ramos = sum_p47 + sum_p48_ramos

    todo_ok = True
    print("")
    print("  Cuadro 20-A vs Cuadro 12 – Reservas de prima SEGUROS DE PERSONAS (Retención propia)")
    print("")

    if abs(total_20a_9_ramos - total_c12_fila) <= TOLERANCIA:
        print("  Suma 9 ramos 20-A = {:,.0f}   Cuadro 12 total (Retención propia) = {:,.0f}   OK".format(
            total_20a_9_ramos, total_c12_fila))
    else:
        print("  Suma 9 ramos 20-A = {:,.0f}   Cuadro 12 total = {:,.0f}   Diferencia = {:,.0f}   FALLO".format(
            total_20a_9_ramos, total_c12_fila, total_20a_9_ramos - total_c12_fila))
        todo_ok = False

    if abs(total_c12 - total_c12_fila) > TOLERANCIA:
        print("  (Cuadro 12: suma empresas sin fila TOTAL = {:,.0f})".format(total_c12))

    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
