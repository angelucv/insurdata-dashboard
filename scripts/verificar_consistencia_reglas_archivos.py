# scripts/verificar_consistencia_reglas_archivos.py
"""
Comprueba la consistencia entre las reglas de validación (REGLAS, índice de cuadros)
y los archivos CSV generados: que todos los archivos esperados existan, que no haya
archivos en disco sin cuadro asociado, y que los scripts de verificación referenciados existan.

Uso: python scripts/verificar_consistencia_reglas_archivos.py [--year 2023]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED
from scripts.verificar_indice_anuario import INDICE_CSV_POR_CUADRO, ORDEN_CUADROS

SCRIPTS_REGLAS = [
    "verificar_cruce_5A_cuadro3.py",
    "verificar_cruce_5B_cuadro3.py",
    "verificar_cruce_5C_cuadro3.py",
    "verificar_cuadro_6_siniestros.py",
    "verificar_cruce_cuadro7_cuadro6.py",
    "verificar_cruce_8A_cuadro6.py",
    "verificar_cruce_8B_cuadro6.py",
    "verificar_cruce_8C_cuadro6.py",
    "verificar_cuadro_9_reservas.py",
    "verificar_cruce_cuadro10_cuadro9.py",
    "verificar_cruce_cuadro11_cuadro10.py",
    "verificar_cruce_cuadros12_13_14_cuadro10.py",
    "verificar_cruce_cuadro15_cuadro9.py",
    "verificar_cruce_cuadro16_cuadro15.py",
    "verificar_cruce_cuadro17_cuadro15.py",
    "verificar_cruce_cuadros18_19_cuadro15.py",
    "verificar_cruce_cuadro20A_cuadro12.py",
    "verificar_cruce_cuadro20B_cuadro13.py",
    "verificar_cruce_cuadro20C_cuadro14.py",
    "verificar_cruce_cuadro20D_cuadro17.py",
    "verificar_cruce_cuadro20E_cuadro18.py",
    "verificar_cruce_cuadro20F_cuadro19.py",
    "verificar_cruce_cuadro22_cuadro4.py",
    "verificar_cruce_cuadro23_cuadro3.py",
    "verificar_cruce_cuadros23_ABCDEF_cuadro23.py",
    "verificar_cruce_cuadro25A_cuadro3.py",
    "verificar_cruce_cuadro25B_cuadro6_cuadro23.py",
    "verificar_cruce_cuadro26_cuadro25A_25B.py",
    "verificar_cruce_cuadro27_cuadro26.py",
    "verificar_cruce_cuadro28_cuadro24.py",
    "verificar_cruce_cuadro29_indicadores.py",
    "verificar_cruce_cuadro31A_cuadro4.py",
    "verificar_cruce_cuadro31B_2023.py",
    "verificar_cruce_cuadro32_cuadros10_15_20A_20D.py",
    "verificar_cruce_cuadro33_cuadros10_15_20A_20D.py",
    "verificar_cruce_cuadro34_cuadro3.py",
    "verificar_cruce_cuadro35.py",
    "verificar_cruce_cuadro36_cuadro16.py",
    "verificar_cruce_cuadro38_cuadro37.py",
    "verificar_cuadro40_balance_reaseguros.py",
    "verificar_cuadro41A_ingresos_reaseguros.py",
    "verificar_cuadro41B_egresos_reaseguros.py",
    "verificar_cruce_cuadro42_cuadro40.py",
    "verificar_cruce_cuadros43_41.py",
    "verificar_cuadro44_indicadores_reaseguros.py",
    "verificar_cruce_cuadro49_cuadro48.py",
    "verificar_cruce_cuadro50_cuadro47.py",
    "verificar_cruce_cuadro51_cuadro48.py",
    "verificar_cuadro54_balance_medicina_prepagada.py",
    "verificar_cuadros55_medicina_prepagada.py",
    "verificar_cruce_cuadro57_cuadro54.py",
]


def run_verificacion(anio: int = 2023) -> bool:
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    scripts_dir = ROOT / "scripts"

    esperados = [
        f for cid in ORDEN_CUADROS for f in INDICE_CSV_POR_CUADRO.get(cid, []) if f
    ]
    en_disco = set(f.name for f in carpeta.glob("*.csv")) if carpeta.exists() else set()

    faltan = [f for f in esperados if f not in en_disco]
    sobran = [f for f in en_disco if f not in esperados]
    scripts_faltantes = [s for s in SCRIPTS_REGLAS if not (scripts_dir / s).exists()]

    todo_ok = True
    print("")
    print("=== Consistencia reglas de validación vs archivos generados (año {}) ===".format(anio))
    print("")
    print("  Archivos esperados (índice): {}  |  En disco: {}".format(len(esperados), len(en_disco)))

    if faltan:
        todo_ok = False
        print("  [FALTA] No encontrados en {}:".format(carpeta))
        for f in faltan:
            print("    - {}".format(f))
    else:
        print("  [OK] Todos los archivos esperados ({} CSV) están en {}.".format(len(esperados), carpeta))

    if sobran:
        todo_ok = False
        print("  [SOBRAN] Archivos en disco no listados en el índice (revisar REGLAS/INDICE_CSV_POR_CUADRO):")
        for f in sorted(sobran):
            print("    - {}".format(f))
    elif not faltan:
        print("  [OK] No hay archivos en disco sin cuadro asociado en el índice.")

    if scripts_faltantes:
        todo_ok = False
        print("  [FALTA] Scripts referenciados en REGLAS no encontrados en scripts/:")
        for s in scripts_faltantes:
            print("    - {}".format(s))
    else:
        print("  [OK] Todos los scripts de verificación referenciados en REGLAS existen.")

    cuadros_con_archivos = [c for c in ORDEN_CUADROS if c not in ("1", "2") and INDICE_CSV_POR_CUADRO.get(c)]
    print("")
    print("  Cuadros con archivos: {} (cuadros 3 a 58), {} archivos CSV.".format(
        len(cuadros_con_archivos),
        len(esperados),
    ))
    print("")
    return todo_ok


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Verificar consistencia reglas vs archivos CSV")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    sys.exit(0 if run_verificacion(args.year) else 1)
