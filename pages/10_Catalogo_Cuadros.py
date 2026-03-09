# pages/8_Catalogo_Cuadros.py — Anuario: Catálogo de cuadros (referencia)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.app.components.data_loader import load_anuario_cuadros
from src.app.anuario_config import APP_NAME, SECTORES, render_sidebar_footer

st.set_page_config(page_title=f"Catálogo de cuadros | {APP_NAME}", page_icon="📑", layout="wide")
st.sidebar.caption(APP_NAME)

st.title("Catálogo de cuadros")
st.caption("Referencia de todos los cuadros del anuario (3 a 58) con sector")

df = load_anuario_cuadros()
if df.empty:
    st.warning("No hay catálogo. Ejecute los DDL en Supabase (001_anuario_dimensiones.sql).")
    st.stop()

# Filtro por sector
sector_sel = st.sidebar.selectbox(
    "Filtrar por sector",
    options=["Todos"] + list(SECTORES.values()),
    index=0,
)
render_sidebar_footer()

if sector_sel != "Todos":
    rev = {v: k for k, v in SECTORES.items()}
    cod = rev.get(sector_sel)
    if cod and "sector" in df.columns:
        df = df[df["sector"] == cod]

st.metric("Cuadros en catálogo", len(df))
st.dataframe(df, use_container_width=True, hide_index=True)
