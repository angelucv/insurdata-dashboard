"""
Verifica Cuadro 20-F (reservas para prestaciones y siniestros pendientes por ramo/empresa SEGUROS OBLIGACIONALES/RESPONSABILIDAD) contra Cuadro 19:
- La suma por columnas de los 8 ramos en 20-F (pág 59+60, sin columna TOTAL) debe coincidir con la columna Retención propia del Cuadro 19 (y con la fila SEGUROS DE RESPONSABILIDAD del Cuadro 15).
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
    path19 = carpeta / "cuadro_19_reservas_prestaciones_siniestros_obligacionales_por_empresa.csv"
    path59 = carpeta / "cuadro_20F_pag59_5_ramos.csv"
    path60 = carpeta / "cuadro_20F_pag60_3_ramos_total.csv"
    for p in (path19, path59, path60):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df19 = pd.read_csv(path19, sep=SEP, encoding=ENCODING)
    df59 = pd.read_csv(path59, sep=SEP, encoding=ENCODING)
    df60 = pd.read_csv(path60, sep=SEP, encoding=ENCODING)
    fila_total = df19[df19.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"]
    total_c19 = float(fila_total["RETENCION_PROPIA"].iloc[0]) if len(fila_total) else df19["RETENCION_PROPIA"].sum()
    total_20f = sum(df59[c].sum() for c in df59.columns if c != "Nombre Empresa")
    total_20f += sum(df60[c].sum() for c in df60.columns if c not in ("Nombre Empresa", "TOTAL"))
    todo_ok = abs(total_20f - total_c19) <= TOLERANCIA
    print("")
    print("  Cuadro 20-F vs Cuadro 19 – Reservas prestaciones/siniestros pendientes OBLIGACIONALES/RESPONSABILIDAD")
    print("")
    if todo_ok:
        print("  Suma 8 ramos 20-F = {:,.0f}   Cuadro 19 total (Retención propia) = {:,.0f}   OK".format(total_20f, total_c19))
    else:
        print("  Suma 8 ramos 20-F = {:,.0f}   Cuadro 19 total = {:,.0f}   Diferencia = {:,.0f}   FALLO".format(total_20f, total_c19, total_20f - total_c19))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
