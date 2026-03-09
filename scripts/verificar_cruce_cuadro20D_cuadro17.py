"""
Verifica Cuadro 20-D (reservas para prestaciones y siniestros pendientes por ramo/empresa SEGUROS DE PERSONAS) contra Cuadro 17:
- La suma por columnas de los 9 ramos en 20-D (pág 54: 5 ramos + pág 55: 4 ramos, sin columna TOTAL)
  debe coincidir con la columna Retención propia del Cuadro 17 (y con la fila SEGURO DE PERSONAS del Cuadro 15).
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
    path17 = carpeta / "cuadro_17_reservas_prestaciones_siniestros_personas_por_empresa.csv"
    path54 = carpeta / "cuadro_20D_pag54_5_ramos.csv"
    path55 = carpeta / "cuadro_20D_pag55_4_ramos_total.csv"
    for p in (path17, path54, path55):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df17 = pd.read_csv(path17, sep=SEP, encoding=ENCODING)
    df54 = pd.read_csv(path54, sep=SEP, encoding=ENCODING)
    df55 = pd.read_csv(path55, sep=SEP, encoding=ENCODING)
    fila_total = df17[df17.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"]
    total_c17 = float(fila_total["RETENCION_PROPIA"].iloc[0]) if len(fila_total) else df17["RETENCION_PROPIA"].sum()
    cols54 = [c for c in df54.columns if c != "Nombre Empresa"]
    cols55 = [c for c in df55.columns if c not in ("Nombre Empresa", "TOTAL")]
    total_20d = sum(df54[c].sum() for c in cols54) + sum(df55[c].sum() for c in cols55)
    todo_ok = abs(total_20d - total_c17) <= TOLERANCIA
    print("")
    print("  Cuadro 20-D vs Cuadro 17 – Reservas prestaciones/siniestros pendientes SEGUROS DE PERSONAS")
    print("")
    if todo_ok:
        print("  Suma 9 ramos 20-D = {:,.0f}   Cuadro 17 total (Retención propia) = {:,.0f}   OK".format(total_20d, total_c17))
    else:
        print("  Suma 9 ramos 20-D = {:,.0f}   Cuadro 17 total = {:,.0f}   Diferencia = {:,.0f}   FALLO".format(total_20d, total_c17, total_20d - total_c17))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
