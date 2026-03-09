# scripts/verificar_cruce_8A_cuadro6.py
"""
Verifica que el Cuadro 8-A (Siniestros Personas por ramo/empresa, pág 29 y 30)
coincida por ramo con el Cuadro 6 (Siniestros por ramo).
- Pág 29: 5 columnas (Vida Individual, Vida Desgravamen, Rentas Vitalicias, Vida Colectivo, Otras Prestaciones).
- Pág 30: 5 ramos + TOTAL (Accidentes Pers. Ind./Col., Hospitalización Ind./Col., Seguros Funerarios, TOTAL).
- Cuadro 6 incluye "Otras Prestaciones"; los totales pueden no coincidir exactamente por redondeos.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"

# Orden: p29 (5) + p30 (5) = 10 conceptos. C6 tiene los 9 ramos + Otras Prestaciones.
COLUMNAS_8A_P29 = ["Vida Individual", "Vida Desgravamen Hipotecario", "Rentas Vitalicias", "Vida Colectivo", "Otras Prestaciones"]
COLUMNAS_8A_P30 = ["Accidentes Personales Individual", "Accidentes Personales Colectivo", "Hospitalizacion Individual", "Hospitalizacion Colectivo", "Seguros Funerarios"]


def _normalizar(s: str) -> str:
    return s.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def _valor_cuadro6_ramo(df6, nombre_ramo: str) -> float | None:
    """Devuelve SEGURO DIRECTO del ramo en Cuadro 6. Coincidencia exacta normalizada (evita Individual vs Colectivo)."""
    col_ramo = df6.iloc[:, 0]
    n = _normalizar(nombre_ramo.strip())
    for i in range(len(df6)):
        r = _normalizar(str(col_ramo.iloc[i]).strip())
        if r == n:
            return float(df6["SEGURO DIRECTO"].iloc[i])
    return None


def run_verificacion(anio: int = 2023) -> bool:
    """Compara sumas por columna del Cuadro 8-A con valores del Cuadro 6."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path6 = carpeta / "cuadro_06_siniestros_pagados_por_ramo.csv"
    path_p29 = carpeta / "cuadro_08A_pag29_5_ramos.csv"
    path_p30 = carpeta / "cuadro_08A_pag30_5_ramos_total.csv"
    if not path6.exists() or not path_p29.exists() or not path_p30.exists():
        print("[ERROR] Faltan cuadro_06 o cuadro_08A en {}.".format(carpeta))
        return False
    df6 = pd.read_csv(path6, sep=SEP, encoding=ENCODING)
    df29 = pd.read_csv(path_p29, sep=SEP, encoding=ENCODING)
    df30 = pd.read_csv(path_p30, sep=SEP, encoding=ENCODING)

    # Excluir fila TOTAL si existe
    df29_sin = df29[df29.iloc[:, 0].astype(str).str.strip().str.upper() != "TOTAL"]
    df30_sin = df30[df30.iloc[:, 0].astype(str).str.strip().str.upper() != "TOTAL"]

    tolerancia = 50
    ok = True
    print("")
    print("  Cuadro 8-A vs Cuadro 6 – Siniestros Personas por ramo")
    print("  (Cuadro 6 incluye Otras Prestaciones; puede haber pequenas diferencias por redondeo)")
    print("")

    # P29: 5 columnas
    for col in COLUMNAS_8A_P29:
        sum_8a = df29_sin[col].sum()
        val_c6 = _valor_cuadro6_ramo(df6, col)
        if val_c6 is None:
            val_c6 = _valor_cuadro6_ramo(df6, col.replace("Hospitalizacion", "Hospitalización"))
        c6 = val_c6 if val_c6 is not None else 0
        diff = abs(sum_8a - c6)
        coincide = diff <= tolerancia
        if not coincide:
            ok = False
        print("    {:35s}  8-A: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
            col[:35], sum_8a, c6, "OK" if coincide else "NO COINCIDE", "(diff {:.0f})".format(diff) if not coincide else ""))

    # P30: 5 columnas (sin TOTAL)
    for col in COLUMNAS_8A_P30:
        sum_8a = df30_sin[col].sum()
        nombre_c6 = col.replace("Hospitalizacion", "Hospitalización")
        val_c6 = _valor_cuadro6_ramo(df6, nombre_c6)
        if val_c6 is None:
            val_c6 = _valor_cuadro6_ramo(df6, col)
        c6 = val_c6 if val_c6 is not None else 0
        diff = abs(sum_8a - c6)
        coincide = diff <= tolerancia
        if not coincide:
            ok = False
        print("    {:35s}  8-A: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
            col[:35], sum_8a, c6, "OK" if coincide else "NO COINCIDE", "(diff {:.0f})".format(diff) if not coincide else ""))

    # Total Personas: suma de las 10 columnas 8-A vs SEGURO DE PERSONAS en C6
    suma_p29 = df29_sin[COLUMNAS_8A_P29].sum().sum()
    suma_p30_5 = df30_sin[COLUMNAS_8A_P30].sum().sum()
    total_8a = suma_p29 + suma_p30_5
    total_c6 = _valor_cuadro6_ramo(df6, "SEGURO DE PERSONAS")
    if total_c6 is None:
        total_c6 = float(df6[df6.iloc[:, 0].astype(str).str.strip().str.upper() == "SEGURO DE PERSONAS"]["SEGURO DIRECTO"].iloc[0])
    diff_total = abs(total_8a - total_c6)
    coincide_total = diff_total <= tolerancia
    if not coincide_total:
        ok = False
    print("    {:35s}  8-A: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
        "SUBTOTAL PERSONAS (10 conceptos)", total_8a, total_c6, "OK" if coincide_total else "NO COINCIDE", "(diff {:.0f})".format(diff_total) if not coincide_total else ""))
    print("")
    if ok:
        print("  Resultado: COINCIDE (totales 8-A = Cuadro 6, salvo redondeo/Otras Prestaciones).")
    else:
        print("  Resultado: HAY DIFERENCIAS (revisar redondeos o concepto Otras Prestaciones).")
    print("")
    return ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 8-A vs Cuadro 6 (siniestros Personas)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
