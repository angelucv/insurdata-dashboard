"""
Verifica Cuadro 27 (Rentabilidad de las inversiones por empresa) contra Cuadro 26 (Gestión general):

- La suma de la columna "Producto de Inversiones" (I) en Cuadro 27 (todas las empresas, sin fila TOTAL)
  debe coincidir con "A.PRODUCTO DE INVERSIONES" en Cuadro 26.

- Opcionalmente: la fila TOTAL del Cuadro 27 (col. Producto de Inversiones) debe ser igual al mismo valor.
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


def _normalizar(s: str) -> str:
    return s.upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path_27 = carpeta / "cuadro_27_rentabilidad_inversiones_por_empresa.csv"
    path_26 = carpeta / "cuadro_26_gestion_general.csv"
    for p in (path_27, path_26):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df27 = pd.read_csv(path_27, sep=SEP, encoding=ENCODING)
    df26 = pd.read_csv(path_26, sep=SEP, encoding=ENCODING)

    producto_c26 = None
    for _, r in df26.iterrows():
        conc = _normalizar(str(r.get("CONCEPTO", r.iloc[0])))
        if "PRODUCTO DE INVERSIONES" in conc or "PRODUCTO DE INVERSIONES" in conc.replace("Ó", "O"):
            producto_c26 = float(r.get("MONTO", r.iloc[1]))
            break
    if producto_c26 is None:
        print("[ERROR] No se encontro 'A.PRODUCTO DE INVERSIONES' en Cuadro 26.")
        return False

    df27_sin_total = df27[df27["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"]
    suma_producto_27 = df27_sin_total["PRODUCTO_INVERSIONES"].sum()
    fila_total_27 = df27[df27["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL"]
    total_producto_27 = float(fila_total_27["PRODUCTO_INVERSIONES"].iloc[0]) if len(fila_total_27) > 0 else None

    todo_ok = True
    print("")
    print("  Cuadro 27 (Rentabilidad inversiones por empresa) vs Cuadro 26 (Producto de Inversiones)")
    print("")

    if abs(suma_producto_27 - producto_c26) <= TOLERANCIA:
        print("  OK  Suma Producto de Inversiones (C27, empresas) = {:,.0f}   C26 A.PRODUCTO DE INVERSIONES = {:,.0f}".format(
            suma_producto_27, producto_c26))
    else:
        print("  FALLO  Suma Producto Inversiones (C27) = {:,.0f}   C26 = {:,.0f}   diff = {:,.0f}".format(
            suma_producto_27, producto_c26, suma_producto_27 - producto_c26))
        todo_ok = False

    if total_producto_27 is not None:
        if abs(total_producto_27 - producto_c26) <= TOLERANCIA:
            print("  OK  Fila TOTAL C27 (Producto Inversiones) = {:,.0f}   C26 = {:,.0f}".format(total_producto_27, producto_c26))
        else:
            print("  FALLO  Fila TOTAL C27 = {:,.0f}   C26 = {:,.0f}".format(total_producto_27, producto_c26))
            todo_ok = False
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
