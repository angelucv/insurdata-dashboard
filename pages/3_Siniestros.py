# pages/2_Siniestros.py — Anuario: Siniestros (por ramo, por empresa, 8-A/8-B/8-C)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.app.components.data_loader import load_anuario_siniestros_por_ramo, load_anuario_siniestros_por_ramo_empresa
from src.app.anuario_config import APP_NAME, estilizar_df_numeros, render_sidebar_footer

st.set_page_config(page_title=f"Siniestros | {APP_NAME}", page_icon="📉", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="anuario_anio")
render_sidebar_footer()

st.title("Siniestros")
st.caption("Cuadros 6, 7, 8-A, 8-B, 8-C — Por ramo, por empresa, por tipo. **Unidad:** miles de bolívares.")

df_ramo = load_anuario_siniestros_por_ramo(anio=anio)
df_empresa = load_anuario_siniestros_por_ramo_empresa(anio=anio)

if df_ramo.empty and df_empresa.empty:
    st.info("Ejecute el ETL para cargar siniestros. Para Cuadro 7 ejecute antes la migración 007 en Supabase.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Por ramo (6)", "Por ramo y empresa (7)", "Personas / Patrimoniales / Obligacionales (8-A, 8-B, 8-C)", "Referencia"])

with tab1:
    st.markdown("**Cuadro 6:** siniestros pagados por ramo.")
    sub6 = df_ramo[df_ramo["cuadro_id"] == "6"]
    if sub6.empty:
        st.info("No hay datos de siniestros por ramo (Cuadro 6). Ejecute el ETL.")
    else:
        try:
            if "datos" in sub6.columns and sub6["datos"].notna().any():
                expand = pd.json_normalize(sub6["datos"])
                display = pd.concat([sub6[["concepto_ramo"]].reset_index(drop=True), expand], axis=1)
            else:
                display = sub6[["concepto_ramo"]].copy()
            cols_num = [c for c in display.columns if c != "concepto_ramo"]
            for c in cols_num:
                display[c] = pd.to_numeric(display[c], errors="coerce")
            col_tot = "TOTAL" if "TOTAL" in display.columns else (cols_num[0] if cols_num else None)
            if col_tot and col_tot in display.columns:
                vals = pd.to_numeric(display[col_tot], errors="coerce")
                df_funnel_s6 = display.assign(_val=vals)[vals.notna() & (vals > 0)].head(12)
                if not df_funnel_s6.empty:
                    import plotly.express as px
                    fig_funnel = px.funnel(df_funnel_s6, x="_val", y="concepto_ramo", title="Siniestros por ramo (Cuadro 6 — Funnel)")
                    fig_funnel.update_layout(margin=dict(t=40, b=80), height=420, xaxis_title="Total (miles Bs.)", yaxis_title="", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_funnel, use_container_width=True)
            st.dataframe(estilizar_df_numeros(display, cols_num, 0), use_container_width=True, hide_index=True)
        except Exception:
            st.dataframe(sub6[["concepto_ramo", "cuadro_id"]], use_container_width=True, hide_index=True)

with tab2:
    st.markdown("**Cuadro 7:** siniestros por ramo y empresa.")
    if not df_empresa.empty:
        if "datos" in df_empresa.columns and df_empresa["datos"].notna().any():
            try:
                expanded = pd.json_normalize(df_empresa["datos"])
                display = pd.concat([df_empresa[["nombre_empresa"]], expanded], axis=1)
            except Exception:
                display = df_empresa[["nombre_empresa"]].copy()
        else:
            display = df_empresa[["nombre_empresa"]].copy()
        cols_num = [c for c in display.columns if c != "nombre_empresa"]
        for c in cols_num:
            display[c] = pd.to_numeric(display[c], errors="coerce")
        col_total = "TOTAL" if "TOTAL" in display.columns else next((c for c in cols_num if "total" in c.lower()), None)
        if col_total and display[col_total].notna().any():
            grupo_size = 10
            grupos = []
            for i in range(0, len(display), grupo_size):
                trozo = display.iloc[i : i + grupo_size]
                suma = trozo[col_total].sum()
                ini, fin = i + 1, min(i + grupo_size, len(display))
                etiqueta = f"Empresas {ini}-{fin}" if fin > ini else f"Empresa {ini}"
                grupos.append({"Grupo": etiqueta, "Total": suma})
            df_grupos = pd.DataFrame(grupos)
            if not df_grupos.empty and df_grupos["Total"].sum() > 0:
                fig_bar = go.Figure(data=[go.Bar(
                    x=df_grupos["Grupo"],
                    y=df_grupos["Total"],
                    marker=dict(color=df_grupos["Total"], colorscale="Reds", line=dict(color="white", width=1)),
                    text=df_grupos["Total"].apply(lambda x: f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")),
                    textposition="outside",
                )])
                fig_bar.update_layout(
                    title="Siniestros por grupo de empresas (cada barra = hasta 10 empresas)",
                    xaxis_title="Grupo",
                    yaxis_title="Total (miles Bs.)",
                    margin=dict(t=50, b=80),
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=360,
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        st.dataframe(estilizar_df_numeros(display, cols_num, 0), use_container_width=True, hide_index=True)

with tab3:
    st.markdown("**Cuadros 8-A** (Personas), **8-B** (Patrimoniales), **8-C** (Obligacionales) por ramo.")
    for cid, label in [("8-A", "8-A — Personas"), ("8-B", "8-B — Patrimoniales"), ("8-C", "8-C — Obligacionales")]:
        sub = df_ramo[df_ramo["cuadro_id"] == cid]
        if sub.empty:
            st.caption(f"{label}: sin datos. Ejecute el ETL.")
            continue
        st.subheader(label)
        try:
            if "datos" in sub.columns and sub["datos"].notna().any():
                expand = pd.json_normalize(sub["datos"])
                display = pd.concat([sub[["concepto_ramo"]].reset_index(drop=True), expand], axis=1)
            else:
                display = sub[["concepto_ramo"]].copy()
            cols_num = [c for c in display.columns if c != "concepto_ramo"]
            for c in cols_num:
                display[c] = pd.to_numeric(display[c], errors="coerce")
            st.dataframe(estilizar_df_numeros(display, cols_num, 0), use_container_width=True, hide_index=True)
        except Exception:
            st.dataframe(sub[["concepto_ramo"]], use_container_width=True, hide_index=True)
        st.markdown("---")

with tab4:
    st.markdown("""
    | Cuadro | Descripción |
    |--------|-------------|
    | 6 | Siniestros pagados por ramo |
    | 7 | Siniestros por ramo y empresa |
    | 8-A | Siniestros Personas por ramo |
    | 8-B | Siniestros Patrimoniales por ramo |
    | 8-C | Siniestros Obligacionales por ramo |
    """)
