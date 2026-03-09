"""
Verifica Cuadro 43-A (Ingresos por empresas) vs Cuadro 41-A (Ingresos agregados)
y Cuadro 43-B (Egresos por empresas) vs Cuadro 41-B (Egresos agregados).

Para cada concepto: suma de las 4 columnas MONTO (RIV + KAIROS + PROVINCIAL + DELTA)
en 43-A debe coincidir con el MONTO del mismo concepto en 41-A. Igual para 43-B vs 41-B.
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
MONTOS_43 = ["RIV_MONTO", "KAIROS_MONTO", "PROVINCIAL_MONTO", "DELTA_MONTO"]


def _norm(s: str) -> str:
    t = s.upper().strip()
    for a, b in [("\u00c1", "A"), ("\u00c9", "E"), ("\u00cd", "I"), ("\u00d3", "O"), ("\u00da", "U")]:
        t = t.replace(a, b)
    t = t.replace("  ", " ").replace(",", "")
    return t


def _verificar_cruce(c43_path: Path, c41_path: Path, etiqueta: str) -> bool:
    import pandas as pd
    if not c43_path.exists():
        print("[ERROR] No existe {}.".format(c43_path))
        return False
    if not c41_path.exists():
        print("[ERROR] No existe {}.".format(c41_path))
        return False
    df43 = pd.read_csv(c43_path, sep=SEP, encoding=ENCODING)
    df41 = pd.read_csv(c41_path, sep=SEP, encoding=ENCODING)
    # 43-A y 41-A tienen mismo número de filas y orden; 43-B puede tener menos filas que 41-B
    list41 = [(_norm(str(r["CONCEPTO"]).strip()), float(r["MONTO"])) for _, r in df41.iterrows()]
    idx41 = 0
    todo_ok = True
    print("")
    print("  {} (por empresa) vs {} (agregado)".format(etiqueta, etiqueta.replace("43-A", "41-A").replace("43-B", "41-B")))
    print("  Suma RIV_MONTO + KAIROS_MONTO + PROVINCIAL_MONTO + DELTA_MONTO = MONTO agregado por concepto")
    print("")
    for _, row in df43.iterrows():
        conc = str(row["CONCEPTO"]).strip()
        suma = sum(float(row[c]) for c in MONTOS_43)
        n = _norm(conc)
        ref = None
        for j in range(idx41, len(list41)):
            n41, m41 = list41[j]
            if n == n41:
                ref = m41
                idx41 = j + 1
                break
            if n in n41 or n41 in n:
                if len(n) > 8 and len(n41) > 8:
                    ref = m41
                    idx41 = j + 1
                    break
        if ref is None:
            continue
        diff = abs(suma - ref)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  {}  suma={:.2f}  ref={:.2f}  diff={:.2f}  {}".format(
            conc[:50].ljust(51), suma, ref, diff, "OK" if ok else "FAIL"))
    print("")
    return todo_ok


def run_verificacion(anio: int = 2023) -> bool:
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path43a = carpeta / "cuadro_43A_estado_ganancias_perdidas_ingresos_por_empresa_reaseguros.csv"
    path43b = carpeta / "cuadro_43B_estado_ganancias_perdidas_egresos_por_empresa_reaseguros.csv"
    path41a = carpeta / "cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros.csv"
    path41b = carpeta / "cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros.csv"
    ok_a = _verificar_cruce(path43a, path41a, "43-A / 41-A")
    ok_b = _verificar_cruce(path43b, path41b, "43-B / 41-B")
    return ok_a and ok_b


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
