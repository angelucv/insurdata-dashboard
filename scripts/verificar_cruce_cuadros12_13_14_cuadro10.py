# scripts/verificar_cruce_cuadros12_13_14_cuadro10.py
"""
Verifica Cuadros 12, 13 y 14 (reservas de prima por empresa por sección) contra Cuadro 10:
- Cuadro 12 (SEGUROS DE PERSONAS): suma de todas las empresas = fila "SEGURO DE PERSONAS" del Cuadro 10.
- Cuadro 13 (SEGUROS PATRIMONIALES): suma de todas las empresas = fila "SEGUROS PATRIMONIALES" del Cuadro 10.
- Cuadro 14 (OBLIGACIONALES/RESPONSABILIDAD): suma de todas las empresas = fila "SEGUROS DE RESPONSABILIDAD" del Cuadro 10.
Columnas: Retención propia, A cargo de Reaseguradores, Total.
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


def _normalizar(s: str) -> str:
    return s.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def _fila_cuadro10_por_seccion(df10, nombre_seccion: str) -> tuple[float, float, float] | None:
    """Devuelve (RETENCION_PROPIA, A_CARGO_REASEGURADORES, TOTAL) de la fila del Cuadro 10 que coincida con nombre_seccion."""
    col = df10["RAMO_DE_SEGUROS"].astype(str).str.strip()
    n = _normalizar(nombre_seccion.strip())
    for i in range(len(df10)):
        if _normalizar(col.iloc[i]) == n:
            return (
                float(df10["RETENCION_PROPIA"].iloc[i]),
                float(df10["A_CARGO_REASEGURADORES"].iloc[i]),
                float(df10["TOTAL"].iloc[i]),
            )
    return None


def run_verificacion(anio: int = 2023) -> bool:
    """Compara suma de empresas en Cuadros 12, 13, 14 con las filas correspondientes del Cuadro 10."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path10 = carpeta / "cuadro_10_reservas_prima_por_ramo.csv"
    path12 = carpeta / "cuadro_12_reservas_prima_personas_por_empresa.csv"
    path13 = carpeta / "cuadro_13_reservas_prima_patrimoniales_por_empresa.csv"
    path14 = carpeta / "cuadro_14_reservas_prima_obligacionales_por_empresa.csv"
    for p in (path10, path12, path13, path14):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df10 = pd.read_csv(path10, sep=SEP, encoding=ENCODING)
    df12 = pd.read_csv(path12, sep=SEP, encoding=ENCODING)
    df13 = pd.read_csv(path13, sep=SEP, encoding=ENCODING)
    df14 = pd.read_csv(path14, sep=SEP, encoding=ENCODING)

    def excluir_total(df):
        return df[df.iloc[:, 0].astype(str).str.strip().str.upper() != "TOTAL"]

    todo_ok = True
    print("")
    print("  Cuadros 12, 13, 14 vs Cuadro 10 – Reservas por empresa (Personas, Patrimoniales, Obligacionales)")
    print("")

    # Cuadro 12 = SEGURO DE PERSONAS
    fila_10 = _fila_cuadro10_por_seccion(df10, "SEGURO DE PERSONAS")
    if fila_10 is None:
        print("  [ERROR] Cuadro 10 no tiene fila 'SEGURO DE PERSONAS'.")
        todo_ok = False
    else:
        d12 = excluir_total(df12)
        s_ret = d12["RETENCION_PROPIA"].sum()
        s_reas = d12["A_CARGO_REASEGURADORES"].sum()
        s_tot = d12["TOTAL"].sum()
        r10, re10, t10 = fila_10
        if abs(s_ret - r10) <= TOLERANCIA and abs(s_reas - re10) <= TOLERANCIA and abs(s_tot - t10) <= TOLERANCIA:
            print("  Cuadro 12 (Personas)     suma empresas = Cuadro 10 'SEGURO DE PERSONAS'  OK")
        else:
            print("  Cuadro 12 (Personas)     Ret {:,.0f} vs {:,.0f}  Reas {:,.0f} vs {:,.0f}  Total {:,.0f} vs {:,.0f}".format(
                s_ret, r10, s_reas, re10, s_tot, t10
            ))
            todo_ok = False

    # Cuadro 13 = SEGUROS PATRIMONIALES
    fila_10 = _fila_cuadro10_por_seccion(df10, "SEGUROS PATRIMONIALES")
    if fila_10 is None:
        print("  [ERROR] Cuadro 10 no tiene fila 'SEGUROS PATRIMONIALES'.")
        todo_ok = False
    else:
        d13 = excluir_total(df13)
        s_ret = d13["RETENCION_PROPIA"].sum()
        s_reas = d13["A_CARGO_REASEGURADORES"].sum()
        s_tot = d13["TOTAL"].sum()
        r10, re10, t10 = fila_10
        if abs(s_ret - r10) <= TOLERANCIA and abs(s_reas - re10) <= TOLERANCIA and abs(s_tot - t10) <= TOLERANCIA:
            print("  Cuadro 13 (Patrimoniales) suma empresas = Cuadro 10 'SEGUROS PATRIMONIALES'  OK")
        else:
            print("  Cuadro 13 (Patrimoniales) Ret {:,.0f} vs {:,.0f}  Reas {:,.0f} vs {:,.0f}  Total {:,.0f} vs {:,.0f}".format(
                s_ret, r10, s_reas, re10, s_tot, t10
            ))
            todo_ok = False

    # Cuadro 14 = SEGUROS DE RESPONSABILIDAD
    fila_10 = _fila_cuadro10_por_seccion(df10, "SEGUROS DE RESPONSABILIDAD")
    if fila_10 is None:
        print("  [ERROR] Cuadro 10 no tiene fila 'SEGUROS DE RESPONSABILIDAD'.")
        todo_ok = False
    else:
        d14 = excluir_total(df14)
        s_ret = d14["RETENCION_PROPIA"].sum()
        s_reas = d14["A_CARGO_REASEGURADORES"].sum()
        s_tot = d14["TOTAL"].sum()
        r10, re10, t10 = fila_10
        if abs(s_ret - r10) <= TOLERANCIA and abs(s_reas - re10) <= TOLERANCIA and abs(s_tot - t10) <= TOLERANCIA:
            print("  Cuadro 14 (Obligacionales) suma empresas = Cuadro 10 'SEGUROS DE RESPONSABILIDAD'  OK")
        else:
            print("  Cuadro 14 (Obligacionales) Ret {:,.0f} vs {:,.0f}  Reas {:,.0f} vs {:,.0f}  Total {:,.0f} vs {:,.0f}".format(
                s_ret, r10, s_reas, re10, s_tot, t10
            ))
            todo_ok = False

    print("")
    if todo_ok:
        print("  Resultado: COINCIDE.")
    else:
        print("  Resultado: HAY DISCREPANCIAS.")
    print("")
    return todo_ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadros 12, 13, 14 vs Cuadro 10 (reservas por sección)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
