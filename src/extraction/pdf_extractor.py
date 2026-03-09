# src/extraction/pdf_extractor.py
"""Extracción de tablas desde PDF (Camelot + pdfplumber + OCR para escaneados)."""
from pathlib import Path
from typing import Literal

import pandas as pd

try:
    import camelot
except ImportError:
    camelot = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from .pdf_ocr import is_likely_scanned, extract_text_ocr, extract_tables_from_ocr_text
except ImportError:
    is_likely_scanned = None
    extract_text_ocr = None
    extract_tables_from_ocr_text = None


class PDFTableExtractor:
    """
    Extrae tablas de PDFs de boletines SUDEASEG.
    Usa Camelot (Lattice/Stream) y pdfplumber como respaldo.
    """

    def __init__(self, flavor: Literal["lattice", "stream"] = "lattice"):
        self.flavor = flavor
        self._camelot_ok = camelot is not None
        self._pdfplumber_ok = pdfplumber is not None

    def extract_with_camelot(self, pdf_path: Path, pages: str = "all") -> list[pd.DataFrame]:
        """Extrae tablas con Camelot. pages: 'all' o ej. '1-5'."""
        if not self._camelot_ok:
            return []
        try:
            tables = camelot.read_pdf(str(pdf_path), flavor=self.flavor, pages=pages)
            return [t.df for t in tables]
        except Exception as e:
            print(f"[PDF] Camelot error en {pdf_path}: {e}")
            return []

    def extract_with_pdfplumber(self, pdf_path: Path) -> list[pd.DataFrame]:
        """Extrae tablas con pdfplumber (bounding boxes)."""
        if not self._pdfplumber_ok:
            return []
        dfs = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables():
                        if table:
                            dfs.append(pd.DataFrame(table[1:], columns=table[0]))
        except Exception as e:
            print(f"[PDF] pdfplumber error en {pdf_path}: {e}")
        return dfs

    def extract(self, pdf_path: Path, pages: str = "all", use_ocr_if_scanned: bool = True) -> list[pd.DataFrame]:
        """
        Intenta Camelot primero; si no hay tablas o falla, usa pdfplumber.
        Si el PDF parece escaneado (poco texto nativo) y use_ocr_if_scanned, usa OCR y convierte a tablas.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return []
        tables = self.extract_with_camelot(pdf_path, pages)
        if not tables:
            tables = self.extract_with_pdfplumber(pdf_path)
        if not tables and use_ocr_if_scanned and is_likely_scanned and extract_text_ocr and extract_tables_from_ocr_text:
            if is_likely_scanned(pdf_path):
                text = extract_text_ocr(pdf_path)
                raw_tables = extract_tables_from_ocr_text(text)
                for raw in raw_tables:
                    if len(raw) < 2:
                        if len(raw) == 1 and raw[0]:
                            tables.append(pd.DataFrame([raw[0]]))
                        continue
                    try:
                        df = pd.DataFrame(raw[1:], columns=raw[0] if len(raw[0]) == len(raw[1]) else None)
                        if df.empty or (df.columns is None and len(raw) >= 1):
                            df = pd.DataFrame(raw)
                        if not df.empty:
                            tables.append(df)
                    except Exception:
                        try:
                            tables.append(pd.DataFrame(raw))
                        except Exception:
                            pass
        return tables

    def extract_first_table(self, pdf_path: Path) -> pd.DataFrame | None:
        """Devuelve la primera tabla extraída o None."""
        tables = self.extract(pdf_path)
        return tables[0] if tables else None
