"""
Verifica Cuadro 20-B (reservas de prima por ramo/empresa SEGUROS PATRIMONIALES) contra Cuadro 13:
- La suma por columnas de los 16 ramos en 20-B (pág 49: 6 ramos + pág 50: 6 ramos + pág 51: 4 ramos, sin columna TOTAL)
  debe coincidir con la columna "Por Retención propia de la Empresa" del Cuadro 13.
- Cuadro 13 tiene una fila por empresa; la suma de RETENCION_PROPIA (o la fila TOTAL) es el total
  a comparar con la suma de los 16 ramos en 20-B.
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
    path13 = carpeta / "cuadro_13_reservas_prima_patrimoniales_por_empresa.csv"
    path49 = carpeta / "cuadro_20B_pag49_6_ramos.csv"
    path50 = carpeta / "cuadro_20B_pag50_6_ramos.csv"
    path51 = carpeta / "cuadro_20B_pag51_4_ramos_total.csv"
    for p in (path13, path49, path50, path51):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df13 = pd.read_csv(path13, sep=SEP, encoding=ENCODING)
    df49 = pd.read_csv(path49, sep=SEP, encoding=ENCODING)
    df50 = pd.read_csv(path50, sep=SEP, encoding=ENCODING)
    df51 = pd.read_csv(path51, sep=SEP, encoding=ENCODING)

    # Cuadro 13: total "Por Retención propia" = suma empresas (excl. fila TOTAL) o fila TOTAL
    c13_sin_total = df13[df13.iloc[:, 0].astype(str).str.strip().str.upper() != "TOTAL"]
    total_c13 = c13_sin_total["RETENCION_PROPIA"].sum()
    fila_total_c13 = df13[df13.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"]
    if len(fila_total_c13) > 0:
        total_c13_fila = float(fila_total_c13["RETENCION_PROPIA"].iloc[0])
    else:
        total_c13_fila = total_c13

    # 20-B: suma de los 16 ramos (6 en p49 + 6 en p50 + 4 en p51, sin columna TOTAL)
    cols_ramos_p49 = [c for c in df49.columns if c != "Nombre Empresa"]
    cols_ramos_p50 = [c for c in df50.columns if c != "Nombre Empresa"]
    cols_ramos_p51 = [c for c in df51.columns if c not in ("Nombre Empresa", "TOTAL")]
    sum_p49 = sum(df49[c].sum() for c in cols_ramos_p49)
    sum_p50 = sum(df50[c].sum() for c in cols_ramos_p50)
    sum_p51_ramos = sum(df51[c].sum() for c in cols_ramos_p51)
    total_20b_16_ramos = sum_p49 + sum_p50 + sum_p51_ramos

    todo_ok = True
    print("")
    print("  Cuadro 20-B vs Cuadro 13 – Reservas de prima SEGUROS PATRIMONIALES (Retención propia)")
    print("")

    if abs(total_20b_16_ramos - total_c13_fila) <= TOLERANCIA:
        print("  Suma 16 ramos 20-B = {:,.0f}   Cuadro 13 total (Retención propia) = {:,.0f}   OK".format(
            total_20b_16_ramos, total_c13_fila))
    else:
        print("  Suma 16 ramos 20-B = {:,.0f}   Cuadro 13 total = {:,.0f}   Diferencia = {:,.0f}   FALLO".format(
            total_20b_16_ramos, total_c13_fila, total_20b_16_ramos - total_c13_fila))
        todo_ok = False

    if abs(total_c13 - total_c13_fila) > TOLERANCIA:
        print("  (Cuadro 13: suma empresas sin fila TOTAL = {:,.0f})".format(total_c13))

    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
