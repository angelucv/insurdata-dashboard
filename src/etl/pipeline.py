# src/etl/pipeline.py
"""Orquestación ETL: extracción -> normalización BCV -> transformación -> salida lista para BD."""
from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd

from config.settings import DATA_RAW, DATA_PROCESSED
from src.extraction.excel_loader import load_sudeaseg_excel
from src.extraction.pdf_extractor import PDFTableExtractor
from src.extraction.bcv_client import BCVClient
from .transformers import (
    flatten_multiindex_headers,
    impute_nulls_financial,
    normalize_entity_name,
    melt_wide_to_long,
)
from .entity_resolver import EntityResolver


class ETLPipeline:
    """
    Pipeline ETL unificado:
    1) Carga raw (Excel/PDF),
    2) Aplana headers, imputa nulos, normaliza entidades,
    3) Opcional: convierte VES -> USD con BCV,
    4) Exporta a CSV/Parquet para carga en Supabase.
    """

    def __init__(
        self,
        bcv_client: BCVClient | None = None,
        entity_resolver: EntityResolver | None = None,
        out_dir: Path | None = None,
    ):
        self.bcv = bcv_client or BCVClient()
        self.resolver = entity_resolver or EntityResolver()
        self.out_dir = out_dir or DATA_PROCESSED

    def process_excel(
        self,
        path: str | Path,
        sheet_name: str | int = 0,
        id_columns: list[str] | None = None,
        date_columns: list[str] | None = None,
        entity_column: str | None = None,
        normalize_currency: bool = False,
        currency_date_column: str | None = None,
    ) -> pd.DataFrame:
        """
        Carga Excel, aplana MultiIndex, imputa nulos, opcionalmente normaliza
        entidades y convierte columnas monetarias a USD.
        """
        raw = load_sudeaseg_excel(path, sheet_name=sheet_name)
        if isinstance(raw, dict):
            raw = raw.get(list(raw.keys())[0], pd.DataFrame())
        df = flatten_multiindex_headers(raw)
        df = impute_nulls_financial(df)

        if entity_column and entity_column in df.columns:
            df["entity_id"] = df[entity_column].map(self.resolver.resolve)

        if normalize_currency and currency_date_column:
            # Obtener tasa por fecha y dividir columnas numéricas
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if currency_date_column in df.columns:
                for idx, row in df.iterrows():
                    d = row.get(currency_date_column)
                    if hasattr(d, "date"):
                        d = d.date() if hasattr(d, "date") else d
                    if isinstance(d, date):
                        rate = self.bcv.get_rate_ves_usd(d)
                        if rate:
                            for c in numeric_cols:
                                if c != "entity_id":
                                    df.at[idx, c] = row[c] / rate if pd.notna(row[c]) else None

        return df

    def process_pdf_tables(self, pdf_path: str | Path) -> list[pd.DataFrame]:
        """Extrae tablas de un PDF y aplica limpieza básica."""
        extractor = PDFTableExtractor(flavor="lattice")
        tables = extractor.extract(Path(pdf_path))
        result = []
        for t in tables:
            t = flatten_multiindex_headers(t)
            t = impute_nulls_financial(t)
            result.append(t)
        return result

    def save_for_db(self, df: pd.DataFrame, name: str) -> Path:
        """Guarda DataFrame en processed/ para posterior carga en Supabase."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / f"{name}.parquet"
        df.to_parquet(path, index=False)
        return path
