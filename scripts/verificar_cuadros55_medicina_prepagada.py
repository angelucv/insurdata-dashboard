"""
Verifica Cuadro 55-A (Estado de Ganancias y Pérdidas - Ingresos medicina prepagada) y
Cuadro 55-B (Egresos medicina prepagada): consistencias internas y entre tablas.

Internas 55-A:
- Suma de líneas (LINEA) bajo cada SECCION = monto de la SECCION.
- Suma de secciones = TOTAL INGRESOS.
- TOTAL INGRESOS + PÉRDIDA (Resultado del ejercicio) = TOTAL GENERAL.

Internas 55-B:
- Suma de líneas bajo cada SECCION = monto de la SECCION.
- Suma de secciones = TOTAL EGRESOS.
- TOTAL EGRESOS + UTILIDAD (Resultado del ejercicio) = TOTAL GENERAL.

Entre tablas:
- TOTAL GENERAL (55-A) = TOTAL GENERAL (55-B).
- TOTAL INGRESOS - TOTAL EGRESOS = UTILIDAD - PÉRDIDA (identidad contable).
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


def _verificar_interno_55(df, etiqueta: str, total_tipo: str, resultado_nombre: str) -> bool:
    """Verifica consistencia interna: suma LINEA por SECCION = SECCION; suma secciones = total; total + resultado = TOTAL_GLOBAL."""
    import pandas as pd
    if "TIPO" not in df.columns or "MONTO" not in df.columns:
        print("[ERROR] Falta columna TIPO o MONTO en {}.".format(etiqueta))
        return False
    tipos = df["TIPO"].astype(str).str.strip()
    montos = df["MONTO"].astype(float)
    todo_ok = True
    idx_total = tipos == total_tipo
    idx_global = tipos == "TOTAL_GLOBAL"
    if not idx_total.any() or not idx_global.any():
        print("[ERROR] No se encontró {} o TOTAL_GLOBAL en {}.".format(total_tipo, etiqueta))
        return False
    total_val = float(montos.loc[idx_total].iloc[0])
    total_global = float(montos.loc[idx_global].iloc[0])
    # Sumar por secciones: entre cada SECCION y la siguiente SECCION o total_tipo, sumar LINEA
    i = 0
    suma_secciones = 0.0
    while i < len(df):
        if tipos.iloc[i] == "SECCION":
            monto_sec = float(montos.iloc[i])
            j = i + 1
            suma_lineas = 0.0
            while j < len(df) and tipos.iloc[j] == "LINEA":
                suma_lineas += float(montos.iloc[j])
                j += 1
            diff = abs(suma_lineas - monto_sec)
            ok = diff <= TOLERANCIA
            if not ok:
                todo_ok = False
            conc = str(df.iloc[i]["CONCEPTO"])[:45]
            print("  {}  sección '{}'  suma líneas = {:.2f}   monto = {:.2f}   diff = {:.2f}  {}".format(
                etiqueta, conc, suma_lineas, monto_sec, diff, "OK" if ok else "FAIL"))
            suma_secciones += monto_sec
            i = j
            continue
        if tipos.iloc[i] == total_tipo:
            diff = abs(suma_secciones - total_val)
            ok = diff <= TOLERANCIA
            if not ok:
                todo_ok = False
            print("  {}  suma secciones = {:.2f}   {} = {:.2f}   diff = {:.2f}  {}".format(
                etiqueta, suma_secciones, total_tipo, total_val, diff, "OK" if ok else "FAIL"))
            break
        i += 1
    # Resultado del ejercicio (PÉRDIDA o UTILIDAD)
    idx_res = df["CONCEPTO"].astype(str).str.upper().str.contains("RESULTADO DEL EJERCICIO")
    if idx_res.any():
        resultado = float(montos.loc[idx_res].iloc[0])
        esperado_global = total_val + resultado
        diff = abs(esperado_global - total_global)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  {}  {} + {} = {:.2f}   TOTAL GENERAL = {:.2f}   diff = {:.2f}  {}".format(
            etiqueta, total_tipo, resultado_nombre, esperado_global, total_global, diff, "OK" if ok else "FAIL"))
    return todo_ok


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path55a = carpeta / "cuadro_55A_estado_ganancias_perdidas_ingresos_medicina_prepagada.csv"
    path55b = carpeta / "cuadro_55B_estado_ganancias_perdidas_egresos_medicina_prepagada.csv"
    if not path55a.exists():
        print("[ERROR] No existe {}.".format(path55a))
        return False
    if not path55b.exists():
        print("[ERROR] No existe {}.".format(path55b))
        return False
    df55a = pd.read_csv(path55a, sep=SEP, encoding=ENCODING)
    df55b = pd.read_csv(path55b, sep=SEP, encoding=ENCODING)
    todo_ok = True
    print("")
    print("  Cuadros 55-A y 55-B – Medicina prepagada (consistencias internas y entre tablas)")
    print("")
    todo_ok &= _verificar_interno_55(df55a, "55-A", "TOTAL_INGRESOS", "PÉRDIDA")
    print("")
    todo_ok &= _verificar_interno_55(df55b, "55-B", "TOTAL_EGRESOS", "UTILIDAD")
    print("")
    # Entre tablas
    tipos_a = df55a["TIPO"].astype(str).str.strip()
    tipos_b = df55b["TIPO"].astype(str).str.strip()
    tg_a = float(df55a.loc[tipos_a == "TOTAL_GLOBAL", "MONTO"].iloc[0])
    tg_b = float(df55b.loc[tipos_b == "TOTAL_GLOBAL", "MONTO"].iloc[0])
    diff_tg = abs(tg_a - tg_b)
    ok = diff_tg <= TOLERANCIA
    if not ok:
        todo_ok = False
    print("  CRUCE  TOTAL GENERAL (55-A) = TOTAL GENERAL (55-B):  {:.2f} = {:.2f}   diff = {:.2f}  {}".format(
        tg_a, tg_b, diff_tg, "OK" if ok else "FAIL"))
    ti = float(df55a.loc[tipos_a == "TOTAL_INGRESOS", "MONTO"].iloc[0])
    te = float(df55b.loc[tipos_b == "TOTAL_EGRESOS", "MONTO"].iloc[0])
    idx_perdida = df55a["CONCEPTO"].astype(str).str.upper().str.contains("RESULTADO DEL EJERCICIO")
    idx_utilidad = df55b["CONCEPTO"].astype(str).str.upper().str.contains("RESULTADO DEL EJERCICIO")
    perdida = float(df55a.loc[idx_perdida, "MONTO"].iloc[0])
    utilidad = float(df55b.loc[idx_utilidad, "MONTO"].iloc[0])
    # Identidad: Ingresos - Egresos = Utilidad - Pérdida  (o sea -Pérdida + Utilidad)
    izquierda = ti - te
    derecha = utilidad - perdida
    diff_id = abs(izquierda - derecha)
    ok = diff_id <= TOLERANCIA
    if not ok:
        todo_ok = False
    print("  CRUCE  TOTAL INGRESOS - TOTAL EGRESOS = UTILIDAD - PÉRDIDA:  {:.2f} - {:.2f} = {:.2f} - {:.2f}  ->  {:.2f} = {:.2f}   diff = {:.2f}  {}".format(
        ti, te, utilidad, perdida, izquierda, derecha, diff_id, "OK" if ok else "FAIL"))
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
