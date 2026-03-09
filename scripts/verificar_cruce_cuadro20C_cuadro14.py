"""
Verifica Cuadro 20-C (reservas de prima por ramo/empresa SEGUROS OBLIGACIONALES Y/O DE RESPONSABILIDAD) contra Cuadro 14:
- La suma por columnas de los 8 ramos en 20-C (pág 52: 5 ramos + pág 53: 3 ramos, sin columna TOTAL)
  debe coincidir con la columna "Por Retención propia de la Empresa" del Cuadro 14.
- Cuadro 14 tiene una fila por empresa; la suma de RETENCION_PROPIA (o la fila TOTAL) es el total
  a comparar con la suma de los 8 ramos en 20-C.
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
    path14 = carpeta / "cuadro_14_reservas_prima_obligacionales_por_empresa.csv"
    path52 = carpeta / "cuadro_20C_pag52_5_ramos.csv"
    path53 = carpeta / "cuadro_20C_pag53_3_ramos_total.csv"
    for p in (path14, path52, path53):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df14 = pd.read_csv(path14, sep=SEP, encoding=ENCODING)
    df52 = pd.read_csv(path52, sep=SEP, encoding=ENCODING)
    df53 = pd.read_csv(path53, sep=SEP, encoding=ENCODING)

    # Cuadro 14: total "Por Retención propia" = suma empresas (excl. fila TOTAL) o fila TOTAL
    c14_sin_total = df14[df14.iloc[:, 0].astype(str).str.strip().str.upper() != "TOTAL"]
    total_c14 = c14_sin_total["RETENCION_PROPIA"].sum()
    fila_total_c14 = df14[df14.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"]
    if len(fila_total_c14) > 0:
        total_c14_fila = float(fila_total_c14["RETENCION_PROPIA"].iloc[0])
    else:
        total_c14_fila = total_c14

    # 20-C: suma de los 8 ramos (5 en p52 + 3 en p53, sin columna TOTAL)
    cols_ramos_p52 = [c for c in df52.columns if c != "Nombre Empresa"]
    cols_ramos_p53 = [c for c in df53.columns if c not in ("Nombre Empresa", "TOTAL")]
    sum_p52 = sum(df52[c].sum() for c in cols_ramos_p52)
    sum_p53_ramos = sum(df53[c].sum() for c in cols_ramos_p53)
    total_20c_8_ramos = sum_p52 + sum_p53_ramos

    todo_ok = True
    print("")
    print("  Cuadro 20-C vs Cuadro 14 – Reservas de prima SEGUROS OBLIGACIONALES/RESPONSABILIDAD (Retención propia)")
    print("")

    if abs(total_20c_8_ramos - total_c14_fila) <= TOLERANCIA:
        print("  Suma 8 ramos 20-C = {:,.0f}   Cuadro 14 total (Retención propia) = {:,.0f}   OK".format(
            total_20c_8_ramos, total_c14_fila))
    else:
        print("  Suma 8 ramos 20-C = {:,.0f}   Cuadro 14 total = {:,.0f}   Diferencia = {:,.0f}   FALLO".format(
            total_20c_8_ramos, total_c14_fila, total_20c_8_ramos - total_c14_fila))
        todo_ok = False

    if abs(total_c14 - total_c14_fila) > TOLERANCIA:
        print("  (Cuadro 14: suma empresas sin fila TOTAL = {:,.0f})".format(total_c14))

    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
