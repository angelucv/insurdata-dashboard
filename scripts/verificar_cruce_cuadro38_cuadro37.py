"""
Verifica Cuadro 38 (Cantidad de pólizas y siniestros por empresa) contra Cuadro 37 (por ramo):

1) Consistencia interna C38: suma de empresas (excl. fila TOTAL) = fila TOTAL en cada columna.
2) Los totales por columna del Cuadro 38 (fila TOTAL) deben coincidir con la fila TOTAL del Cuadro 37
   (misma información agregada por ramo en C37 y por empresa en C38).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 500.0  # diferencias de redondeo (cantidades)


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path38 = carpeta / "cuadro_38_cantidad_polizas_siniestros_por_empresa.csv"
    path37 = carpeta / "cuadro_37_cantidad_polizas_siniestros_por_ramo.csv"
    for p in (path38, path37):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df38 = pd.read_csv(path38, sep=SEP, encoding=ENCODING)
    df37 = pd.read_csv(path37, sep=SEP, encoding=ENCODING)

    todo_ok = True

    # 1) Consistencia interna C38: suma empresas = TOTAL
    df38_emp = df38[
        df38["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"
    ].copy()
    total_row = df38[df38["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL"]
    if total_row.empty:
        print("[ERROR] Cuadro 38: no se encontró fila TOTAL.")
        return False
    total_row = total_row.iloc[0]
    suma_pol = df38_emp["POLIZAS"].astype(float).sum()
    suma_sin = df38_emp["SINIESTROS"].astype(float).sum()
    t_pol = float(total_row["POLIZAS"])
    t_sin = float(total_row["SINIESTROS"])
    print("")
    print("  Cuadro 38 – Consistencia interna (suma empresas = TOTAL)")
    print("")
    for label, suma, ref in [("POLIZAS", suma_pol, t_pol), ("SINIESTROS", suma_sin, t_sin)]:
        diff = abs(suma - ref)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  {}: suma empresas={:.0f} TOTAL={:.0f} diff={:.0f} {}".format(
            label, suma, ref, diff, "OK" if ok else "FAIL"
        ))
    print("")

    # 2) C38 TOTAL = C37 TOTAL (fila TOTAL del Cuadro 37)
    total_37 = df37[df37["RAMO_DE_SEGUROS"].astype(str).str.strip().str.upper() == "TOTAL"]
    if total_37.empty:
        print("[ERROR] Cuadro 37: no se encontró fila TOTAL.")
        return False
    total_37 = total_37.iloc[0]
    c37_pol = float(total_37["POLIZAS"])
    c37_sin = float(total_37["SINIESTROS"])
    print("  Cuadro 38 TOTAL vs Cuadro 37 TOTAL (misma información por empresa / por ramo)")
    print("")
    ok_pol = abs(t_pol - c37_pol) <= TOLERANCIA
    ok_sin = abs(t_sin - c37_sin) <= TOLERANCIA
    if not ok_pol:
        todo_ok = False
    if not ok_sin:
        todo_ok = False
    print("  POLIZAS:   C38 TOTAL={:.0f}  C37 TOTAL={:.0f}  {}".format(t_pol, c37_pol, "OK" if ok_pol else "FAIL"))
    print("  SINIESTROS: C38 TOTAL={:.0f}  C37 TOTAL={:.0f}  {}".format(t_sin, c37_sin, "OK" if ok_sin else "FAIL"))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
