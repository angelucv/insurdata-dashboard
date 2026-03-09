"""
Verifica que el TOTAL de reservas técnicas del Cuadro 57 (Reservas técnicas por empresa,
medicina prepagada) coincida con el concepto RESERVAS TÉCNICAS del Cuadro 54 (Balance condensado
empresas de medicina prepagada).

- Cuadro 57: fila TOTAL, columna TOTAL_RESERVAS (segunda tabla).
- Cuadro 54: línea RESERVAS TÉCNICAS en la sección PASIVO.
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
    return s.upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path57 = carpeta / "cuadro_57_reservas_tecnicas_por_empresa_medicina_prepagada.csv"
    path54 = carpeta / "cuadro_54_balance_condensado_medicina_prepagada.csv"
    if not path57.exists():
        print("[ERROR] No existe {}.".format(path57))
        return False
    if not path54.exists():
        print("[ERROR] No existe {}.".format(path54))
        return False

    df57 = pd.read_csv(path57, sep=SEP, encoding=ENCODING)
    df54 = pd.read_csv(path54, sep=SEP, encoding=ENCODING)

    if "NOMBRE_EMPRESA" not in df57.columns or "TOTAL_RESERVAS" not in df57.columns:
        print("[ERROR] Cuadro 57 debe tener NOMBRE_EMPRESA y TOTAL_RESERVAS.")
        return False
    if "CONCEPTO" not in df54.columns or "MONTO" not in df54.columns:
        print("[ERROR] Cuadro 54 debe tener CONCEPTO y MONTO.")
        return False

    total57 = df57.loc[df57["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL", "TOTAL_RESERVAS"]
    if total57.empty:
        print("[ERROR] Cuadro 57: no se encontró fila TOTAL.")
        return False
    valor57 = float(total57.iloc[0])

    conceptos = df54["CONCEPTO"].astype(str).apply(_norm)
    # Solo la línea PASIVO "RESERVAS TÉCNICAS" (no "BIENES APTOS... REPRESENTACIÓN... RESERVAS TÉCNICAS")
    idx_rt = conceptos == "RESERVAS TECNICAS"
    if not idx_rt.any():
        idx_rt = conceptos.str.strip() == "RESERVAS TECNICAS"
    if not idx_rt.any():
        print("[ERROR] Cuadro 54: no se encontró RESERVAS TÉCNICAS (pasivo).")
        return False
    valor54 = float(df54.loc[idx_rt, "MONTO"].iloc[0])

    diff = abs(valor57 - valor54)
    ok = diff <= TOLERANCIA
    print("")
    print("  Cruce Cuadro 57 (TOTAL reservas) vs Cuadro 54 (RESERVAS TÉCNICAS)")
    print("  Cuadro 57 TOTAL_RESERVAS = {:.2f}".format(valor57))
    print("  Cuadro 54 RESERVAS TÉCNICAS = {:.2f}".format(valor54))
    print("  Diferencia = {:.2f}  {}".format(diff, "OK" if ok else "FAIL"))
    print("")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_verificacion() else 1)
