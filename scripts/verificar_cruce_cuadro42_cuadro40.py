"""
Verifica Cuadro 42 (Balance condensado por empresa - reaseguros) contra Cuadro 40 (Balance condensado):

Para cada concepto del Cuadro 42, la suma de las 4 columnas (RIV + KAIROS + PROVINCIAL + DELTA)
debe coincidir con el MONTO del concepto correspondiente en el Cuadro 40.
Se hace correspondencia por nombre de concepto (normalizado) entre C42 y C40.
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
    t = t.replace("\u00c7", "C").replace("\u00e7", "C")  # C cedilla (typo en PDF)
    t = t.replace("  ", " ")
    if t == "TOTAL ACTIVOS":
        t = "TOTAL ACTIVO"
    if t == "CUENTA DE ORDEN":
        t = "CUENTAS DE ORDEN"
    return t


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path42 = carpeta / "cuadro_42_balance_condensado_por_empresa_reaseguros.csv"
    path40 = carpeta / "cuadro_40_balance_condensado_reaseguros.csv"
    if not path42.exists():
        print("[ERROR] No existe {}.".format(path42))
        return False
    if not path40.exists():
        print("[ERROR] No existe {}.".format(path40))
        return False
    df42 = pd.read_csv(path42, sep=SEP, encoding=ENCODING)
    df40 = pd.read_csv(path40, sep=SEP, encoding=ENCODING)

    # Mapa concepto normalizado -> MONTO en C40
    map40 = {}
    for _, row in df40.iterrows():
        conc = str(row["CONCEPTO"]).strip()
        monto = float(row["MONTO"])
        n = _norm(conc)
        if n:
            map40[n] = monto

    todo_ok = True
    print("")
    print("  Cuadro 42 (Balance por empresa) vs Cuadro 40 (Balance condensado)")
    print("  Suma RIV + KAIROS + PROVINCIAL + DELTA = MONTO C40 por concepto")
    print("")
    cols = ["RIV", "KAIROS", "PROVINCIAL", "DELTA"]
    for _, row in df42.iterrows():
        conc = str(row["CONCEPTO"]).strip()
        suma = sum(float(row[c]) for c in cols)
        n = _norm(conc)
        ref = map40.get(n)
        if ref is None:
            # Buscar clave que coincida (ej. PREVISION vs PREVISIÓN)
            for k in map40:
                k_norm = _norm(k)
                if k_norm == n or (n in k_norm and len(n) > 15):
                    ref = map40[k]
                    break
        if ref is None:
            if "INVERSIONES NO APTAS" in n and ("REPRESENTACION" in n or "REPRESENTACI" in n):
                for k in map40:
                    if "INVERSIONES NO APTAS" in k and "REPRESENTACION" in k:
                        ref = map40[k]
                        break
            if ref is None and "TOTAL PASIVO Y CAPITAL" in n:
                ref = map40.get("TOTAL GENERAL")
            elif ref is None and "TOTAL ACTIVO" in n:
                ref = map40.get("TOTAL ACTIVO")
            elif ref is None and ("CUENTAS DE ORDEN" in n or "CUENTA DE ORDEN" in n):
                ref = map40.get("CUENTAS DE ORDEN")
            elif ref is None and "PREVISION" in n:
                for k in map40:
                    if "PREVIS" in k.upper():
                        ref = map40[k]
                        break
            elif ref is None and ("SUPERAVIT" in n or "SUPERÁVIT" in n):
                for k in map40:
                    if "SUPER" in k.upper() and "AVIT" in k.upper():
                        ref = map40[k]
                        break
        if ref is None:
            print("  [AVISO] Sin concepto en C40: {}".format(conc[:50]))
            continue
        diff = abs(suma - ref)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  {}  suma={:.2f}  C40={:.2f}  diff={:.2f}  {}".format(
            conc[:55].ljust(56), suma, ref, diff, "OK" if ok else "FAIL"))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
