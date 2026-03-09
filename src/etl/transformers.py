# src/etl/transformers.py
"""Transformaciones pandas: MultiIndex, nulos, normalización de texto, melt."""
import re
import unicodedata

import pandas as pd


def flatten_multiindex_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplana columnas MultiIndex concatenando niveles con guión bajo.
    Ej: (Trimestre I, Primas Netas) -> Trimestre_I_Primas_Netas
    """
    if not isinstance(df.columns, pd.MultiIndex):
        return df.copy()
    new_cols = []
    for col in df.columns:
        if isinstance(col, tuple):
            name = "_".join(str(c).strip().replace(" ", "_") for c in col if c)
        else:
            name = str(col)
        name = re.sub(r"_+", "_", name).strip("_") or "unnamed"
        new_cols.append(name)
    out = df.copy()
    out.columns = new_cols
    return out


def impute_nulls_financial(
    df: pd.DataFrame,
    fill_value: float = 0.0,
    drop_threshold: float = 0.95,
) -> pd.DataFrame:
    """
    Imputa nulos en columnas numéricas con fill_value.
    Elimina filas donde la proporción de nulos supera drop_threshold.
    """
    out = df.copy()
    numeric = out.select_dtypes(include=["number"])
    for c in numeric.columns:
        out[c] = out[c].fillna(fill_value)
    if drop_threshold < 1.0:
        null_ratio = out.isnull().mean(axis=1)
        out = out.loc[null_ratio < drop_threshold]
    return out


def normalize_entity_name(s: str) -> str:
    """
    Normaliza nombre de entidad: minúsculas, sin tildes, sin espacios extra,
    sin signos de puntuación problemáticos.
    """
    if pd.isna(s) or not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def melt_wide_to_long(
    df: pd.DataFrame,
    id_vars: list[str],
    value_vars: list[str] | None = None,
    var_name: str = "periodo",
    value_name: str = "valor",
) -> pd.DataFrame:
    """
    Transpone columnas de periodo (meses/años) a formato largo.
    id_vars: columnas que identifican la entidad (ej. empresa).
    value_vars: columnas numéricas por periodo; si None se infieren.
    """
    if value_vars is None:
        value_vars = [c for c in df.columns if c not in id_vars and df[c].dtype in ["float64", "int64"]]
    return pd.melt(
        df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=var_name,
        value_name=value_name,
    )
