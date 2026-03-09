"""
Revisión inicial de todos los Excel en data/raw de forma local:
lista archivos, hojas, columnas y conteo de filas por hoja.
No requiere base de datos. Útil para auditoría previa.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_RAW


def main():
    print("=== Revisión local de archivos Excel ===\n")
    print(f"Carpeta: {DATA_RAW}\n")
    files = sorted(DATA_RAW.rglob("*.xlsx")) + sorted(DATA_RAW.rglob("*.xls"))
    if not files:
        print("No se encontraron archivos .xlsx o .xls")
        return
    for path in files:
        rel = path.relative_to(DATA_RAW)
        print(f"--- {rel} ---")
        try:
            xl = pd.ExcelFile(path)
        except Exception as e:
            print(f"  Error abriendo: {e}")
            continue
        for sheet in xl.sheet_names:
            try:
                df = pd.read_excel(path, sheet_name=sheet, header=None)
            except Exception as e:
                print(f"  Hoja '{sheet}': error {e}")
                continue
            nrows, ncols = df.shape
            print(f"  Hoja '{sheet}': {nrows} filas x {ncols} columnas")
            if nrows > 0 and ncols > 0:
                sample = df.iloc[0].astype(str).tolist()[:6]
                print(f"    Primera fila (muestra): {sample}")
        print()
    print(f"Total archivos revisados: {len(files)}")


if __name__ == "__main__":
    main()
