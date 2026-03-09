"""
Verifica Cuadro 20-E (reservas para prestaciones y siniestros pendientes por ramo/empresa SEGUROS PATRIMONIALES) contra Cuadro 18:
- La suma por columnas de los 16 ramos en 20-E (pág 56+57+58, sin columna TOTAL) debe coincidir con la columna Retención propia del Cuadro 18 (y con la fila SEGUROS PATRIMONIALES del Cuadro 15).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 10.0


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path18 = carpeta / "cuadro_18_reservas_prestaciones_siniestros_patrimoniales_por_empresa.csv"
    path56 = carpeta / "cuadro_20E_pag56_6_ramos.csv"
    path57 = carpeta / "cuadro_20E_pag57_6_ramos.csv"
    path58 = carpeta / "cuadro_20E_pag58_4_ramos_total.csv"
    for p in (path18, path56, path57, path58):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df18 = pd.read_csv(path18, sep=SEP, encoding=ENCODING)
    df56 = pd.read_csv(path56, sep=SEP, encoding=ENCODING)
    df57 = pd.read_csv(path57, sep=SEP, encoding=ENCODING)
    df58 = pd.read_csv(path58, sep=SEP, encoding=ENCODING)
    fila_total = df18[df18.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"]
    total_c18 = float(fila_total["RETENCION_PROPIA"].iloc[0]) if len(fila_total) else df18["RETENCION_PROPIA"].sum()
    total_20e = sum(df56[c].sum() for c in df56.columns if c != "Nombre Empresa")
    total_20e += sum(df57[c].sum() for c in df57.columns if c != "Nombre Empresa")
    total_20e += sum(df58[c].sum() for c in df58.columns if c not in ("Nombre Empresa", "TOTAL"))
    todo_ok = abs(total_20e - total_c18) <= TOLERANCIA
    print("")
    print("  Cuadro 20-E vs Cuadro 18 – Reservas prestaciones/siniestros pendientes SEGUROS PATRIMONIALES")
    print("")
    if todo_ok:
        print("  Suma 16 ramos 20-E = {:,.0f}   Cuadro 18 total (Retención propia) = {:,.0f}   OK".format(total_20e, total_c18))
    else:
        print("  Suma 16 ramos 20-E = {:,.0f}   Cuadro 18 total = {:,.0f}   Diferencia = {:,.0f}   FALLO".format(total_20e, total_c18, total_20e - total_c18))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
