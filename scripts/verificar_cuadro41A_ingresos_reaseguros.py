"""
Verifica Cuadro 41-A (Estado de Ganancias y Pérdidas - Ingresos, reaseguros):

1) Lógica interna: subtotales y totales.
   - OPERACIONES TÉCNICAS = suma de líneas "padre" (excl. sublíneas DEL PAÍS, DEL EXTERIOR, NEGOCIOS NACIONALES, NEGOCIOS EXTRANJEROS).
   - GESTIÓN GENERAL = suma de sus líneas (PRODUCTO DE INVERSIONES, AJUSTE DE VALORES, BENEFICIOS DIVERSOS).
   - TOTAL INGRESOS = OPERACIONES TÉCNICAS + GESTIÓN GENERAL.
   - TOTAL GENERAL = TOTAL INGRESOS + PÉRDIDA DEL EJERCICIO.

2) Cruce con Cuadro 40: la UTILIDAD DEL EJERCICIO del balance (C40) debe coincidir con
   Total Ingresos (C41-A) − Total Egresos (C41-B). Si existe el CSV de 41-B, se verifica;
   si no, se informan los valores para referencia.
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
SUBLINEAS = ("DEL PAIS", "DEL EXTERIOR", "NEGOCIOS NACIONALES", "NEGOCIOS EXTRANJEROS")


def _norm(s: str) -> str:
    return s.upper().strip().replace("Á", "A").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("É", "E")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path41a = carpeta / "cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros.csv"
    path40 = carpeta / "cuadro_40_balance_condensado_reaseguros.csv"
    path41b = carpeta / "cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros.csv"
    if not path41a.exists():
        print("[ERROR] No existe {}.".format(path41a))
        return False
    df = pd.read_csv(path41a, sep=SEP, encoding=ENCODING)
    if "TIPO" not in df.columns or "MONTO" not in df.columns:
        print("[ERROR] Cuadro 41-A debe tener columnas CONCEPTO, MONTO, TIPO.")
        return False

    todo_ok = True
    conceptos = df["CONCEPTO"].astype(str).str.strip()
    montos = df["MONTO"].astype(float)
    tipos = df["TIPO"].astype(str).str.strip()

    print("")
    print("  Cuadro 41-A – Estado de Ganancias y Pérdidas. Ingresos (reaseguros)")
    print("")

    # 1) OPERACIONES TÉCNICAS = suma de líneas padre (excl. sublíneas)
    idx_op = (tipos == "SECCION") & (conceptos.str.upper().str.contains("OPERACIONES"))
    idx_gest = (tipos == "SECCION") & (conceptos.str.upper().str.contains("GESTIÓN"))
    if idx_op.any():
        i_op = df.index[idx_op][0]
        i_gest = df.index[idx_gest][0] if idx_gest.any() else len(df)
        suma_op = 0.0
        for j in range(i_op + 1, i_gest):
            if tipos.iloc[j] != "LINEA":
                break
            c = _norm(conceptos.iloc[j])
            if c not in SUBLINEAS:
                suma_op += montos.iloc[j]
        total_op = float(montos.iloc[i_op])
        diff = abs(suma_op - total_op)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  OPERACIONES TÉCNICAS:  suma líneas (padre) = {:.2f}   declarado = {:.2f}   diff = {:.2f}  {}".format(
            suma_op, total_op, diff, "OK" if ok else "FAIL"))
    else:
        print("  [AVISO] No se encontró sección OPERACIONES TÉCNICAS.")

    # 2) GESTIÓN GENERAL = suma de sus líneas
    if idx_gest.any():
        i_gest = df.index[idx_gest][0]
        idx_total_ing = tipos == "TOTAL_INGRESOS"
        i_end = df.index[idx_total_ing][0] if idx_total_ing.any() else len(df)
        suma_gest = montos.iloc[i_gest + 1 : i_end][tipos.iloc[i_gest + 1 : i_end] == "LINEA"].sum()
        total_gest = float(montos.iloc[i_gest])
        diff = abs(suma_gest - total_gest)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  GESTIÓN GENERAL:  suma líneas = {:.2f}   declarado = {:.2f}   diff = {:.2f}  {}".format(
            suma_gest, total_gest, diff, "OK" if ok else "FAIL"))

    # 3) TOTAL INGRESOS = OPERACIONES + GESTIÓN
    idx_total_ing = tipos == "TOTAL_INGRESOS"
    if idx_total_ing.any() and idx_op.any() and idx_gest.any():
        total_ingresos = float(montos.loc[idx_total_ing].iloc[0])
        esperado = total_op + total_gest
        diff = abs(total_ingresos - esperado)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  TOTAL INGRESOS:  OPERACIONES + GESTIÓN = {:.2f}   declarado = {:.2f}  {}".format(
            esperado, total_ingresos, "OK" if ok else "FAIL"))

    # 4) TOTAL GENERAL = TOTAL INGRESOS + PÉRDIDA DEL EJERCICIO
    idx_perdida = conceptos.str.upper().str.contains("PÉRDIDA DEL EJERCICIO") | conceptos.str.upper().str.contains("PERDIDA DEL EJERCICIO")
    idx_total_glob = tipos == "TOTAL_GLOBAL"
    if idx_total_glob.any() and idx_total_ing.any():
        total_general = float(montos.loc[idx_total_glob].iloc[0])
        perdida = float(montos.loc[idx_perdida].iloc[0]) if idx_perdida.any() else 0.0
        esperado = total_ingresos + perdida
        diff = abs(total_general - esperado)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  TOTAL GENERAL:  TOTAL INGRESOS + PÉRDIDA = {:.2f}   declarado = {:.2f}  {}".format(
            esperado, total_general, "OK" if ok else "FAIL"))
    print("")

    # 5) Cruce con Cuadro 40: UTILIDAD C40 ≈ Total Ingresos (41-A) − Total Egresos (41-B)
    if path40.exists():
        df40 = pd.read_csv(path40, sep=SEP, encoding=ENCODING)
        idx_util = df40["CONCEPTO"].astype(str).str.upper().str.contains("UTILIDAD DEL EJERCICIO")
        if idx_util.any() and idx_total_ing.any():
            utilidad_c40 = float(df40.loc[idx_util, "MONTO"].iloc[0])
            total_ingresos_41a = float(montos.loc[idx_total_ing].iloc[0])
            if path41b.exists():
                df41b = pd.read_csv(path41b, sep=SEP, encoding=ENCODING)
                # Buscar TOTAL EGRESOS o equivalente en 41-B
                conc41b = df41b["CONCEPTO"].astype(str).str.upper()
                idx_total_eg = conc41b.str.contains("TOTAL EGRESOS") | conc41b.str.contains("TOTAL GENERAL")
                if idx_total_eg.any():
                    total_egresos_41b = float(df41b.loc[idx_total_eg, "MONTO"].iloc[0])
                    utilidad_calc = total_ingresos_41a - total_egresos_41b
                    diff = abs(utilidad_calc - utilidad_c40)
                    ok = diff <= TOLERANCIA
                    if not ok:
                        todo_ok = False
                    print("  Cruce con C40 y C41-B:  UTILIDAD C40 = {:.2f}   (Ingresos 41-A - Egresos 41-B) = {:.2f}  {}".format(
                        utilidad_c40, utilidad_calc, "OK" if ok else "FAIL"))
                else:
                    print("  Cruce C40:  UTILIDAD C40 = {:.2f}   Total Ingresos 41-A = {:.2f}   (falta 41-B para completar Ingresos - Egresos).".format(
                        utilidad_c40, total_ingresos_41a))
            else:
                print("  Cruce C40:  UTILIDAD C40 = {:.2f}   Total Ingresos 41-A = {:.2f}   (para verificar: Ingresos - Egresos 41-B = Utilidad; 41-B no extraido aun).".format(
                    utilidad_c40, total_ingresos_41a))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
