"""
Verifica Cuadro 31-A (Primas netas cobradas por empresa 2023 vs 2022) contra Cuadro 4:

- La columna PRIMAS_2023 del Cuadro 31-A debe coincidir con la columna TOTAL del Cuadro 4 para cada empresa.
- Equivale al mismo cruce que Cuadro 22 (primas netas = total por empresa del Cuadro 4).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 500.0  # diferencias de redondeo


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
    path31a = carpeta / "cuadro_31A_primas_netas_cobradas_2023_vs_2022.csv"
    path4 = carpeta / "cuadro_04_primas_por_ramo_empresa.csv"
    for p in (path31a, path4):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df31a = pd.read_csv(path31a, sep=SEP, encoding=ENCODING)
    df4 = pd.read_csv(path4, sep=SEP, encoding=ENCODING)

    # Excluir fila Total de 31-A
    df31a_emp = df31a[
        df31a["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"
    ].copy()
    nom31 = df31a_emp["NOMBRE_EMPRESA"].astype(str).str.strip()
    primas_31 = df31a_emp["PRIMAS_2023"]

    nom4 = df4.iloc[:, 0].astype(str).str.strip()
    total4 = df4["TOTAL"]

    map4 = {}
    for i in range(len(df4)):
        n = _normalizar(nom4.iloc[i])
        if n and n != "TOTAL":
            map4[n] = float(total4.iloc[i])

    todo_ok = True
    no_encontradas = []
    diferencias = []
    print("")
    print("  Cuadro 31-A (Primas 2023) vs Cuadro 4 (TOTAL) – Primas netas por empresa")
    print("")

    for i in range(len(df31a_emp)):
        nombre = nom31.iloc[i]
        primas_c31 = float(primas_31.iloc[i])
        n_norm = _normalizar(nombre)
        # Quitar nota (3) (4) para matchear con C4
        n_buscar = n_norm.split(" (3)")[0].split(" (4)")[0].strip()
        if n_buscar not in map4:
            n_alt = n_buscar.replace(" C.A.", " S.A.") if " C.A." in n_buscar else n_buscar.replace(" S.A.", " C.A.")
            if n_alt in map4:
                n_buscar = n_alt
            else:
                for k in map4:
                    if n_buscar in k or k in n_buscar:
                        n_buscar = k
                        break
                else:
                    no_encontradas.append(nombre)
                    continue
        total_c4 = map4.get(n_buscar)
        if total_c4 is None:
            no_encontradas.append(nombre)
            continue
        diff = abs(primas_c31 - total_c4)
        if diff > TOLERANCIA:
            diferencias.append((nombre, primas_c31, total_c4, diff))
            todo_ok = False

    if no_encontradas:
        print("  Empresas en C31-A no encontradas en C4 ({}): {}.".format(len(no_encontradas), no_encontradas[:5]))
        if len(no_encontradas) > 5:
            print("    ...")
        print("")

    if diferencias:
        print("  Diferencias PRIMAS_2023 (C31-A) vs TOTAL (C4) > {}:".format(TOLERANCIA))
        for nom, p31, p4, d in diferencias[:10]:
            print("    {}  C31-A={:,.0f}  C4={:,.0f}  diff={:,.0f}".format(nom[:45], p31, p4, d))
        if len(diferencias) > 10:
            print("    ... ({} más)".format(len(diferencias) - 10))
        print("")
    else:
        print("  OK  Todas las empresas coinciden (PRIMAS_2023 = C4 TOTAL) dentro de tolerancia {}.".format(TOLERANCIA))
        print("")

    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
