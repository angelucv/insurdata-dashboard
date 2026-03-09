# pages/1_Primas.py — Anuario: Primas (por ramo, por empresa)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.app.components.data_loader import load_anuario_primas_por_ramo, load_anuario_primas_por_ramo_empresa
from src.app.anuario_config import (
    APP_NAME,
    estilizar_df_numeros,
    estilizar_primas_cuadro3_con_subtotales,
    SUBTOTALES_CUADRO_3,
    render_sidebar_footer,
    LAYOUT_PIE_MODERNO,
    PALETA_PIE_MODERNA,
)

st.set_page_config(page_title=f"Primas | {APP_NAME}", page_icon="💰", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="anuario_anio")
render_sidebar_footer()

st.title("Primas")
st.caption("Cuadros 3, 4, 5-A, 5-B, 5-C — Por ramo y por ramo y empresa. **Unidad:** miles de bolívares.")

df_ramo = load_anuario_primas_por_ramo(anio=anio)
df_empresa = load_anuario_primas_por_ramo_empresa(anio=anio)

if df_ramo.empty and df_empresa.empty:
    st.info("Ejecute el ETL para cargar primas: `python scripts/etl_anuario_a_supabase.py --year 2023`.")
    st.stop()

tab_ramo, tab_empresa, tab_ref = st.tabs(["Por ramo (3, 5-A, 5-B, 5-C)", "Por ramo y empresa (4)", "Referencia"])

with tab_ramo:
    if df_ramo.empty:
        st.info("No hay datos de primas por ramo. Ejecute el ETL.")
    else:
        # Totales por área (5-A, 5-B, 5-C) para gráfico general
        for c in ["total", "seguro_directo"]:
            if c in df_ramo.columns:
                df_ramo[c] = pd.to_numeric(df_ramo[c], errors="coerce")
        areas = {"5-A": "Personas", "5-B": "Patrimoniales", "5-C": "Obligacionales"}
        totales_area = {}
        for cid, label in areas.items():
            sub = df_ramo[df_ramo["cuadro_id"] == cid]
            if not sub.empty and "total" in sub.columns:
                totales_area[label] = sub["total"].sum()
            elif not sub.empty and "seguro_directo" in sub.columns:
                totales_area[label] = sub["seguro_directo"].sum()
            else:
                totales_area[label] = 0
        if any(totales_area.values()):
            st.subheader("Distribución por área (Personas, Patrimoniales, Obligacionales)")
            # Treemap: área -> ramo (detalle por ramos)
            areas_ids = {"5-A": "Personas", "5-B": "Patrimoniales", "5-C": "Obligacionales"}
            treemap_rows = []
            for cid, area_name in areas_ids.items():
                sub = df_ramo[df_ramo["cuadro_id"] == cid]
                if sub.empty or "total" not in sub.columns:
                    continue
                sub = sub.copy()
                sub["total"] = pd.to_numeric(sub["total"], errors="coerce")
                sub = sub[~sub["concepto_ramo"].astype(str).str.strip().str.upper().isin(SUBTOTALES_CUADRO_3)]
                sub = sub[sub["total"].notna() & (sub["total"] > 0)]
                for _, row in sub.iterrows():
                    nombre = str(row.get("concepto_ramo", "")).strip() or "Ramo"
                    treemap_rows.append({"Área": area_name, "Ramo": nombre[:35], "Total": float(row.get("total", 0))})
            if treemap_rows:
                df_treemap = pd.DataFrame(treemap_rows)
                fig_treemap = px.treemap(
                    df_treemap, path=["Área", "Ramo"], values="Total",
                    title="Primas por área y ramo (Treemap)",
                    color="Total", color_continuous_scale="Teal",
                )
                fig_treemap.update_layout(margin=dict(t=40, b=20), height=400, paper_bgcolor="rgba(0,0,0,0)")
                fig_treemap.update_traces(textinfo="label+value+percent parent")
                st.plotly_chart(fig_treemap, use_container_width=True)
        st.markdown("---")
        # Tablas: Cuadro 3 (general), luego 5-A, 5-B, 5-C
        cols_num = ["seguro_directo", "reaseguro_aceptado", "total", "pct"]
        df_3 = df_ramo[df_ramo["cuadro_id"] == "3"]
        if not df_3.empty:
            st.subheader("Cuadro 3 — Primas por ramo (general)")
            disp_3 = df_3[["concepto_ramo"] + [c for c in cols_num if c in df_3.columns]].copy()
            for c in cols_num:
                if c in disp_3.columns:
                    disp_3[c] = pd.to_numeric(disp_3[c], errors="coerce")
            # Gráfico de subtotales (Personas, Patrimoniales, Solidarios)
            sub_total = disp_3[disp_3["concepto_ramo"].str.strip().str.upper().isin(SUBTOTALES_CUADRO_3 - {"TOTAL"})]
            if not sub_total.empty and "total" in sub_total.columns:
                sub_pie = sub_total[["concepto_ramo", "total"]].dropna(subset=["total"]).query("total > 0")
                if not sub_pie.empty:
                    etiquetas = sub_pie["concepto_ramo"].replace({
                        "SEGURO DE PERSONAS": "Personas",
                        "SEGUROS PATRIMONIALES": "Patrimoniales",
                        "SEGUROS SOLIDARIOS": "Solidarios",
                    }, regex=False)
                    fig3 = go.Figure(data=[go.Pie(
                        values=sub_pie["total"],
                        labels=etiquetas,
                        hole=0.58,
                        marker=dict(
                            colors=[PALETA_PIE_MODERNA[i % len(PALETA_PIE_MODERNA)] for i in range(len(sub_pie))],
                            line=dict(color="white", width=1.8),
                        ),
                        textinfo="label+percent",
                        hoverinfo="label+value+percent",
                        pull=[0.01] * len(sub_pie),
                    )])
                    fig3.update_layout(**LAYOUT_PIE_MODERNO, title="Subtotales por tipo (Personas, Patrimoniales, Solidarios)", showlegend=True, height=360)
                    st.plotly_chart(fig3, use_container_width=True)
            st.dataframe(estilizar_primas_cuadro3_con_subtotales(disp_3, columnas_numericas=[c for c in cols_num if c in disp_3.columns], decimals=0), use_container_width=True, hide_index=True)
        st.markdown("---")
        for cid, label in [("5-A", "5-A — Personas"), ("5-B", "5-B — Patrimoniales"), ("5-C", "5-C — Obligacionales")]:
            sub = df_ramo[df_ramo["cuadro_id"] == cid]
            if sub.empty:
                continue
            st.subheader(label)
            disp = sub[["concepto_ramo"] + [c for c in cols_num if c in sub.columns]].copy()
            for c in cols_num:
                if c in disp.columns:
                    disp[c] = pd.to_numeric(disp[c], errors="coerce")
            st.dataframe(estilizar_df_numeros(disp, [c for c in cols_num if c in disp.columns], 0), use_container_width=True, hide_index=True)
            # Funnel por ramos (más legible que torta cuando hay muchos ramos)
            if "total" in disp.columns and disp["total"].sum() > 0:
                disp_fun = disp[["concepto_ramo", "total"]].dropna(subset=["total"]).query("total > 0").sort_values("total", ascending=False)
                if not disp_fun.empty:
                    fig_funnel_ramo = px.funnel(disp_fun, x="total", y="concepto_ramo", title=f"Ramos en {label} (Funnel)")
                    fig_funnel_ramo.update_layout(margin=dict(t=40, b=20), height=max(300, min(500, len(disp_fun) * 28)), xaxis_title="Total (miles Bs.)", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_funnel_ramo, use_container_width=True)
            st.markdown("---")

with tab_empresa:
    st.markdown("**Cuadro 4:** primas por ramo desglosadas por empresa.")
    if df_empresa.empty:
        st.info("No hay datos de primas por ramo y empresa. Ejecute el ETL.")
    else:
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
        # Gráfico por grupos de empresas (primeras 10, siguientes 10, etc.)
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
                    marker=dict(color=df_grupos["Total"], colorscale="Blues", line=dict(color="white", width=1)),
                    text=df_grupos["Total"].apply(lambda x: f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")),
                    textposition="outside",
                )])
                fig_bar.update_layout(
                    title="Primas por grupo de empresas (cada barra = hasta 10 empresas)",
                    xaxis_title="Grupo",
                    yaxis_title="Total (miles Bs.)",
                    margin=dict(t=50, b=80),
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=360,
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        st.dataframe(estilizar_df_numeros(display, cols_num, 0), use_container_width=True, hide_index=True)

with tab_ref:
    st.markdown("""
    | Cuadro | Descripción |
    |--------|-------------|
    | 3 | Primas por ramo (general) |
    | 4 | Primas por ramo y empresa |
    | 5-A | Primas Personas por ramo |
    | 5-B | Primas Patrimoniales por ramo |
    | 5-C | Primas Obligacionales por ramo |
    """)
