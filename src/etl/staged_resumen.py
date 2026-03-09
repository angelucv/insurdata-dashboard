"""
Construcción de la tabla base de vaciado desde Resumen por empresa (Excel extract).
Estructura del Excel original: #, Empresas de Seguros, y 8 campos (1) a (8):
  (1) Primas Netas Cobradas, (2) Siniestros Pagados, (3) Reservas Brutas, (4) Reservas Netas,
  (5) Siniestros Totales (2+3), (6) Comisiones, (7) Gastos de Adquisición, (8) Gastos de Administración.
La información en cada pestaña es ACUMULADA (YTD) para (1),(2),(6),(7),(8); las reservas (3),(4)
y (5) se constituyen y liberan mes a mes (pueden subir o bajar). Una fila por (entidad, periodo).
Diciembre 2023 = 51 compañías + fila TOTAL (excluida).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config.settings import DATA_STAGED, DATA_AUDIT_BY_SOURCE
from src.etl.transformers import normalize_entity_name

MES_SHEET_TO_NUM = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

# Los 8 campos del resumen financiero (Excel original)
CAMPOS_EXCEL = [
    "primas_netas_ves",           # (1) Primas Netas Cobradas
    "siniestros_pagados_ves",     # (2) Siniestros Pagados (Netos de Salvamento)
    "reservas_brutas_ves",        # (3) Reservas para Prestaciones y Siniestros Pendientes Brutas
    "reservas_netas_ves",         # (4) Reservas Netas de Reaseguradores Inscritos
    "siniestros_totales_ves",     # (5) Siniestros Totales (2+3)
    "comisiones_ves",             # (6) Comisiones
    "gastos_adquisicion_ves",     # (7) Gastos de Adquisición
    "gastos_administracion_ves",  # (8) Gastos de Administración
]
# Para compatibilidad: gastos operativos = (6)+(7)+(8)
COLUMNAS_BASE = ["primas_netas_ves", "siniestros_pagados_ves", "gastos_operativos_ves"]

# Dimensión esperada: 51 compañías por mes (según tabla Diciembre 2023). Otros meses pueden variar.
ESPERADO_COMPANIAS_POR_MES = 51


def _find_column(df: pd.DataFrame, *keywords: str) -> str | None:
    """Devuelve la primera columna cuyo nombre contiene alguno de los keywords (case insensitive)."""
    for c in df.columns:
        c_low = str(c).lower()
        if any(kw in c_low for kw in keywords):
            return c
    return None


def _find_column_by_num(df: pd.DataFrame, num: int) -> str | None:
    """Busca columna que contenga '(num)' en el nombre (ej. (1), (2)... (8))."""
    needle = f"({num})"
    for c in df.columns:
        if needle in str(c):
            return c
    return None


def _parse_val(row: pd.Series, col: str | None, scale_thousands: bool = True) -> float | None:
    """Lee valor numérico de la fila; si scale_thousands y valor < 1e9, multiplica por 1000 (En Miles de Bs.)."""
    if not col or col not in row.index:
        return None
    try:
        v = float(row.get(col, 0) or 0)
    except (TypeError, ValueError):
        return None
    if scale_thousands and v < 1e9:
        v = v * 1000
    return round(v, 2)


def load_resumen_extract_csv(path: Path) -> pd.DataFrame:
    """
    Carga el CSV de by_source (resumen-por-empresa-YYYY_extract.csv) y devuelve
    un DataFrame con columnas: entity_normalized, entity_canonical, periodo, mes,
    y los 8 campos (1) a (8) del Excel, más gastos_operativos_ves = (6)+(7)+(8).
    Excluye la fila TOTAL.
    """
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if "_sheet" not in df.columns:
        raise ValueError("El CSV debe tener columna _sheet (nombre del mes).")
    col_empresa = _find_column(df, "empresa", "seguros")
    if not col_empresa:
        col_empresa = df.columns[2] if len(df.columns) > 2 else None
    # Mapeo de los 8 campos por número (1)..(8)
    cols_num = {}
    for i in range(1, 9):
        c = _find_column_by_num(df, i)
        if c:
            cols_num[i] = c
    if 1 not in cols_num:
        col_primas = _find_column(df, "primas", "netas", "cobradas")
        if col_primas:
            cols_num[1] = col_primas
    if not col_empresa or 1 not in cols_num:
        raise ValueError("No se encontraron columnas de empresa o (1) Primas Netas Cobradas.")

    m = re.search(r"20\d{2}", path.name)
    year = int(m.group(0)) if m else 2023

    # Columna # (1..51): solo filas de compañías; excluye TOTAL y filas de notas/leyendas
    col_num = _find_column(df, "#") or (df.columns[0] if len(df.columns) else None)
    def _row_es_compania(r: pd.Series) -> bool:
        if not col_num or col_num not in r.index:
            return True
        try:
            n = int(float(r.get(col_num)))
            return 1 <= n <= 100  # 51 en dic-2023; otros meses pueden variar
        except (TypeError, ValueError):
            return False

    rows = []
    for _, row in df.iterrows():
        if not _row_es_compania(row):
            continue
        emp = row.get(col_empresa)
        if pd.isna(emp) or not str(emp).strip():
            continue
        emp_str = str(emp).strip()
        if "total" in emp_str.lower() or emp_str.lower().startswith("total"):
            continue
        sheet = row.get("_sheet")
        if pd.isna(sheet):
            continue
        month_num = MES_SHEET_TO_NUM.get(str(sheet).strip().lower())
        if not month_num:
            continue
        periodo = f"{year}-{month_num:02d}-01"

        out = {
            "entity_normalized": normalize_entity_name(emp_str),
            "entity_canonical": emp_str,
            "periodo": periodo,
            "mes": month_num,
        }
        if not out["entity_normalized"] or out["entity_normalized"] == "_empty":
            continue

        for i, name in enumerate(CAMPOS_EXCEL, start=1):
            c = cols_num.get(i)
            out[name] = _parse_val(row, c)

        # Gastos operativos = (6) + (7) + (8)
        g6 = out.get("comisiones_ves")
        g7 = out.get("gastos_adquisicion_ves")
        g8 = out.get("gastos_administracion_ves")
        gastos = None
        if g6 is not None or g7 is not None or g8 is not None:
            gastos = (g6 or 0) + (g7 or 0) + (g8 or 0)
        out["gastos_operativos_ves"] = round(gastos, 2) if gastos is not None else None

        rows.append(out)
    return pd.DataFrame(rows)


def resumen_companias_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve un DataFrame con columnas: mes, n_companias.
    Útil para validar que cada mes tenga la dimensión esperada (ej. 51 compañías en diciembre).
    """
    if df.empty or "mes" not in df.columns:
        return pd.DataFrame(columns=["mes", "n_companias"])
    return df.groupby("mes", as_index=False).agg(n_companias=("entity_normalized", "nunique"))


def build_staged_resumen_2023(
    by_source_dir: Path | None = None,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """
    Construye la tabla base de vaciado para 2023 desde resumen-por-empresa-2023_extract.csv
    y la guarda en data/staged/2023/resumen_por_empresa_2023_base.csv.
    """
    by_source_dir = by_source_dir or DATA_AUDIT_BY_SOURCE
    output_dir = output_dir or (DATA_STAGED / "2023")
    output_dir.mkdir(parents=True, exist_ok=True)

    path = by_source_dir / "resumen-por-empresa-2023_extract.csv"
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}. Ejecuta antes el pipeline de auditoría para generar el extract.")
    df = load_resumen_extract_csv(path)
    out_path = output_dir / "resumen_por_empresa_2023_base.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    # Validación de dimensión: compañías por mes (esperado 51 en diciembre)
    resumen_mes = resumen_companias_por_mes(df)
    resumen_mes.to_csv(output_dir / "resumen_companias_por_mes.csv", index=False, encoding="utf-8-sig")
    return df
