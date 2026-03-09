"""
Verifica Cuadro 41-B (Estado de Ganancias y Perdidas - Egresos, reaseguros):

1) Logica interna: subtotales y totales.
   - OPERACIONES TECNICAS = suma de lineas "padre" (excl. sublineas: AL PAIS, AL EXTERIOR, DEL PAIS, DEL EXTERIOR, NEGOCIOS NACIONALES, NEGOCIOS EXTRANJEROS, NACIONALES, EXTRANJERAS).
   - GESTION GENERAL = suma de sus lineas.
   - TOTAL EGRESOS = OPERACIONES TECNICAS + GESTION GENERAL.
   - TOTAL GENERAL = TOTAL EGRESOS + UTILIDAD DEL EJERCICIO.

2) Cruce con Cuadro 40 y 41-A: UTILIDAD C40 = Total Ingresos (41-A) - Total Egresos (41-B).
   Ademas UTILIDAD DEL EJERCICIO en 41-B debe coincidir con UTILIDAD en C40.
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
SUBLINEAS_41B = ("DEL PAIS", "DEL EXTERIOR", "AL PAIS", "AL EXTERIOR", "NEGOCIOS NACIONALES", "NEGOCIOS EXTRANJEROS", "NACIONALES", "EXTRANJERAS")


def _norm(s: str) -> str:
    t = s.upper().strip()
    for a, b in [("\u00c1", "A"), ("\u00c9", "E"), ("\u00cd", "I"), ("\u00d3", "O"), ("\u00da", "U")]:
        t = t.replace(a, b)
    return t


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path41b = carpeta / "cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros.csv"
    path41a = carpeta / "cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros.csv"
    path40 = carpeta / "cuadro_40_balance_condensado_reaseguros.csv"
    if not path41b.exists():
        print("[ERROR] No existe {}.".format(path41b))
        return False
    df = pd.read_csv(path41b, sep=SEP, encoding=ENCODING)
    if "TIPO" not in df.columns or "MONTO" not in df.columns:
        print("[ERROR] Cuadro 41-B debe tener columnas CONCEPTO, MONTO, TIPO.")
        return False

    todo_ok = True
    conceptos = df["CONCEPTO"].astype(str).str.strip()
    montos = df["MONTO"].astype(float)
    tipos = df["TIPO"].astype(str).str.strip()

    print("")
    print("  Cuadro 41-B - Estado de Ganancias y Perdidas. Egresos (reaseguros)")
    print("")

    # 1) OPERACIONES TECNICAS = suma lineas padre
    idx_op = (tipos == "SECCION") & (conceptos.str.upper().str.contains("OPERACIONES"))
    idx_gest = (tipos == "SECCION") & (conceptos.str.upper().str.contains("GESTI"))
    if idx_op.any():
        i_op = df.index[idx_op][0]
        i_gest = df.index[idx_gest][0] if idx_gest.any() else len(df)
        suma_op = 0.0
        for j in range(i_op + 1, i_gest):
            if tipos.iloc[j] != "LINEA":
                break
            c = _norm(conceptos.iloc[j])
            if c not in SUBLINEAS_41B:
                suma_op += montos.iloc[j]
        total_op = float(montos.iloc[i_op])
        diff = abs(suma_op - total_op)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  OPERACIONES TECNICAS:  suma lineas (padre) = {:.2f}   declarado = {:.2f}   diff = {:.2f}  {}".format(
            suma_op, total_op, diff, "OK" if ok else "FAIL"))
    else:
        print("  [AVISO] No se encontro seccion OPERACIONES TECNICAS.")

    # 2) GESTION GENERAL = suma de sus lineas
    if idx_gest.any():
        i_gest = df.index[idx_gest][0]
        idx_total_eg = tipos == "TOTAL_EGRESOS"
        i_end = df.index[idx_total_eg][0] if idx_total_eg.any() else len(df)
        suma_gest = montos.iloc[i_gest + 1 : i_end][tipos.iloc[i_gest + 1 : i_end] == "LINEA"].sum()
        total_gest = float(montos.iloc[i_gest])
        diff = abs(suma_gest - total_gest)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  GESTION GENERAL:  suma lineas = {:.2f}   declarado = {:.2f}   diff = {:.2f}  {}".format(
            suma_gest, total_gest, diff, "OK" if ok else "FAIL"))

    # 3) TOTAL EGRESOS = OPERACIONES + GESTION
    idx_total_eg = tipos == "TOTAL_EGRESOS"
    if idx_total_eg.any() and idx_op.any() and idx_gest.any():
        total_egresos = float(montos.loc[idx_total_eg].iloc[0])
        esperado = total_op + total_gest
        diff = abs(total_egresos - esperado)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  TOTAL EGRESOS:  OPERACIONES + GESTION = {:.2f}   declarado = {:.2f}  {}".format(
            esperado, total_egresos, "OK" if ok else "FAIL"))

    # 4) TOTAL GENERAL = TOTAL EGRESOS + UTILIDAD DEL EJERCICIO
    idx_util = conceptos.str.upper().str.contains("UTILIDAD DEL EJERCICIO")
    idx_total_glob = tipos == "TOTAL_GLOBAL"
    if idx_total_glob.any() and idx_total_eg.any():
        total_general = float(montos.loc[idx_total_glob].iloc[0])
        utilidad = float(montos.loc[idx_util].iloc[0]) if idx_util.any() else 0.0
        esperado = total_egresos + utilidad
        diff = abs(total_general - esperado)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  TOTAL GENERAL:  TOTAL EGRESOS + UTILIDAD = {:.2f}   declarado = {:.2f}  {}".format(
            esperado, total_general, "OK" if ok else "FAIL"))
    print("")

    # 5) Cruce con C40 y 41-A: UTILIDAD C40 = Total Ingresos (41-A) - Total Egresos (41-B)
    if path40.exists() and path41a.exists():
        df40 = pd.read_csv(path40, sep=SEP, encoding=ENCODING)
        df41a = pd.read_csv(path41a, sep=SEP, encoding=ENCODING)
        idx_util_c40 = df40["CONCEPTO"].astype(str).str.upper().str.contains("UTILIDAD DEL EJERCICIO")
        idx_total_ing = df41a["TIPO"] == "TOTAL_INGRESOS"
        if idx_util_c40.any() and idx_total_ing.any() and idx_total_eg.any():
            utilidad_c40 = float(df40.loc[idx_util_c40, "MONTO"].iloc[0])
            total_ingresos = float(df41a.loc[idx_total_ing, "MONTO"].iloc[0])
            total_egresos_41b = float(montos.loc[idx_total_eg].iloc[0])
            utilidad_calc = total_ingresos - total_egresos_41b
            diff = abs(utilidad_calc - utilidad_c40)
            ok = diff <= TOLERANCIA
            if not ok:
                todo_ok = False
            print("  Cruce con C40 y 41-A:  UTILIDAD C40 = {:.2f}   (Ingresos 41-A - Egresos 41-B) = {:.2f}  {}".format(
                utilidad_c40, utilidad_calc, "OK" if ok else "FAIL"))
            if idx_util.any():
                util_41b = float(montos.loc[idx_util].iloc[0])
                if abs(util_41b - utilidad_c40) <= TOLERANCIA:
                    print("  UTILIDAD en 41-B = {:.2f}   UTILIDAD C40 = {:.2f}  OK".format(util_41b, utilidad_c40))
                else:
                    todo_ok = False
                    print("  UTILIDAD en 41-B = {:.2f}   UTILIDAD C40 = {:.2f}  FAIL".format(util_41b, utilidad_c40))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
