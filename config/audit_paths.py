"""Rutas y nombres de la estructura espejo para auditoría (sin DB)."""
from pathlib import Path

from config.settings import (
    DATA_AUDIT,
    DATA_AUDIT_MIRROR,
    DATA_AUDIT_BY_SOURCE,
    DATA_AUDIT_MANIFEST,
)

# Subcarpetas del espejo (una por tabla lógica)
MIRROR_ENTITIES = DATA_AUDIT_MIRROR / "entities"
MIRROR_PRIMAS = DATA_AUDIT_MIRROR / "primas_mensuales"
MIRROR_EXCHANGE_RATES = DATA_AUDIT_MIRROR / "exchange_rates"
MIRROR_MARGEN_SOLVENCIA = DATA_AUDIT_MIRROR / "margen_solvencia"
MIRROR_SERIES_HISTORICAS = DATA_AUDIT_MIRROR / "series_historicas"

# Archivos consolidados por tabla (salida del arqueo)
MIRROR_ENTITIES_CSV = MIRROR_ENTITIES / "entities.csv"
MIRROR_PRIMAS_CSV = MIRROR_PRIMAS / "primas_mensuales.csv"
MIRROR_EXCHANGE_CSV = MIRROR_EXCHANGE_RATES / "exchange_rates.csv"
MIRROR_MARGEN_CSV = MIRROR_MARGEN_SOLVENCIA / "margen_solvencia.csv"
MIRROR_SERIES_CSV = MIRROR_SERIES_HISTORICAS / "series_historicas.csv"

# Manifest: índice de extracciones (origen -> qué se generó)
MANIFEST_INDEX_JSON = DATA_AUDIT_MANIFEST / "index.json"
MANIFEST_LINKS_CSV = DATA_AUDIT_MANIFEST / "descargas.csv"

# Crudo: texto completo de PDFs (nativo o OCR)
DATA_AUDIT_RAW_PDF_TEXT = DATA_AUDIT_BY_SOURCE / "pdf_text"


def ensure_mirror_dirs() -> None:
    """Crea todas las carpetas del espejo si no existen."""
    for d in (
        MIRROR_ENTITIES,
        MIRROR_PRIMAS,
        MIRROR_EXCHANGE_RATES,
        MIRROR_MARGEN_SOLVENCIA,
        MIRROR_SERIES_HISTORICAS,
        DATA_AUDIT_BY_SOURCE,
        DATA_AUDIT_RAW_PDF_TEXT,
        DATA_AUDIT_MANIFEST,
    ):
        d.mkdir(parents=True, exist_ok=True)
