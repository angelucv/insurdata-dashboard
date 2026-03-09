# src/app/components/data_loader.py
"""Carga de datos para el dashboard: Supabase o CSV/Parquet local con caché."""
from pathlib import Path

import pandas as pd
import streamlit as st

from config.settings import DATA_PROCESSED, SUPABASE_URL, SUPABASE_KEY


@st.cache_data(ttl=3600)
def load_primas_from_supabase() -> pd.DataFrame:
    """Carga tabla primas_mensuales desde Supabase (cache 1h). Pagina para traer todos los registros."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return pd.DataFrame()
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        all_data = []
        offset = 0
        page_size = 1000
        while True:
            r = sb.table("primas_mensuales").select("*").range(offset, offset + page_size - 1).execute()
            chunk = r.data or []
            if not chunk:
                break
            all_data.extend(chunk)
            if len(chunk) < page_size:
                break
            offset += page_size
        df = pd.DataFrame(all_data)
        # Asegurar tipos numéricos para que la vista muestre valores
        for c in ["primas_netas_ves", "primas_netas_usd", "siniestros_pagados_ves", "siniestros_pagados_usd", "gastos_operativos_ves", "gastos_operativos_usd"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except Exception as e:
        st.warning(f"No se pudo cargar desde Supabase: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_entities_from_supabase() -> pd.DataFrame:
    """Carga catálogo de entidades desde Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return pd.DataFrame()
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        r = sb.table("entities").select("*").execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_series_from_supabase() -> pd.DataFrame:
    """Carga series_historicas para KPIs."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return pd.DataFrame()
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        r = sb.table("series_historicas").select("*").execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


def load_primas_fallback_local() -> pd.DataFrame:
    """Carga desde data/processed si existe (fallback sin Supabase)."""
    for name in ("primas_mensuales", "primas", "metricas"):
        p = DATA_PROCESSED / f"{name}.parquet"
        if p.exists():
            return pd.read_parquet(p)
    return pd.DataFrame()


def get_primas_df() -> pd.DataFrame:
    """Obtiene DataFrame de primas: Supabase o archivo local."""
    df = load_primas_from_supabase()
    if df.empty:
        df = load_primas_fallback_local()
    return df


# --- Anuario "Seguro en Cifras" (schema anuario en Supabase) ---


@st.cache_data(ttl=3600)
def load_anuario_cuadros() -> pd.DataFrame:
    """Catálogo de cuadros del anuario (anuario.cuadros)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        r = sb.table("cuadros").select("*").execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_anuario_balances_condensados(anio: int | None = None) -> pd.DataFrame:
    """Balances condensados por sector/cuadro (anuario.balances_condensados)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("balances_condensados").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_listados_empresas(anio: int | None = None) -> pd.DataFrame:
    """Listados de empresas por sector (anuario.listados_empresas). TTL 5 min para que tras ETL se vean los datos actualizados."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("listados_empresas").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_anuario_capital_garantia_por_empresa(anio: int | None = None) -> pd.DataFrame:
    """Capital y garantía por empresa (anuario.capital_garantia_por_empresa, Cuadro 2)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("capital_garantia_por_empresa").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_primas_por_ramo(anio: int | None = None) -> pd.DataFrame:
    """Primas por ramo (anuario.primas_por_ramo, cuadros 3, 5-A, 5-B, 5-C)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("primas_por_ramo").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_primas_por_ramo_empresa(anio: int | None = None) -> pd.DataFrame:
    """Primas por ramo y empresa (anuario.primas_por_ramo_empresa, cuadro 4)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("primas_por_ramo_empresa").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_siniestros_por_ramo(anio: int | None = None) -> pd.DataFrame:
    """Siniestros por ramo (anuario.siniestros_por_ramo, cuadros 6, 8-A, 8-B, 8-C)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("siniestros_por_ramo").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_siniestros_por_ramo_empresa(anio: int | None = None) -> pd.DataFrame:
    """Siniestros por ramo y empresa (anuario.siniestros_por_ramo_empresa, cuadro 7)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("siniestros_por_ramo_empresa").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_reservas_tecnicas_agregado(anio: int | None = None) -> pd.DataFrame:
    """Reservas técnicas agregado (anuario.reservas_tecnicas_agregado, cuadro 9)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("reservas_tecnicas_agregado").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_reservas_prima_por_ramo(anio: int | None = None) -> pd.DataFrame:
    """Reservas de prima por ramo (anuario.reservas_prima_por_ramo, cuadro 10)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("reservas_prima_por_ramo").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_reservas_prestaciones_por_ramo(anio: int | None = None) -> pd.DataFrame:
    """Reservas prestaciones/siniestros por ramo (anuario.reservas_prestaciones_por_ramo, cuadro 15)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("reservas_prestaciones_por_ramo").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_estados_ingresos_egresos(anio: int | None = None) -> pd.DataFrame:
    """Estados de ingresos y egresos por sector (anuario.estados_ingresos_egresos, cuadros 25-A/B, 41-A/B, 48, 55-A/B)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("estados_ingresos_egresos").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_reservas_prima_por_empresa(anio: int | None = None) -> pd.DataFrame:
    """Reservas de prima por empresa (anuario.reservas_prima_por_empresa, cuadros 11, 12, 13, 14)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("reservas_prima_por_empresa").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_reservas_prestaciones_por_empresa(anio: int | None = None) -> pd.DataFrame:
    """Reservas de prestaciones por empresa (anuario.reservas_prestaciones_por_empresa, cuadros 16, 17, 18, 19)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("reservas_prestaciones_por_empresa").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_indicadores_financieros_empresa(anio: int | None = None) -> pd.DataFrame:
    """Indicadores financieros por empresa (anuario.indicadores_financieros_empresa, cuadros 29, 44, 52, 58)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("indicadores_financieros_empresa").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_suficiencia_patrimonio(anio: int | None = None) -> pd.DataFrame:
    """Suficiencia patrimonio (anuario.suficiencia_patrimonio, cuadros 30, 45)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("suficiencia_patrimonio").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_series_historicas_primas(anio: int | None = None) -> pd.DataFrame:
    """Series históricas primas (anuario.series_historicas_primas, cuadros 31-A, 31-B)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("series_historicas_primas").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_gastos_vs_primas(anio: int | None = None) -> pd.DataFrame:
    """Gastos vs primas (anuario.gastos_vs_primas, cuadros 22, 23)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("gastos_vs_primas").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_datos_por_empresa(anio: int | None = None) -> pd.DataFrame:
    """Datos por empresa (anuario.datos_por_empresa, cuadros 27, 28, 34-36, 49-51, 56, 57)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("datos_por_empresa").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_cantidad_polizas_siniestros(anio: int | None = None) -> pd.DataFrame:
    """Cantidad pólizas y siniestros (anuario.cantidad_polizas_siniestros, cuadros 37, 38)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("cantidad_polizas_siniestros").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_anuario_gestion_general(anio: int | None = None) -> pd.DataFrame:
    """Gestión general (anuario.gestion_general, cuadro 26)."""
    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
        if sb is None:
            return pd.DataFrame()
        q = sb.table("gestion_general").select("*")
        if anio is not None:
            q = q.eq("anio", anio)
        r = q.execute()
        return pd.DataFrame(r.data or [])
    except Exception:
        return pd.DataFrame()
