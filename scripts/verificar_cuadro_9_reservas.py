# scripts/verificar_cuadro_9_reservas.py
"""
Verifica el Cuadro 9 (Reservas técnicas por retención propia):
- Para cada sección (SECCION) que tiene subdivisiones, la suma de las subdivisiones debe igualar el total de la sección.
- El TOTAL general debe coincidir con la suma de los montos de todas las secciones.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 5.0


def run_verificacion(anio: int = 2023) -> bool:
    """Lee el CSV del Cuadro 9 y verifica coherencia sección vs subdivisiones y TOTAL."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path = carpeta / "cuadro_09_reservas_tecnicas.csv"
    if not path.exists():
        print("[ERROR] No existe {}.".format(path))
        return False
    df = pd.read_csv(path, sep=SEP, encoding=ENCODING)
    if "CONCEPTO" not in df.columns or "MONTO" not in df.columns or "TIPO" not in df.columns:
        print("[ERROR] CSV debe tener columnas CONCEPTO, MONTO, TIPO.")
        return False
    conceptos = df["CONCEPTO"].astype(str)
    montos = df["MONTO"].astype(float)
    tipos = df["TIPO"].astype(str).str.strip()
    todo_ok = True
    i = 0
    total_secciones = 0.0
    total_documento = None
    while i < len(df):
        if tipos.iloc[i] == "SECCION":
            total_seccion = montos.iloc[i]
            nombre = conceptos.iloc[i].strip()
            if nombre.upper() == "TOTAL":
                total_documento = total_seccion
            else:
                total_secciones += total_seccion
            suma_sub = 0.0
            j = i + 1
            while j < len(df) and tipos.iloc[j] == "SUBDIVISION":
                suma_sub += montos.iloc[j]
                j += 1
            if j > i + 1:
                diff = abs(suma_sub - total_seccion)
                tol = max(TOLERANCIA, total_seccion * 1e-6)
                if diff > tol:
                    print(
                        "[Cuadro 9] Seccion '{}': total {:,.0f} vs suma subdivisiones {:,.0f} (diff {:,.0f})".format(
                            nombre, total_seccion, suma_sub, diff
                        )
                    )
                    todo_ok = False
            i = j
            continue
        i += 1
    if total_documento is not None and total_secciones > 0:
        diff_total = abs(total_secciones - total_documento)
        if diff_total > max(TOLERANCIA, total_documento * 1e-6):
            print(
                "[Cuadro 9] Suma de secciones {:,.0f} vs TOTAL documento {:,.0f} (diff {:,.0f})".format(
                    total_secciones, total_documento, diff_total
                )
            )
            todo_ok = False
    print("")
    print("  Cuadro 9 – Reservas técnicas por retención propia")
    print("  Verificación: suma(subdivisiones) = total por sección; suma(secciones) = TOTAL.")
    if todo_ok:
        print("  Resultado: COINCIDE.")
    else:
        print("  Resultado: HAY DISCREPANCIAS.")
    print("")
    return todo_ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 9 (reservas técnicas)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
