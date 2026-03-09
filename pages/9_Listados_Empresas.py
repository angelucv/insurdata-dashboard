# pages/7_Listados_Empresas.py — Anuario: Listados de empresas autorizadas y Capital y garantía
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from src.app.components.data_loader import load_anuario_listados_empresas, load_anuario_capital_garantia_por_empresa
from src.app.anuario_config import APP_NAME, SECTORES, LISTADOS_CUADRO_POR_SECTOR, ORDEN_SECTORES, estilizar_df_numeros, render_sidebar_footer

st.set_page_config(page_title=f"Listados y empresas | {APP_NAME}", page_icon="🏢", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="anuario_anio")
render_sidebar_footer()

st.title("Listados de empresas autorizadas")
st.caption("Cuadro 1 = Empresas de seguros autorizadas (Empresas de Seguro). Cuadros 39, 46, 53 = Empresas de Reaseguro, Financiadoras de Primas, Medicina Prepagada.")

df = load_anuario_listados_empresas(anio=anio)

if df.empty:
    st.warning(f"No hay listados para el año {anio}. Ejecute el ETL para listados_empresas.")
else:
    sector_counts = df.groupby("cuadro_id").size()
    cols = st.columns(4)
    for i, (sector_id, cuadro_id) in enumerate(LISTADOS_CUADRO_POR_SECTOR.items()):
        with cols[i]:
            n = sector_counts.get(cuadro_id, 0)
            label = SECTORES.get(sector_id, sector_id)
            st.metric(f"Empresas — {label}", n)
    with cols[3]:
        st.metric("Total empresas listadas", len(df))

    st.markdown("---")
    st.subheader("Detalle por sector")

    sectores_listados = [s for s in ORDEN_SECTORES if s in LISTADOS_CUADRO_POR_SECTOR]
    tab_names = [SECTORES.get(s, s) for s in sectores_listados]
    tabs = st.tabs(tab_names)

    for i, sector_id in enumerate(sectores_listados):
        cuadro_id = LISTADOS_CUADRO_POR_SECTOR[sector_id]
        sub = df[df["cuadro_id"] == cuadro_id][["numero_orden", "nombre_empresa"]]
        with tabs[i]:
            if sector_id == "seguro_directo":
                st.caption("**Cuadro 1** — Empresas de seguros autorizadas (Empresas de Seguro).")
            if sub.empty:
                st.info(f"Sin datos para cuadro {cuadro_id}.")
            else:
                st.dataframe(sub, use_container_width=True, hide_index=True)

# --- Cuadro 2: Capital y garantía por empresa ---
st.markdown("---")
st.subheader("Capital y garantía por empresa (Cuadro 2)")
st.caption("Inscripción (número, año), Empresa, Capital Social Suscrito, Garantía en depósito: Operaciones de Seguros, Fideicomiso, Total.")

df_cg = load_anuario_capital_garantia_por_empresa(anio=anio)
if df_cg.empty:
    st.info("No hay datos de capital y garantía para este año. Ejecute el ETL cargando cuadro_02_capital_garantia_por_empresa.csv.")
else:
    display = df_cg[[
        "inscripcion_numero", "inscripcion_anio", "nombre_empresa",
        "capital_social_suscrito", "garantia_operaciones_seguros",
        "garantia_operaciones_fideicomiso", "garantia_total"
    ]].copy()
    display.columns = [
        "Inscripción Nº", "Inscripción Año", "Empresa",
        "Capital social suscrito", "Garantía operaciones seguros",
        "Garantía operaciones fideicomiso", "Total garantía"
    ]
    cols_num = ["Capital social suscrito", "Garantía operaciones seguros", "Garantía operaciones fideicomiso", "Total garantía"]
    for c in cols_num:
        display[c] = pd.to_numeric(display[c], errors="coerce")
    st.dataframe(estilizar_df_numeros(display, cols_num, 0), use_container_width=True, hide_index=True)
