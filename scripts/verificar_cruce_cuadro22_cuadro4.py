"""
Verifica Cuadro 22 (gastos de administración vs primas netas por empresa) contra Cuadro 4:
- La columna PRIMAS_NETAS del Cuadro 22 debe coincidir con la columna TOTAL del Cuadro 4 para cada empresa.
- Cuadro 4 tiene una fila por empresa con TOTAL = suma de ramos; ese mismo valor es Primas Netas en Cuadro 22.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 500.0  # diferencias de redondeo o pequeñas discrepancias documentales (ej. C22 vs C4)


def _normalizar(s: str) -> str:
    return s.upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path4 = carpeta / "cuadro_04_primas_por_ramo_empresa.csv"
    path22 = carpeta / "cuadro_22_gastos_admin_vs_primas_por_empresa.csv"
    for p in (path4, path22):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df4 = pd.read_csv(path4, sep=SEP, encoding=ENCODING)
    df22 = pd.read_csv(path22, sep=SEP, encoding=ENCODING)

    # Cuadro 4: columna "Nombre Empresa" y "TOTAL"
    nom4 = df4.iloc[:, 0].astype(str).str.strip()
    total4 = df4["TOTAL"]

    # Cuadro 22: excluir fila TOTAL
    df22_emp = df22[df22["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"]
    nom22 = df22_emp["NOMBRE_EMPRESA"].astype(str).str.strip()
    primas22 = df22_emp["PRIMAS_NETAS"]

    # Índice por nombre normalizado en C4
    map4 = {}
    for i in range(len(df4)):
        n = _normalizar(nom4.iloc[i])
        if n and n != "TOTAL":
            map4[n] = (i, float(total4.iloc[i]))

    todo_ok = True
    no_encontradas = []
    diferencias = []
    print("")
    print("  Cuadro 22 vs Cuadro 4 – Primas Netas por empresa = TOTAL Cuadro 4")
    print("")

    for i in range(len(df22_emp)):
        nombre = nom22.iloc[i]
        primas_c22 = float(primas22.iloc[i])
        n_norm = _normalizar(nombre)
        if n_norm not in map4:
            # Intentar match flexible (ej. C.A. vs S.A.)
            n_alt = n_norm.replace(" C.A.", " S.A.") if " C.A." in n_norm else n_norm.replace(" S.A.", " C.A.")
            if n_alt in map4:
                n_norm = n_alt
            else:
                no_encontradas.append(nombre)
                continue
        _, total_c4 = map4[n_norm]
        diff = abs(primas_c22 - total_c4)
        if diff > TOLERANCIA:
            diferencias.append((nombre, primas_c22, total_c4, diff))
            todo_ok = False

    if no_encontradas:
        print("  Empresas en C22 no encontradas en C4 ({}): {}.".format(len(no_encontradas), no_encontradas[:5]))
        if len(no_encontradas) > 5:
            print("    ... y {} más.".format(len(no_encontradas) - 5))
        print("")
    if diferencias:
        for nom, p22, t4, d in diferencias[:10]:
            print("  Diferencia: {}  C22={:,.0f}  C4={:,.0f}  diff={:,.0f}".format(nom[:40], p22, t4, d))
        if len(diferencias) > 10:
            print("    ... y {} más.".format(len(diferencias) - 10))
        print("")
    if todo_ok and not no_encontradas:
        print("  Todas las empresas coinciden (Primas Netas C22 = TOTAL C4) dentro de tolerancia.")
    elif todo_ok and no_encontradas:
        print("  Empresas encontradas coinciden; hay {} empresas en C22 sin match en C4.".format(len(no_encontradas)))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
