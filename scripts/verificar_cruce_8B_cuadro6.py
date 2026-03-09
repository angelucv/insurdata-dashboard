# scripts/verificar_cruce_8B_cuadro6.py
"""
Verifica que el Cuadro 8-B (Siniestros Patrimoniales por ramo/empresa, pág 31, 32, 33)
coincida por ramo con el Cuadro 6 (Siniestros por ramo – 16 ramos Seguros Patrimoniales).
- Pág 31: 5 ramos (Incendio, Terremoto, Robo, Transporte, Ramos Técnicos).
- Pág 32: 6 ramos (Petroleros, Combinados, Lucro cesante, Automóvil casco, Aeronaves, Naves).
- Pág 33: 5 ramos + TOTAL (Agrícola, Pecuario, Bancarios, Joyería, Diversos, TOTAL).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED
from scripts.verificar_cruce_5B_cuadro3 import RAMOS_SEG_PATRIMONIALES

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 50


def _normalizar(s: str) -> str:
    return s.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def _valor_cuadro6_ramo(df6, nombre_ramo: str) -> float | None:
    """Devuelve SEGURO DIRECTO del ramo en Cuadro 6. Coincidencia exacta normalizada."""
    col_ramo = df6.iloc[:, 0]
    n = _normalizar(nombre_ramo.strip())
    for i in range(len(df6)):
        r = _normalizar(str(col_ramo.iloc[i]).strip())
        if r == n:
            return float(df6["SEGURO DIRECTO"].iloc[i])
    return None


def run_verificacion(anio: int = 2023) -> bool:
    """Compara sumas por columna del Cuadro 8-B con valores del Cuadro 6."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path6 = carpeta / "cuadro_06_siniestros_pagados_por_ramo.csv"
    path_p31 = carpeta / "cuadro_08B_pag31_5_ramos.csv"
    path_p32 = carpeta / "cuadro_08B_pag32_6_ramos.csv"
    path_p33 = carpeta / "cuadro_08B_pag33_5_ramos_total.csv"
    if not path6.exists() or not path_p31.exists() or not path_p32.exists() or not path_p33.exists():
        print("[ERROR] Faltan cuadro_06 o cuadro_08B en {}.".format(carpeta))
        return False
    df6 = pd.read_csv(path6, sep=SEP, encoding=ENCODING)
    df31 = pd.read_csv(path_p31, sep=SEP, encoding=ENCODING)
    df32 = pd.read_csv(path_p32, sep=SEP, encoding=ENCODING)
    df33 = pd.read_csv(path_p33, sep=SEP, encoding=ENCODING)

    for df in (df31, df32, df33):
        df.drop(df[df.iloc[:, 0].astype(str).str.strip().str.upper() == "TOTAL"].index, inplace=True)

    ok = True
    print("")
    print("  Cuadro 8-B vs Cuadro 6 – Siniestros Patrimoniales (16 ramos)")
    print("")

    # Ramos en C6 pueden tener "Ramos Tecnicos" sin tilde; RAMOS_SEG_PATRIMONIALES tiene "Ramos Técnicos"
    for idx, col in enumerate(RAMOS_SEG_PATRIMONIALES):
        if idx < 5:
            sum_8b = df31[col].sum()
        elif idx < 11:
            sum_8b = df32[col].sum()
        else:
            sum_8b = df33[col].sum()
        nombre_c6 = col.replace("Ramos Técnicos", "Ramos Tecnicos")
        val_c6 = _valor_cuadro6_ramo(df6, nombre_c6)
        if val_c6 is None:
            val_c6 = _valor_cuadro6_ramo(df6, col)
        c6 = val_c6 if val_c6 is not None else 0
        diff = abs(sum_8b - c6)
        coincide = diff <= TOLERANCIA
        if not coincide:
            ok = False
        print("    {:25s}  8-B: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
            col[:25], sum_8b, c6, "OK" if coincide else "NO COINCIDE", "(diff {:.0f})".format(diff) if not coincide else ""))

    total_8b = df31[[RAMOS_SEG_PATRIMONIALES[i] for i in range(5)]].sum().sum()
    total_8b += df32[[RAMOS_SEG_PATRIMONIALES[i] for i in range(5, 11)]].sum().sum()
    total_8b += df33[[RAMOS_SEG_PATRIMONIALES[i] for i in range(11, 16)]].sum().sum()
    total_c6 = _valor_cuadro6_ramo(df6, "SEGUROS PATRIMONIALES")
    if total_c6 is None:
        total_c6 = 0
    diff_total = abs(total_8b - total_c6)
    coincide_total = diff_total <= TOLERANCIA
    if not coincide_total:
        ok = False
    print("    {:25s}  8-B: {:>12,.0f}   C6: {:>12,.0f}   {} {}".format(
        "SUBTOTAL PATRIMONIALES", total_8b, total_c6, "OK" if coincide_total else "NO COINCIDE", "(diff {:.0f})".format(diff_total) if not coincide_total else ""))
    print("")
    if ok:
        print("  Resultado: COINCIDE (totales 8-B = Cuadro 6, salvo redondeo).")
    else:
        print("  Resultado: HAY DIFERENCIAS.")
    print("")
    return ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 8-B vs Cuadro 6 (siniestros Patrimoniales)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
