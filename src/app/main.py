# src/app/main.py
"""Dashboard SUDEASEG - Punto de entrada Streamlit."""
import streamlit as st

from src.app.components.auth import check_auth_required, render_login_or_session, logout_button

st.set_page_config(
    page_title="SUDEASEG - Inteligencia del Sector Asegurador",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilo mínimo para aspecto profesional
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }
    h1 { color: #1e3a5f; }
    .stMetric { background: #f0f2f6; padding: 0.5rem 1rem; border-radius: 0.5rem; }
</style>
""", unsafe_allow_html=True)

if check_auth_required() and not render_login_or_session():
    st.stop()

logout_button()

st.sidebar.title("📊 SUDEASEG Dashboard")
st.sidebar.caption("Inteligencia de datos del sector asegurador venezolano")
st.sidebar.markdown("---")

st.title("Inteligencia de Datos del Sector Asegurador Venezolano")
st.caption("Superintendencia de la Actividad Aseguradora — Extracción, modelado y visualización")

# Las páginas en ./pages/ se listan automáticamente en el sidebar de Streamlit.

# Página principal: resumen rápido
from src.app.components.data_loader import get_primas_df

df = get_primas_df()
if df.empty:
    st.info(
        "No hay datos cargados. Ejecuta primero el pipeline de extracción y ETL, "
        "o configura Supabase con datos. Ver `scripts/run_extraction.py` y `scripts/run_etl.py`."
    )
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Registros cargados", len(df))
    with col2:
        if "periodo" in df.columns:
            st.metric("Periodos", df["periodo"].nunique())
    with col3:
        if "entity_id" in df.columns:
            st.metric("Entidades", df["entity_id"].nunique())
    st.markdown("---")
    st.subheader("Vista previa de datos")
    st.dataframe(df.head(100), use_container_width=True)
