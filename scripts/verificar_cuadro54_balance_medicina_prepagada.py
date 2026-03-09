"""
Verifica Cuadro 54 (Balance condensado empresas de medicina prepagada): consistencia interna de totales y subtotales.

- Suma de líneas de ACTIVO (entre ACTIVO y TOTAL ACTIVO) = TOTAL ACTIVO.
- TOTAL ACTIVO + PÉRDIDAS DEL EJERCICIO + PÉRDIDAS ANTERIORES + SALDO = primer TOTAL GENERAL.
- Suma de líneas de PASIVO (entre PASIVO y TOTAL PASIVO) = TOTAL PASIVO.
- Suma de líneas de PATRIMONIO (entre PATRIMONIO y TOTAL PATRIMONIO) = TOTAL PATRIMONIO.
- Los dos TOTAL GENERAL deben coincidir (cuadre del balance).
- TOTAL PASIVO + TOTAL PATRIMONIO + SUPERÁVIT NO REALIZADO + UTILIDAD DEL EJERCICIO = TOTAL GENERAL.
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


def _norm(s: str) -> str:
    return s.upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path54 = carpeta / "cuadro_54_balance_condensado_medicina_prepagada.csv"
    if not path54.exists():
        print("[ERROR] No existe {}.".format(path54))
        return False
    df = pd.read_csv(path54, sep=SEP, encoding=ENCODING)
    if "TIPO" not in df.columns or "MONTO" not in df.columns:
        print("[ERROR] Cuadro 54 debe tener columnas CONCEPTO, MONTO, TIPO.")
        return False

    todo_ok = True
    conceptos = df["CONCEPTO"].astype(str).str.strip()
    montos = df["MONTO"].astype(float)
    tipos = df["TIPO"].astype(str).str.strip()

    # 1) ACTIVO: suma LINEA entre SECCION ACTIVO y TOTAL_ACTIVO
    idx_activo = (tipos == "SECCION") & (conceptos.str.upper() == "ACTIVO")
    idx_total_activo = tipos == "TOTAL_ACTIVO"
    if idx_total_activo.any():
        i_start = df.index[idx_activo][0] if idx_activo.any() else 0
        i_end = df.index[idx_total_activo][0]
        bloque = df.iloc[i_start + 1 : i_end]
        suma_activo = bloque[bloque["TIPO"] == "LINEA"]["MONTO"].sum()
        total_activo = float(montos.loc[idx_total_activo].iloc[0])
        diff = abs(suma_activo - total_activo)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("")
        print("  Cuadro 54 – Balance condensado medicina prepagada (totales y subtotales)")
        print("")
        print("  ACTIVO:  suma líneas = {:.2f}   TOTAL ACTIVO = {:.2f}   diff = {:.2f}  {}".format(
            suma_activo, total_activo, diff, "OK" if ok else "FAIL"
        ))
    else:
        print("[ERROR] No se encontró TOTAL ACTIVO.")
        todo_ok = False

    # 2) Primer TOTAL GENERAL = TOTAL ACTIVO + PÉRDIDAS + SALDO (líneas entre TOTAL_ACTIVO y primer TOTAL_GLOBAL)
    idx_total_global = tipos == "TOTAL_GLOBAL"
    if idx_total_activo.any() and idx_total_global.any():
        i_ta = df.index[idx_total_activo][0]
        i_tg1 = df.index[idx_total_global][0]
        bloque_perdidas = df.iloc[i_ta + 1 : i_tg1]
        suma_perdidas = bloque_perdidas[bloque_perdidas["TIPO"] == "LINEA"]["MONTO"].sum()
        total_general_1 = float(montos.loc[idx_total_global].iloc[0])
        esperado = total_activo + suma_perdidas
        diff = abs(esperado - total_general_1)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  TOTAL ACTIVO + Pérdidas/Saldo = TOTAL GENERAL (1): {:.2f} + {:.2f} = {:.2f}   ref = {:.2f}   diff = {:.2f}  {}".format(
            total_activo, suma_perdidas, esperado, total_general_1, diff, "OK" if ok else "FAIL"
        ))

    # 3) PASIVO: suma LINEA entre PASIVO y TOTAL_PASIVO
    idx_pasivo = (tipos == "SECCION") & (conceptos.str.upper() == "PASIVO")
    idx_total_pasivo = tipos == "TOTAL_PASIVO"
    if idx_total_pasivo.any():
        i_start = df.index[idx_pasivo][0] if idx_pasivo.any() else 0
        i_end = df.index[idx_total_pasivo][0]
        bloque = df.iloc[i_start + 1 : i_end]
        suma_pasivo = bloque[bloque["TIPO"] == "LINEA"]["MONTO"].sum()
        total_pasivo = float(montos.loc[idx_total_pasivo].iloc[0])
        diff = abs(suma_pasivo - total_pasivo)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  PASIVO:  suma líneas = {:.2f}   TOTAL PASIVO = {:.2f}   diff = {:.2f}  {}".format(
            suma_pasivo, total_pasivo, diff, "OK" if ok else "FAIL"
        ))

    # 4) PATRIMONIO: suma LINEA entre PATRIMONIO y TOTAL_PATRIMONIO
    idx_patrimonio = (tipos == "SECCION") & (conceptos.str.upper() == "PATRIMONIO")
    idx_total_patrimonio = tipos == "TOTAL_PATRIMONIO"
    if idx_total_patrimonio.any():
        i_start = df.index[idx_patrimonio][0] if idx_patrimonio.any() else 0
        i_end = df.index[idx_total_patrimonio][0]
        bloque = df.iloc[i_start + 1 : i_end]
        suma_patrimonio = bloque[bloque["TIPO"] == "LINEA"]["MONTO"].sum()
        total_patrimonio = float(montos.loc[idx_total_patrimonio].iloc[0])
        diff = abs(suma_patrimonio - total_patrimonio)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  PATRIMONIO:  suma líneas = {:.2f}   TOTAL PATRIMONIO = {:.2f}   diff = {:.2f}  {}".format(
            suma_patrimonio, total_patrimonio, diff, "OK" if ok else "FAIL"
        ))

    # 5) Los dos TOTAL GENERAL deben ser iguales
    if idx_total_global.sum() >= 2:
        tg1 = float(montos.loc[idx_total_global].iloc[0])
        tg2 = float(montos.loc[idx_total_global].iloc[1])
        ok = abs(tg1 - tg2) <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  TOTAL GENERAL (1) = TOTAL GENERAL (2): {:.2f} = {:.2f}   diff = {:.2f}  {}".format(
            tg1, tg2, abs(tg1 - tg2), "OK" if ok else "FAIL"
        ))

    # 6) TOTAL PASIVO + TOTAL PATRIMONIO + SUPERÁVIT NO REALIZADO + UTILIDAD = TOTAL GENERAL
    idx_superavit = conceptos.str.upper().str.contains("SUPERAVIT NO REALIZADO") | conceptos.str.upper().str.contains("SUPERÁVIT NO REALIZADO")
    idx_utilidad = conceptos.str.upper().str.contains("UTILIDAD DEL EJERCICIO")
    if idx_total_pasivo.any() and idx_total_patrimonio.any() and idx_utilidad.any():
        superavit = float(montos.loc[idx_superavit].iloc[0]) if idx_superavit.any() else 0.0
        utilidad = float(montos.loc[idx_utilidad].iloc[0])
        total_general_2 = float(montos.loc[idx_total_global].iloc[1]) if idx_total_global.sum() >= 2 else total_general_1
        esperado = total_pasivo + total_patrimonio + superavit + utilidad
        diff = abs(esperado - total_general_2)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  TOTAL PASIVO + PATRIMONIO + SUPERÁVIT NO REAL. + UTILIDAD = TOTAL GENERAL: {:.2f} + {:.2f} + {:.2f} + {:.2f} = {:.2f}   ref = {:.2f}   diff = {:.2f}  {}".format(
            total_pasivo, total_patrimonio, superavit, utilidad, esperado, total_general_2, diff, "OK" if ok else "FAIL"
        ))

    print("")
    return todo_ok


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
