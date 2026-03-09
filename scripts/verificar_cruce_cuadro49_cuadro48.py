"""
Verifica Cuadro 49 (Ingresos por empresa - financiadoras de primas) vs Cuadro 48
(Estado de Ganancias y Pérdidas - Ingresos y Egresos agregado).

- La fila TOTAL del Cuadro 49 debe tener:
  OPERACIONES_POR_FINANCIAMIENTO = C48 "OPERACIONES DE FINANCIAMIENTO"
  POR_FINANCIAMIENTO = C48 "POR FINANCIAMIENTO"
  AJUSTE_DE_VALORES = C48 "AJUSTE DE VALORES"
  TOTAL (C49) = suma de las tres anteriores = 132.950 (no incluye OTROS INGRESOS de C48).
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
    t = s.upper().strip()
    for a, b in [("\u00c1", "A"), ("\u00c9", "E"), ("\u00cd", "I"), ("\u00d3", "O"), ("\u00da", "U")]:
        t = t.replace(a, b)
    t = t.replace("  ", " ").replace(",", "")
    return t


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path48 = carpeta / "cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas.csv"
    path49 = carpeta / "cuadro_49_ingresos_por_empresa_financiadoras_primas.csv"
    if not path48.exists():
        print("[ERROR] No existe {}.".format(path48))
        return False
    if not path49.exists():
        print("[ERROR] No existe {}.".format(path49))
        return False
    df48 = pd.read_csv(path48, sep=SEP, encoding=ENCODING)
    df49 = pd.read_csv(path49, sep=SEP, encoding=ENCODING)
    # C48: primeras 3 líneas de ingreso son Operaciones de Financiamiento, Por Financiamiento, Ajuste de Valores
    lineas_ingreso = df48[df48["TIPO"] == "LINEA_INGRESO"]
    ref_op = ref_por = ref_ajuste = None
    for _, r in lineas_ingreso.iterrows():
        c = _norm(str(r["CONCEPTO"]).strip())
        m = float(r["MONTO"])
        if ref_op is None and "OPERACIONES" in c and "FINANCIAMIENTO" in c:
            ref_op = m
        elif ref_por is None and "POR FINANCIAMIENTO" in c:
            ref_por = m
        elif ref_ajuste is None and "AJUSTE DE VALORES" in c and "OTROS" not in c:
            ref_ajuste = m
        if ref_op is not None and ref_por is not None and ref_ajuste is not None:
            break
    # C49: fila TOTAL
    total_row = df49[df49["NOMBRE_EMPRESA"].str.upper().str.strip() == "TOTAL"]
    if total_row.empty:
        print("[ERROR] Cuadro 49 no tiene fila TOTAL.")
        return False
    row = total_row.iloc[0]
    op_fin = float(row["OPERACIONES_POR_FINANCIAMIENTO"])
    por_fin = float(row["POR_FINANCIAMIENTO"])
    ajuste = float(row["AJUSTE_DE_VALORES"])
    total49 = float(row["TOTAL"])
    todo_ok = True
    print("")
    print("  Cuadro 49 (Ingresos por empresa - fila TOTAL) vs Cuadro 48 (Ingresos agregados)")
    print("  Operaciones por Financiamiento, Por Financiamiento, Ajuste de Valores, Total")
    print("")
    if ref_op is not None:
        ok = abs(op_fin - ref_op) <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  Operaciones por Financiamiento   C49={:.2f}  C48={:.2f}  diff={:.2f}  {}".format(
            op_fin, ref_op, abs(op_fin - ref_op), "OK" if ok else "FAIL"))
    else:
        print("  Operaciones por Financiamiento   (C48 no encontrado)")
    if ref_por is not None:
        ok = abs(por_fin - ref_por) <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  Por Financiamiento                C49={:.2f}  C48={:.2f}  diff={:.2f}  {}".format(
            por_fin, ref_por, abs(por_fin - ref_por), "OK" if ok else "FAIL"))
    else:
        print("  Por Financiamiento                (C48 no encontrado)")
    if ref_ajuste is not None:
        ok = abs(ajuste - ref_ajuste) <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  Ajuste de Valores                 C49={:.2f}  C48={:.2f}  diff={:.2f}  {}".format(
            ajuste, ref_ajuste, abs(ajuste - ref_ajuste), "OK" if ok else "FAIL"))
    else:
        print("  Ajuste de Valores                 (C48 no encontrado)")
    suma_tres = op_fin + por_fin + ajuste
    ok_total = abs(total49 - suma_tres) <= TOLERANCIA
    if not ok_total:
        todo_ok = False
    print("  Total (suma de las 3 columnas)     C49={:.2f}  esperado={:.2f}  diff={:.2f}  {}".format(
        total49, suma_tres, abs(total49 - suma_tres), "OK" if ok_total else "FAIL"))
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
