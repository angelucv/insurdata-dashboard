# scripts/verificar_cruce_cuadro10_cuadro9.py
"""
Verifica el Cuadro 10 (Reservas de prima por ramo, pág 37) contra el Cuadro 9 (Reservas técnicas):
- Por línea en Cuadro 10: RETENCION_PROPIA + A_CARGO_REASEGURADORES = TOTAL.
- Las tres secciones (SEGURO DE PERSONAS, SEGUROS PATRIMONIALES, SEGUROS DE RESPONSABILIDAD): la suma de sus
  subdivisiones debe igualar el total de la sección (por cada columna).
- La columna RETENCION_PROPIA de esas tres secciones debe coincidir con Cuadro 9:
  - SEGURO DE PERSONAS = Cuadro 9 "RESERVAS DE PRIMA SEGUROS DE PERSONAS"
  - SEGUROS PATRIMONIALES = Cuadro 9 "Patrimoniales" (bajo RESERVAS DE PRIMAS SEGUROS GENERALES)
  - SEGUROS DE RESPONSABILIDAD = Cuadro 9 "Obligacionales o de responsabilidad" (bajo RESERVAS DE PRIMAS SEGUROS GENERALES)
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


def _valor_cuadro9(df9, concepto_buscar: str) -> float | None:
    """Devuelve MONTO del concepto en Cuadro 9 (CONCEPTO exacto normalizado)."""
    col = df9["CONCEPTO"].astype(str)
    n = _normalizar(concepto_buscar.strip())
    for i in range(len(df9)):
        if _normalizar(col.iloc[i].strip()) == n:
            return float(df9["MONTO"].iloc[i])
    return None


def run_verificacion(anio: int = 2023) -> bool:
    """Verifica Cuadro 10: suma por línea, suma por sección y cruce con Cuadro 9."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path9 = carpeta / "cuadro_09_reservas_tecnicas.csv"
    path10 = carpeta / "cuadro_10_reservas_prima_por_ramo.csv"
    if not path9.exists() or not path10.exists():
        print("[ERROR] Faltan cuadro_09 o cuadro_10 en {}.".format(carpeta))
        return False
    df9 = pd.read_csv(path9, sep=SEP, encoding=ENCODING)
    df10 = pd.read_csv(path10, sep=SEP, encoding=ENCODING)
    ramo = df10["RAMO_DE_SEGUROS"].astype(str).str.strip()
    ret = df10["RETENCION_PROPIA"].astype(float)
    reas = df10["A_CARGO_REASEGURADORES"].astype(float)
    total = df10["TOTAL"].astype(float)
    todo_ok = True
    print("")
    print("  Cuadro 10 vs Cuadro 9 – Reservas de prima por ramo")
    print("")

    # 1) Por línea: RETENCION_PROPIA + A_CARGO_REASEGURADORES = TOTAL
    for i in range(len(df10)):
        s = ret.iloc[i] + reas.iloc[i]
        diff = abs(s - total.iloc[i])
        if diff > TOLERANCIA:
            print("  [Cuadro 10] Linea '{}': Ret+Reas={:,.0f} vs Total={:,.0f} (diff {:,.0f})".format(
                ramo.iloc[i], s, total.iloc[i], diff
            ))
            todo_ok = False
    if todo_ok:
        print("  Por linea: Retencion + Reaseguradores = Total  OK")
    print("")

    # 2) Secciones Cuadro 10: SEGURO DE PERSONAS, SEGUROS PATRIMONIALES, SEGUROS DE RESPONSABILIDAD
    secciones = [
        ("SEGURO DE PERSONAS", "RESERVAS DE PRIMA SEGUROS DE PERSONAS"),
        ("SEGUROS PATRIMONIALES", "Patrimoniales"),
        ("SEGUROS DE RESPONSABILIDAD", "Obligacionales o de responsabilidad"),
    ]
    for nombre_10, nombre_9 in secciones:
        idx = ramo[ramo.str.upper() == nombre_10.upper()].index
        if len(idx) == 0:
            print("  [Cuadro 10] No se encontro seccion '{}'".format(nombre_10))
            todo_ok = False
            continue
        i_sec = idx[0]
        r_sec = int(ramo.index.get_loc(i_sec))
        total_ret_sec = ret.iloc[i_sec]
        total_reas_sec = reas.iloc[i_sec]
        total_tot_sec = total.iloc[i_sec]
        sum_ret = 0.0
        sum_reas = 0.0
        sum_tot = 0.0
        j = r_sec + 1
        while j < len(df10) and ramo.iloc[j].upper() not in (
            "SEGUROS PATRIMONIALES", "SEGUROS DE RESPONSABILIDAD", "TOTAL"
        ):
            sum_ret += ret.iloc[j]
            sum_reas += reas.iloc[j]
            sum_tot += total.iloc[j]
            j += 1
        if j > r_sec + 1:
            for label, v_sec, v_sum in [
                ("Retencion propia", total_ret_sec, sum_ret),
                ("A cargo reaseguradores", total_reas_sec, sum_reas),
                ("Total", total_tot_sec, sum_tot),
            ]:
                diff = abs(v_sec - v_sum)
                if diff > TOLERANCIA:
                    print("  [Cuadro 10] Seccion '{}' {}: total {:,.0f} vs suma subdivisiones {:,.0f} (diff {:,.0f})".format(
                        nombre_10, label, v_sec, v_sum, diff
                    ))
                    todo_ok = False
        val_9 = _valor_cuadro9(df9, nombre_9)
        if val_9 is not None:
            diff_cruce = abs(total_ret_sec - val_9)
            if diff_cruce > TOLERANCIA:
                print("  [Cruce 10 vs 9] '{}': Cuadro 10 Retencion {:,.0f} vs Cuadro 9 '{}' {:,.0f} (diff {:,.0f})".format(
                    nombre_10, total_ret_sec, nombre_9, val_9, diff_cruce
                ))
                todo_ok = False
            else:
                print("  Cruce '{}' Retencion propia {:,.0f} = Cuadro 9 '{}'  OK".format(
                    nombre_10, total_ret_sec, nombre_9
                ))
        else:
            print("  [AVISO] Cuadro 9 no tiene concepto '{}' para cruce.".format(nombre_9))

    print("")
    if todo_ok:
        print("  Resultado: COINCIDE (lineas, secciones y cruce con Cuadro 9).")
    else:
        print("  Resultado: HAY DISCREPANCIAS.")
    print("")
    return todo_ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 10 vs Cuadro 9 (reservas prima por ramo)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
