"""
Verifica Cuadro 50 (Circulante Activo por empresa - financiadoras de primas) vs Cuadro 47
(Balance condensado financiadoras de primas).

- El total del Cuadro 50 (fila TOTAL o suma de columna TOTAL por empresa) debe coincidir
  con el concepto CIRCULANTE (activo) del Cuadro 47, es decir la línea CIRCULANTE bajo la
  sección ACTIVOS.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 50.0


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path47 = carpeta / "cuadro_47_balance_condensado_financiadoras_primas.csv"
    path50 = carpeta / "cuadro_50_circulante_activo_por_empresa_financiadoras_primas.csv"
    if not path47.exists():
        print("[ERROR] No existe {}.".format(path47))
        return False
    if not path50.exists():
        print("[ERROR] No existe {}.".format(path50))
        return False
    df47 = pd.read_csv(path47, sep=SEP, encoding=ENCODING)
    df50 = pd.read_csv(path50, sep=SEP, encoding=ENCODING)
    # C47: primer CIRCULANTE (bajo ACTIVOS), no el de PASIVOS
    visto_activos = False
    ref_circulante = None
    for _, r in df47.iterrows():
        c = str(r["CONCEPTO"]).strip().upper()
        if c == "ACTIVOS":
            visto_activos = True
            continue
        if visto_activos and c == "TOTAL ACTIVO":
            break
        if visto_activos and c == "CIRCULANTE":
            ref_circulante = float(r["MONTO"])
            break
    if ref_circulante is None:
        print("[ERROR] No se encontró CIRCULANTE (activo) en Cuadro 47.")
        return False
    # C50: fila TOTAL o suma de columna TOTAL (excl. fila TOTAL)
    total_row = df50[df50["NOMBRE_EMPRESA"].str.upper().str.strip() == "TOTAL"]
    if not total_row.empty:
        total50 = float(total_row.iloc[0]["TOTAL"])
    else:
        total50 = df50["TOTAL"].sum()
    diff = abs(total50 - ref_circulante)
    ok = diff <= TOLERANCIA
    print("")
    print("  Cuadro 50 (Circulante Activo por empresa) vs Cuadro 47 (CIRCULANTE bajo ACTIVOS)")
    print("  Total C50 = {}   C47 CIRCULANTE (activo) = {}   diff = {}  {}".format(
        total50, ref_circulante, diff, "OK" if ok else "FAIL"))
    print("")
    return ok


if __name__ == "__main__":
    anio = 2023
    if len(sys.argv) > 1 and "--year" in sys.argv:
        for i, a in enumerate(sys.argv):
            if a == "--year" and i + 1 < len(sys.argv):
                try:
                    anio = int(sys.argv[i + 1])
                except ValueError:
                    pass
                break
    ok = run_verificacion(anio)
    sys.exit(0 if ok else 1)
