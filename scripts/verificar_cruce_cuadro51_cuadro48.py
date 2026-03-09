"""
Verifica Cuadro 51 (Gastos operativos, administrativos y financieros por empresa - financiadoras de primas)
vs Cuadro 48 (Estado de Ganancias y Pérdidas - Egresos).

Los totales del Cuadro 51 (fila TOTAL o suma por columna) deben coincidir con:
- GASTOS_OPERATIVOS (C51) = GASTOS OPERACIONALES (C48)
- GASTOS_ADMINISTRATIVOS (C51) = GASTOS DE ADMINISTRACIÓN (C48)
- GASTOS_FINANCIEROS (C51) = GASTOS FINANCIEROS (C48)
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
    for a, b in [("\u00c1", "A"), ("\u00c9", "E"), ("\u00cd", "I"), ("\u00d3", "O"), ("\u00da", "U"), ("\u00d1", "N")]:
        t = t.replace(a, b)
    t = t.replace("  ", " ").replace(",", "")
    return t


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path48 = carpeta / "cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas.csv"
    path51 = carpeta / "cuadro_51_gastos_operativos_administrativos_financieros_por_empresa_financiadoras_primas.csv"
    if not path48.exists():
        print("[ERROR] No existe {}.".format(path48))
        return False
    if not path51.exists():
        print("[ERROR] No existe {}.".format(path51))
        return False
    df48 = pd.read_csv(path48, sep=SEP, encoding=ENCODING)
    df51 = pd.read_csv(path51, sep=SEP, encoding=ENCODING)
    # C48: obtener GASTOS OPERACIONALES, GASTOS DE ADMINISTRACIÓN, GASTOS FINANCIEROS (egresos)
    ref_operativos = ref_administrativos = ref_financieros = None
    for _, r in df48.iterrows():
        c = _norm(str(r["CONCEPTO"]).strip())
        m = float(r["MONTO"])
        if "GASTOS OPERACIONALES" in c or (c == "GASTOS OPERACIONALES"):
            ref_operativos = m
        elif "GASTOS DE ADMINISTRACION" in c or "GASTOS DE ADMINISTRACI" in c:
            ref_administrativos = m
        elif "GASTOS FINANCIEROS" in c and "ADMINISTRATIVOS" not in c:
            ref_financieros = m
        if ref_operativos is not None and ref_administrativos is not None and ref_financieros is not None:
            break
    # C51: fila TOTAL o suma por columna
    total_row = df51[df51["NOMBRE_EMPRESA"].str.upper().str.strip() == "TOTAL"]
    if not total_row.empty:
        tot_op = float(total_row.iloc[0]["GASTOS_OPERATIVOS"])
        tot_adm = float(total_row.iloc[0]["GASTOS_ADMINISTRATIVOS"])
        tot_fin = float(total_row.iloc[0]["GASTOS_FINANCIEROS"])
    else:
        tot_op = df51["GASTOS_OPERATIVOS"].sum()
        tot_adm = df51["GASTOS_ADMINISTRATIVOS"].sum()
        tot_fin = df51["GASTOS_FINANCIEROS"].sum()
    todo_ok = True
    print("")
    print("  Cuadro 51 (Gastos por empresa - fila TOTAL) vs Cuadro 48 (Egresos)")
    print("  Gastos Operativos/Operacionales, Administrativos/Administración, Financieros")
    print("")
    for label, val51, ref, name_ref in [
        ("Gastos Operativos (C51) vs GASTOS OPERACIONALES (C48)", tot_op, ref_operativos, "GASTOS OPERACIONALES"),
        ("Gastos Administrativos (C51) vs GASTOS DE ADMINISTRACIÓN (C48)", tot_adm, ref_administrativos, "GASTOS DE ADMINISTRACIÓN"),
        ("Gastos Financieros (C51) vs GASTOS FINANCIEROS (C48)", tot_fin, ref_financieros, "GASTOS FINANCIEROS"),
    ]:
        if ref is None:
            print("  {}  C51={:.2f}  C48 {} no encontrado".format(label[:55].ljust(56), val51, name_ref))
            todo_ok = False
            continue
        diff = abs(val51 - ref)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  {}  C51={:.2f}  C48={:.2f}  diff={:.2f}  {}".format(
            label[:50].ljust(51), val51, ref, diff, "OK" if ok else "FAIL"))
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
