# config/settings.py
"""Configuración central del proyecto SUDEASEG Dashboard."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# En Streamlit Community Cloud, los secrets se inyectan vía st.secrets (no .env).
# Copiamos a os.environ para que el resto del código siga usando getenv().
try:
    import streamlit as _st
    if getattr(_st, "secrets", None) and _st.secrets:
        for _k in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_DB_URL", "REQUIRE_AUTH"):
            if _k in _st.secrets:
                os.environ.setdefault(_k, str(_st.secrets[_k]))
except Exception:
    pass

# Rutas
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
# Compilación escalable por año: staged = una salida por archivo fuente; clean = compilado por año
DATA_STAGED = BASE_DIR / "data" / "staged"
DATA_CLEAN = BASE_DIR / "data" / "clean"

# Estructura espejo para auditoría (sin tocar la base de datos hasta validar)
# Refleja tablas: entities, primas_mensuales, exchange_rates, margen_solvencia, series_historicas
DATA_AUDIT = BASE_DIR / "data" / "audit"
DATA_AUDIT_MIRROR = DATA_AUDIT / "mirror"  # CSV/Parquet por tabla (legacy; ver DATA_REPLICA)
DATA_AUDIT_BY_SOURCE = DATA_AUDIT / "by_source"  # Extracciones por archivo origen (trazabilidad)
DATA_AUDIT_MANIFEST = DATA_AUDIT / "manifest"  # Índice de qué se extrajo de cada descarga

# Réplica local de la base de datos: mismo esquema que Supabase, para auditar antes de subir
# Contiene: entities, primas_mensuales, exchange_rates, margen_solvencia, series_historicas
DATA_REPLICA = BASE_DIR / "data" / "replica_db"

# Base de datos del anuario "Seguro en Cifras": SQLite local y DDL para Supabase (schema anuario)
DATA_DB = BASE_DIR / "data" / "db"
DATA_DB_LOCAL = DATA_DB / "local"  # anuario.db + manifest_carga.json
DATA_DB_SCHEMA = DATA_DB / "schema"  # SQL PostgreSQL para Supabase

# SUDEASEG - URLs base y subpáginas para buscar PDF/XLSX
SUDEASEG_BASE_URL = os.getenv("SUDEASEG_BASE_URL", "https://www.sudeaseg.gob.ve")
SUDEASEG_ESTADISTICAS_PATH = "/estadisticas"
# Subpáginas bajo estadísticas donde suelen estar los enlaces (ajustar si el portal cambia)
SUDEASEG_CRAWL_PATHS = [
    "/estadisticas",
    "/estadisticas/cifras-mensuales",
    "/estadisticas/boletin-en-cifras",
    "/estadisticas/cifras-anuales",
    "/estadisticas/margen-de-solvencia",
]
# Anuarios: página que suele listar publicaciones desde años históricos (ej. 1967+)
SUDEASEG_ANUARIOS_PATH = "/estadisticas/cifras-anuales"
# Año mínimo para considerar "anuario" en nombres de archivo/url
ANUARIO_YEAR_MIN = 1967

# BCV / Tasas de cambio
BCV_URL = os.getenv("BCV_URL", "https://www.bcv.org.ve")
DOLAR_API_BASE = os.getenv("DOLAR_API_BASE", "https://api.dolarapi.com")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
# Clave con privilegios de escritura (INSERT/DELETE). Usar para ETL; no exponer en front.
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
# Opcional: URI de conexión directa a PostgreSQL (para ejecutar migraciones). Dashboard → Settings → Database → Connection string (URI)
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")

# ETL: depuración por año (dejar vacío o 0 para procesar todos los años)
ETL_TARGET_YEAR = os.getenv("ETL_TARGET_YEAR", "")
try:
    ETL_TARGET_YEAR = int(ETL_TARGET_YEAR) if ETL_TARGET_YEAR and ETL_TARGET_YEAR != "0" else None
except ValueError:
    ETL_TARGET_YEAR = None
# ETL: modo depuración (verbose: listar archivos, año detectado, filas por archivo)
ETL_DEBUG = os.getenv("ETL_DEBUG", "false").lower() in ("1", "true", "yes")

# Scraping
REQUEST_DELAY_MIN = float(os.getenv("REQUEST_DELAY_MIN", "1"))
REQUEST_DELAY_MAX = float(os.getenv("REQUEST_DELAY_MAX", "3"))
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (compatible; SUDEASEG-DataPipeline/1.0; +https://github.com/sudeaseg-dashboard)",
)

# Crear directorios si no existen
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
DATA_AUDIT.mkdir(parents=True, exist_ok=True)
DATA_AUDIT_MIRROR.mkdir(parents=True, exist_ok=True)
DATA_AUDIT_BY_SOURCE.mkdir(parents=True, exist_ok=True)
DATA_AUDIT_MANIFEST.mkdir(parents=True, exist_ok=True)
DATA_STAGED.mkdir(parents=True, exist_ok=True)
DATA_CLEAN.mkdir(parents=True, exist_ok=True)
DATA_REPLICA.mkdir(parents=True, exist_ok=True)
DATA_DB.mkdir(parents=True, exist_ok=True)
DATA_DB_LOCAL.mkdir(parents=True, exist_ok=True)
DATA_DB_SCHEMA.mkdir(parents=True, exist_ok=True)
