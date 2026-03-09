# pages/5_Estados_Resultado.py — Anuario: Estados de ingresos y egresos por sector
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from src.app.components.data_loader import load_anuario_estados_ingresos_egresos
from src.app.anuario_config import APP_NAME, SECTORES, estilizar_df_numeros, render_sidebar_footer

# Cuadros de estados por sector (ingresos + egresos)
ESTADOS_CUADROS_POR_SECTOR = {
    "seguro_directo": ["25-A", "25-B"],
    "reaseguro": ["41-A", "41-B"],
    "financiadoras_primas": ["48"],
    "medicina_prepagada": ["55-A", "55-B"],
}
ORDEN_SECTORES = ["seguro_directo", "reaseguro", "financiadoras_primas", "medicina_prepagada"]

st.set_page_config(page_title=f"Estados de resultado | {APP_NAME}", page_icon="📈", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="anuario_anio")
render_sidebar_footer()

st.title("Estados de resultado (ingresos y egresos)")
st.caption("Cuadros 25-A/B, 41-A/B, 48, 55-A/B — Por sector. **Unidad:** miles de bolívares.")

df = load_anuario_estados_ingresos_egresos(anio=anio)

if df.empty:
    st.info("No hay datos de estados de ingresos y egresos. Ejecute el ETL: `python scripts/etl_anuario_a_supabase.py --year 2023`.")
    st.stop()

tab_names = [SECTORES.get(s, s) for s in ORDEN_SECTORES]
tabs = st.tabs(tab_names)

for i, sector_id in enumerate(ORDEN_SECTORES):
    cuadros = ESTADOS_CUADROS_POR_SECTOR.get(sector_id, [])
    sub = df[df["cuadro_id"].isin(cuadros)].copy()
    with tabs[i]:
        if sub.empty:
            st.info(f"Sin datos para este sector (cuadros {', '.join(cuadros)}).")
            continue
        sub["monto"] = pd.to_numeric(sub["monto"], errors="coerce")
        disp = sub[["concepto", "monto", "tipo"]].copy()
        st.dataframe(estilizar_df_numeros(disp, ["monto"], 0), use_container_width=True, hide_index=True)
