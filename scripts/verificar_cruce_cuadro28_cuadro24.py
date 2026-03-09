"""
Verifica Cuadro 28 (Resultados del ejercicio económico 2019-2023 por empresa) contra Cuadro 24 (Balance condensado):

- Para el año 2023, TOTAL BENEFICIO en Cuadro 28 debe coincidir con UTILIDAD DEL EJERCICIO en Cuadro 24.
- Para el año 2023, TOTAL PÉRDIDA en Cuadro 28 (valor absoluto) debe coincidir con PÉRDIDA DEL EJERCICIO en Cuadro 24.
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
    return (
        s.upper()
        .strip()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
    )


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path_28 = carpeta / "cuadro_28_resultados_ejercicio_2019_2023_por_empresa.csv"
    path_24 = carpeta / "cuadro_24_balance_condensado.csv"
    for p in (path_28, path_24):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df28 = pd.read_csv(path_28, sep=SEP, encoding=ENCODING)
    df24 = pd.read_csv(path_24, sep=SEP, encoding=ENCODING)

    # Cuadro 28: TOTAL BENEFICIO y TOTAL PÉRDIDA (columna AÑO_2023)
    col_2023 = [c for c in df28.columns if "2023" in str(c) or "AÑO_2023" in str(c)]
    if not col_2023:
        print("[ERROR] No se encontro columna AÑO_2023 en Cuadro 28.")
        return False
    col_2023 = col_2023[0]
    total_beneficio_28 = None
    total_perdida_28 = None
    for _, r in df28.iterrows():
        nombre = str(r.get("NOMBRE_EMPRESA", r.iloc[0]) or "")
        norm = _normalizar(nombre)
        if "TOTAL BENEFICIO" in norm:
            total_beneficio_28 = float(r.get(col_2023, r[col_2023]))
            break
    for _, r in df28.iterrows():
        nombre = str(r.get("NOMBRE_EMPRESA", r.iloc[0]) or "")
        norm = _normalizar(nombre)
        if "TOTAL" in norm and "PERDIDA" in norm:
            total_perdida_28 = float(r.get(col_2023, r[col_2023]))
            break
    if total_beneficio_28 is None:
        print("[ERROR] No se encontro fila 'TOTAL BENEFICIO' en Cuadro 28.")
        return False
    if total_perdida_28 is None:
        print("[ERROR] No se encontro fila 'TOTAL PÉRDIDA' en Cuadro 28.")
        return False

    # Cuadro 24: UTILIDAD DEL EJERCICIO y PÉRDIDA DEL EJERCICIO
    utilidad_24 = None
    perdida_24 = None
    for _, r in df24.iterrows():
        conc = _normalizar(str(r.get("CONCEPTO", r.iloc[0]) or ""))
        if "UTILIDAD DEL EJERCICIO" in conc:
            utilidad_24 = float(r.get("MONTO", r.iloc[1]))
            break
    for _, r in df24.iterrows():
        conc = _normalizar(str(r.get("CONCEPTO", r.iloc[0]) or ""))
        if "PÉRDIDA DEL EJERCICIO" in conc or "PERDIDA DEL EJERCICIO" in conc:
            perdida_24 = float(r.get("MONTO", r.iloc[1]))
            break
    if utilidad_24 is None:
        print("[ERROR] No se encontro 'UTILIDAD DEL EJERCICIO' en Cuadro 24.")
        return False
    if perdida_24 is None:
        print("[ERROR] No se encontro 'PÉRDIDA DEL EJERCICIO' en Cuadro 24.")
        return False

    todo_ok = True
    print("")
    print("  Cuadro 28 (Resultados ejercicio 2019-2023) vs Cuadro 24 (Balance condensado). Año 2023")
    print("")

    if abs(total_beneficio_28 - utilidad_24) <= TOLERANCIA:
        print(
            "  OK  TOTAL BENEFICIO (C28) = {:,.0f}   UTILIDAD DEL EJERCICIO (C24) = {:,.0f}".format(
                total_beneficio_28, utilidad_24
            )
        )
    else:
        print(
            "  FALLO  TOTAL BENEFICIO (C28) = {:,.0f}   UTILIDAD (C24) = {:,.0f}   diff = {:,.0f}".format(
                total_beneficio_28, utilidad_24, total_beneficio_28 - utilidad_24
            )
        )
        todo_ok = False

    perdida_28_abs = abs(total_perdida_28)
    if abs(perdida_28_abs - perdida_24) <= TOLERANCIA:
        print(
            "  OK  TOTAL PÉRDIDA (C28, valor abs.) = {:,.0f}   PÉRDIDA DEL EJERCICIO (C24) = {:,.0f}".format(
                perdida_28_abs, perdida_24
            )
        )
    else:
        print(
            "  FALLO  TOTAL PÉRDIDA (C28) = {:,.0f}   PÉRDIDA (C24) = {:,.0f}   diff = {:,.0f}".format(
                perdida_28_abs, perdida_24, perdida_28_abs - perdida_24
            )
        )
        todo_ok = False
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
