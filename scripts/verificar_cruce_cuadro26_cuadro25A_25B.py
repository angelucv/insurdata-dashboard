"""
Verifica Cuadro 26 (Gestión general, pág 82) contra Cuadros 25-A y 25-B:

1) PRODUCTO BRUTO TOTAL (C26) = GESTIÓN GENERAL DE LA EMPRESA (25-A ingresos).
2) TOTAL EGRESOS POR LA GESTIÓN GENERAL (C26) = GESTIÓN GENERAL DE LA EMPRESA (25-B egresos).
3) Opcional: PRODUCTO NETO TOTAL (C26) = PRODUCTO BRUTO - TOTAL EGRESOS.
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
    path_26 = carpeta / "cuadro_26_gestion_general.csv"
    path_25a = carpeta / "cuadro_25A_estado_ganancias_perdidas_ingresos.csv"
    path_25b = carpeta / "cuadro_25B_estado_ganancias_perdidas_egresos.csv"
    for p in (path_26, path_25a, path_25b):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df26 = pd.read_csv(path_26, sep=SEP, encoding=ENCODING)
    df25a = pd.read_csv(path_25a, sep=SEP, encoding=ENCODING)
    df25b = pd.read_csv(path_25b, sep=SEP, encoding=ENCODING)

    def _valor_26(concepto_substr: str) -> float | None:
        key = _normalizar(concepto_substr)
        for _, r in df26.iterrows():
            conc = _normalizar(str(r.get("CONCEPTO", r.iloc[0])))
            if key in conc:
                return float(r.get("MONTO", r.iloc[1]))
        return None

    producto_bruto_26 = _valor_26("PRODUCTO BRUTO TOTAL")
    total_egresos_26 = _valor_26("TOTAL EGRESOS")
    producto_neto_26 = _valor_26("PRODUCTO NETO TOTAL")

    gestion_25a = None
    for _, r in df25a.iterrows():
        conc = _normalizar(str(r.get("CONCEPTO", "")))
        if "GESTION GENERAL" in conc and "EMPRESA" in conc:
            gestion_25a = float(r.get("MONTO", 0))
            break
    gestion_25b = None
    for _, r in df25b.iterrows():
        conc = _normalizar(str(r.get("CONCEPTO", "")))
        if "GESTION GENERAL" in conc and "EMPRESA" in conc:
            gestion_25b = float(r.get("MONTO", 0))
            break

    todo_ok = True
    print("")
    print("  Cuadro 26 (Gestión general) vs 25-A (ingresos) y 25-B (egresos)")
    print("")

    if producto_bruto_26 is not None and gestion_25a is not None:
        if abs(producto_bruto_26 - gestion_25a) <= TOLERANCIA:
            print("  OK  PRODUCTO BRUTO TOTAL (C26) = {:,.0f}   GESTIÓN GENERAL (25-A) = {:,.0f}".format(
                producto_bruto_26, gestion_25a))
        else:
            print("  FALLO  PRODUCTO BRUTO (C26) = {:,.0f}   GESTIÓN 25-A = {:,.0f}   diff = {:,.0f}".format(
                producto_bruto_26, gestion_25a, producto_bruto_26 - gestion_25a))
            todo_ok = False
    else:
        print("  ERROR  No se encontró PRODUCTO BRUTO en C26 o GESTIÓN en 25-A.")
        todo_ok = False

    if total_egresos_26 is not None and gestion_25b is not None:
        if abs(total_egresos_26 - gestion_25b) <= TOLERANCIA:
            print("  OK  TOTAL EGRESOS GESTIÓN (C26) = {:,.0f}   GESTIÓN GENERAL (25-B) = {:,.0f}".format(
                total_egresos_26, gestion_25b))
        else:
            print("  FALLO  TOTAL EGRESOS (C26) = {:,.0f}   GESTIÓN 25-B = {:,.0f}   diff = {:,.0f}".format(
                total_egresos_26, gestion_25b, total_egresos_26 - gestion_25b))
            todo_ok = False
    else:
        print("  ERROR  No se encontró TOTAL EGRESOS en C26 o GESTIÓN en 25-B.")
        todo_ok = False

    if producto_bruto_26 is not None and total_egresos_26 is not None and producto_neto_26 is not None:
        esperado_neto = producto_bruto_26 - total_egresos_26
        if abs(producto_neto_26 - esperado_neto) <= TOLERANCIA:
            print("  OK  PRODUCTO NETO (C26) = {:,.0f}   (= {:,.0f} - {:,.0f})".format(
                producto_neto_26, producto_bruto_26, total_egresos_26))
        else:
            print("  FALLO  PRODUCTO NETO (C26) = {:,.0f}   esperado {:,.0f}".format(producto_neto_26, esperado_neto))
            todo_ok = False
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
