"""
Verifica Cuadro 40 (Balance condensado empresas de reaseguro): lógica interna de totales y subtotales.

- Suma de líneas de ACTIVOS (entre ACTIVOS y TOTAL ACTIVO) = TOTAL ACTIVO.
- Suma de líneas de PASIVOS (entre PASIVOS y TOTAL PASIVO) = TOTAL PASIVO.
- Suma de líneas de CAPITAL Y OTROS = TOTAL CAPITAL Y OTROS.
- TOTAL ACTIVO = TOTAL GENERAL (primer total general).
- TOTAL PASIVO + TOTAL CAPITAL Y OTROS + UTILIDAD DEL EJERCICIO = TOTAL GENERAL (ecuación contable).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 50.0  # redondeos en miles


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path40 = carpeta / "cuadro_40_balance_condensado_reaseguros.csv"
    if not path40.exists():
        print("[ERROR] No existe {}.".format(path40))
        return False
    df = pd.read_csv(path40, sep=SEP, encoding=ENCODING)
    if "TIPO" not in df.columns or "MONTO" not in df.columns:
        print("[ERROR] Cuadro 40 debe tener columnas CONCEPTO, MONTO, TIPO.")
        return False

    todo_ok = True
    conceptos = df["CONCEPTO"].astype(str).str.strip()
    montos = df["MONTO"].astype(float)
    tipos = df["TIPO"].astype(str).str.strip()

    # 1) ACTIVOS: sumar LINEA desde después de SECCION "ACTIVOS" hasta TOTAL_ACTIVO
    idx_activos = (tipos == "SECCION") & (conceptos.str.upper() == "ACTIVOS")
    idx_total_activo = tipos == "TOTAL_ACTIVO"
    if idx_total_activo.any():
        i_start = idx_activos.idxmax() if idx_activos.any() else 0
        i_end = df.index[idx_total_activo][0]
        suma_activos = montos.iloc[i_start + 1 : i_end][tipos.iloc[i_start + 1 : i_end] == "LINEA"].sum()
        total_activo = float(montos.loc[idx_total_activo].iloc[0])
        diff = abs(suma_activos - total_activo)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("")
        print("  Cuadro 40 – Balance condensado reaseguros (totales y subtotales)")
        print("")
        print("  ACTIVOS:  suma líneas = {:.2f}   TOTAL ACTIVO = {:.2f}   diff = {:.2f}  {}".format(
            suma_activos, total_activo, diff, "OK" if ok else "FAIL"
        ))
    else:
        print("[ERROR] No se encontró TOTAL ACTIVO en Cuadro 40.")
        todo_ok = False

    # 2) PASIVOS: sumar LINEA entre PASIVOS y TOTAL_PASIVO
    idx_pasivos = (tipos == "SECCION") & (conceptos.str.upper() == "PASIVOS")
    idx_total_pasivo = tipos == "TOTAL_PASIVO"
    if idx_total_pasivo.any():
        i_start = df.index[idx_pasivos][0] if idx_pasivos.any() else 0
        i_end = df.index[idx_total_pasivo][0]
        suma_pasivos = montos.iloc[i_start + 1 : i_end][tipos.iloc[i_start + 1 : i_end] == "LINEA"].sum()
        total_pasivo = float(montos.loc[idx_total_pasivo].iloc[0])
        diff = abs(suma_pasivos - total_pasivo)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  PASIVOS:  suma líneas = {:.2f}   TOTAL PASIVO = {:.2f}   diff = {:.2f}  {}".format(
            suma_pasivos, total_pasivo, diff, "OK" if ok else "FAIL"
        ))

    # 3) CAPITAL Y OTROS: sumar LINEA entre CAPITAL Y OTROS y TOTAL_CAPITAL
    idx_capital_sec = (tipos == "SECCION") & (conceptos.str.upper().str.contains("CAPITAL Y OTROS"))
    idx_total_capital = tipos == "TOTAL_CAPITAL"
    if idx_total_capital.any():
        i_start = df.index[idx_capital_sec][0] if idx_capital_sec.any() else 0
        i_end = df.index[idx_total_capital][0]
        suma_capital = montos.iloc[i_start + 1 : i_end][tipos.iloc[i_start + 1 : i_end] == "LINEA"].sum()
        total_capital = float(montos.loc[idx_total_capital].iloc[0])
        diff = abs(suma_capital - total_capital)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  CAPITAL Y OTROS:  suma líneas = {:.2f}   TOTAL CAPITAL Y OTROS = {:.2f}   diff = {:.2f}  {}".format(
            suma_capital, total_capital, diff, "OK" if ok else "FAIL"
        ))

    # 4) TOTAL ACTIVO = TOTAL GENERAL (primer TOTAL_GLOBAL)
    idx_total_global = tipos == "TOTAL_GLOBAL"
    if idx_total_activo.any() and idx_total_global.any():
        total_general_1 = float(montos.loc[idx_total_global].iloc[0])
        if abs(total_activo - total_general_1) > TOLERANCIA:
            todo_ok = False
            print("  TOTAL ACTIVO vs TOTAL GENERAL (1): {} vs {}  FAIL".format(total_activo, total_general_1))
        else:
            print("  TOTAL ACTIVO = TOTAL GENERAL (1): {:.2f}  OK".format(total_activo))

    # 5) TOTAL PASIVO + TOTAL CAPITAL + UTILIDAD DEL EJERCICIO = TOTAL GENERAL
    idx_utilidad = conceptos.str.upper().str.contains("UTILIDAD DEL EJERCICIO")
    if idx_total_pasivo.any() and idx_total_capital.any() and idx_utilidad.any():
        utilidad = float(montos.loc[idx_utilidad].iloc[0])
        suma_ecuacion = total_pasivo + total_capital + utilidad
        total_general_2 = float(montos.loc[idx_total_global].iloc[-1]) if len(montos.loc[idx_total_global]) >= 2 else total_general_1
        diff = abs(suma_ecuacion - total_general_2)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  Ecuación: TOTAL PASIVO + TOTAL CAPITAL + UTILIDAD = {:.2f} + {:.2f} + {:.2f} = {:.2f}   TOTAL GENERAL = {:.2f}  {}".format(
            total_pasivo, total_capital, utilidad, suma_ecuacion, total_general_2, "OK" if ok else "FAIL"
        ))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
