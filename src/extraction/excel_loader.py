# src/extraction/excel_loader.py
"""Carga y lectura inicial de archivos Excel de Cifras Mensuales SUDEASEG."""
from pathlib import Path

import pandas as pd


def load_sudeaseg_excel(
    path: str | Path,
    sheet_name: str | int | list = 0,
    header: int | list[int] | None = None,
) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """
    Carga archivo(s) Excel de SUDEASEG.
    - Si sheet_name es lista o 0, puede devolver múltiples hojas.
    - header=None permite que pandas infiera MultiIndex para luego aplanar en ETL.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if isinstance(sheet_name, list) or sheet_name is None:
        return pd.read_excel(path, sheet_name=sheet_name or None, header=header)
    try:
        return pd.read_excel(path, sheet_name=sheet_name, header=header)
    except Exception as e:
        print(f"[Excel] Error leyendo {path}: {e}")
        raise


def list_sheets(path: str | Path) -> list[str]:
    """Lista nombres de hojas de un archivo Excel."""
    return pd.ExcelFile(path).sheet_names
