"""
Verifica Cuadro 23 (gastos de producción vs primas netas por ramo) contra Cuadro 3:
- La columna PRIMAS_NETAS del Cuadro 23 debe coincidir con la columna SEGURO DIRECTO del Cuadro 3 para cada ramo.
- Cuadro 3 tiene primas por ramo (SEGURO DIRECTO); Cuadro 23 tiene las mismas primas netas por ramo más gastos.
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

# Ramos obligacionales en C3 (para comparar sección C23 "SEGUROS OBLIGACIONALES O DE RESPONSABILIDAD")
RAMOS_OBLIGACIONALES_C3 = [
    "Responsabilidad Civil Automóvil",
    "Responsabilidad Civil Patronal",
    "Responsabilidad Civil General",
    "Responsabilidad Civil Profesional",
    "Fianzas",
    "Fidelidad de Empleados",
    "Responsabilidad Civil de Productos",
    "Seguros de Crédito",
]


def _normalizar(s: str) -> str:
    return s.upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path3 = carpeta / "cuadro_03_primas_por_ramo.csv"
    path23 = carpeta / "cuadro_23_gastos_produccion_vs_primas_por_ramo.csv"
    for p in (path3, path23):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df3 = pd.read_csv(path3, sep=SEP, encoding=ENCODING)
    df23 = pd.read_csv(path23, sep=SEP, encoding=ENCODING)

    # C3: mapa ramo normalizado -> SEGURO DIRECTO
    col_ramo_c3 = df3.columns[0]
    col_seguro = [c for c in df3.columns if "SEGURO" in c.upper() and "DIRECTO" in c.upper()]
    if not col_seguro:
        col_seguro = [df3.columns[1]]
    col_seguro = col_seguro[0]
    map3 = {}
    for i in range(len(df3)):
        ramo = str(df3[col_ramo_c3].iloc[i]).strip()
        n = _normalizar(ramo)
        if n:
            map3[n] = float(df3[col_seguro].iloc[i])

    # C23: para cada fila, PRIMAS_NETAS debe = C3 SEGURO DIRECTO (mismo ramo o sección)
    todo_ok = True
    diferencias = []
    no_encontrados = []

    for i in range(len(df23)):
        ramo23 = str(df23["RAMO_DE_SEGUROS"].iloc[i]).strip()
        primas23 = float(df23["PRIMAS_NETAS"].iloc[i])
        n23 = _normalizar(ramo23)

        if n23 == "TOTAL":
            total_c3 = sum(map3.get(_normalizar(r), 0) for r in df3[col_ramo_c3])
            # C3 TOTAL row
            fila_total_c3 = df3[df3[col_ramo_c3].astype(str).str.strip().str.upper() == "TOTAL"]
            if len(fila_total_c3) > 0:
                total_c3 = float(fila_total_c3[col_seguro].iloc[0])
            if abs(primas23 - total_c3) > TOLERANCIA:
                diferencias.append((ramo23, primas23, total_c3, primas23 - total_c3))
                todo_ok = False
            continue

        if n23 == _normalizar("SEGUROS OBLIGACIONALES O DE RESPONSABILIDAD"):
            suma_c3 = sum(map3.get(_normalizar(r), 0) for r in RAMOS_OBLIGACIONALES_C3)
            if abs(primas23 - suma_c3) > TOLERANCIA:
                diferencias.append((ramo23, primas23, suma_c3, primas23 - suma_c3))
                todo_ok = False
            continue

        if n23 not in map3:
            # Intentar match flexible (ej. Automóviles casco vs Automóvil casco)
            for k in map3:
                if k.replace("AUTOMOVILES", "AUTOMOVIL") == n23.replace("AUTOMOVILES", "AUTOMOVIL") or k == n23:
                    n23 = k
                    break
            if n23 not in map3:
                no_encontrados.append(ramo23)
                continue
        val_c3 = map3[n23]
        if abs(primas23 - val_c3) > TOLERANCIA:
            diferencias.append((ramo23, primas23, val_c3, primas23 - val_c3))
            todo_ok = False

    print("")
    print("  Cuadro 23 vs Cuadro 3 – Primas Netas por ramo = SEGURO DIRECTO Cuadro 3")
    print("")

    if no_encontrados:
        print("  Ramos en C23 no encontrados en C3: {}.".format(no_encontrados))
        print("")
    if diferencias:
        for ramo, p23, v3, d in diferencias[:15]:
            print("  Diferencia: {}  C23={:,.0f}  C3={:,.0f}  diff={:,.0f}".format(ramo[:45], p23, v3, d))
        if len(diferencias) > 15:
            print("    ... y {} más.".format(len(diferencias) - 15))
        print("")
        todo_ok = False
    if todo_ok and not no_encontrados:
        print("  Todos los ramos coinciden (PRIMAS_NETAS C23 = SEGURO DIRECTO C3) dentro de tolerancia.")
    elif todo_ok:
        print("  Ramos encontrados coinciden.")
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
