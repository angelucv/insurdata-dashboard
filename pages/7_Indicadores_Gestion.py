# pages/6_Indicadores_Gestion.py — Anuario: Indicadores, gestión, suficiencia, series, gastos
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from src.app.components.data_loader import (
    load_anuario_gestion_general,
    load_anuario_indicadores_financieros_empresa,
    load_anuario_suficiencia_patrimonio,
    load_anuario_series_historicas_primas,
    load_anuario_gastos_vs_primas,
    load_anuario_datos_por_empresa,
    load_anuario_cantidad_polizas_siniestros,
)
from src.app.anuario_config import APP_NAME, estilizar_df_numeros, render_sidebar_footer

st.set_page_config(page_title=f"Indicadores y gestión | {APP_NAME}", page_icon="📌", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="anuario_anio")
render_sidebar_footer()

st.title("Indicadores y gestión")
st.caption("Gestión general, indicadores por empresa, suficiencia patrimonio, series históricas, gastos vs primas. **Unidad:** miles de bolívares.")
st.markdown(
    "Este módulo reúne indicadores que ayudan a interpretar la **gestión** de las entidades aseguradoras: "
    "producto de inversiones, indicadores financieros por empresa, suficiencia patrimonial, series históricas de primas, "
    "relación gastos/primas y otros datos por compañía. Sirve como puente entre las cifras agregadas del anuario y "
    "la lectura más detallada que se plantea para futuros demos por empresa."
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Gestión general (26)",
    "Indicadores financieros por empresa (29, 44, 52, 58)",
    "Suficiencia patrimonio (30, 45)",
    "Series históricas primas (31-A, 31-B)",
    "Gastos vs primas (22, 23, 23-A a 23-F)",
    "Datos por empresa (27, 28, 34-36, 49-51, 56, 57)",
    "Cantidad pólizas y siniestros (37, 38)",
])

with tab1:
    st.markdown("**Cuadro 26** — Gestión general (producto de inversiones, intereses, etc.).")
    df_gestion = load_anuario_gestion_general(anio=anio)
    if df_gestion.empty:
        st.info(
            "En esta instancia no hay datos de gestión general para el año seleccionado. "
            "En la versión completa del proyecto, esta vista se alimenta del Cuadro 26 del anuario «Seguro en Cifras»."
        )
    else:
        df_gestion["monto"] = pd.to_numeric(df_gestion["monto"], errors="coerce")
        disp = df_gestion[["concepto", "monto"]].copy()
        st.dataframe(estilizar_df_numeros(disp, ["monto"], 0), use_container_width=True, hide_index=True)

with tab2:
    st.markdown("**Indicadores financieros por empresa** (cuadros 29, 44, 52, 58).")
    df_ind = load_anuario_indicadores_financieros_empresa(anio=anio)
    if df_ind.empty:
        st.caption(
            "En esta instancia no hay datos de indicadores financieros por empresa para el año seleccionado. "
            "En la versión completa del proyecto, esta vista se alimenta de los cuadros 29, 44, 52 y 58 del anuario."
        )
    else:
        for cuadro_id, label in [
            ("29", "Cuadro 29 — Empresas de Seguro"),
            ("44", "Cuadro 44 — Empresas de Reaseguro"),
            ("52", "Cuadro 52 — Financiadoras de Primas"),
            ("58", "Cuadro 58 — Medicina Prepagada"),
        ]:
            sub = df_ind[df_ind["cuadro_id"] == cuadro_id]
            if sub.empty:
                continue
            with st.expander(label, expanded=(cuadro_id == "29")):
                try:
                    if "datos" in sub.columns and sub["datos"].notna().any():
                        d = sub["datos"].dropna()
                        if len(d) > 0 and isinstance(d.iloc[0], dict):
                            expand = pd.json_normalize(d.tolist())
                            display = pd.concat([sub.loc[d.index, ["nombre_empresa"]].reset_index(drop=True), expand.reset_index(drop=True)], axis=1)
                        else:
                            display = sub[["nombre_empresa"]].copy()
                    else:
                        display = sub[["nombre_empresa"]].copy()
                    cols_num = [c for c in display.columns if c != "nombre_empresa"]
                    for c in cols_num:
                        display[c] = pd.to_numeric(display[c], errors="coerce")
                    st.dataframe(estilizar_df_numeros(display, cols_num, 2), use_container_width=True, hide_index=True)
                except Exception:
                    st.dataframe(sub[["nombre_empresa", "datos"]], use_container_width=True, hide_index=True)
def _tabla_desde_nombre_datos(df_sub, nombre_col="nombre_empresa"):
    """Muestra tabla expandiendo columna datos (JSONB) a columnas."""
    if df_sub.empty:
        return
    try:
        if "datos" in df_sub.columns and df_sub["datos"].notna().any():
            d = df_sub["datos"].dropna()
            if len(d) > 0 and isinstance(d.iloc[0], dict):
                expand = pd.json_normalize(d.tolist())
                display = pd.concat([df_sub.loc[d.index, [nombre_col]].reset_index(drop=True), expand.reset_index(drop=True)], axis=1)
            else:
                display = df_sub[[nombre_col]].copy()
        else:
            display = df_sub[[nombre_col]].copy()
        cols_num = [c for c in display.columns if c != nombre_col]
        for c in cols_num:
            display[c] = pd.to_numeric(display[c], errors="coerce")
        st.dataframe(estilizar_df_numeros(display, cols_num, 2), use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(df_sub, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("**Suficiencia patrimonio** (cuadros 30, 45).")
    df_suf = load_anuario_suficiencia_patrimonio(anio=anio)
    if df_suf.empty:
        st.caption(
            "En esta instancia no hay datos de suficiencia patrimonial para el año seleccionado. "
            "En la versión completa del proyecto, esta vista se alimenta de los cuadros 30 y 45 del anuario."
        )
    else:
        for cid, label in [("30", "Cuadro 30 — Empresas de Seguro"), ("45", "Cuadro 45 — Empresas de Reaseguro")]:
            sub = df_suf[df_suf["cuadro_id"] == cid]
            if sub.empty:
                continue
            with st.expander(label, expanded=(cid == "30")):
                _tabla_desde_nombre_datos(sub)

with tab4:
    st.markdown("**Series históricas primas** (cuadros 31-A, 31-B).")
    df_series = load_anuario_series_historicas_primas(anio=anio)
    if df_series.empty:
        st.caption(
            "En esta instancia no hay series históricas de primas cargadas para el año seleccionado. "
            "En la versión completa del proyecto, esta vista se alimenta de los cuadros 31-A y 31-B."
        )
    else:
        for cid, label in [("31-A", "Cuadro 31-A — Primas netas 2023 vs 2022"), ("31-B", "Cuadro 31-B — Primas/prestaciones 1990-2023")]:
            sub = df_series[df_series["cuadro_id"] == cid]
            if sub.empty:
                continue
            with st.expander(label, expanded=(cid == "31-A")):
                try:
                    if "datos" in sub.columns and sub["datos"].notna().any():
                        d = sub["datos"].dropna()
                        if len(d) > 0 and isinstance(d.iloc[0], dict):
                            display = pd.json_normalize(d.tolist())
                            cols_num = [c for c in display.columns]
                            for c in cols_num:
                                display[c] = pd.to_numeric(display[c], errors="coerce")
                            st.dataframe(estilizar_df_numeros(display, cols_num, 2), use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(sub, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(sub, use_container_width=True, hide_index=True)
                except Exception:
                    st.dataframe(sub, use_container_width=True, hide_index=True)

with tab5:
    st.markdown("**Gastos vs primas** (cuadros 22, 23).")
    df_gastos = load_anuario_gastos_vs_primas(anio=anio)
    if df_gastos.empty:
        st.caption(
            "En esta instancia no hay datos de gastos vs primas para el año seleccionado. "
            "En la versión completa del proyecto, esta vista se alimenta de los cuadros 22 y 23 del anuario."
        )
    else:
        for cid, label in [("22", "Cuadro 22 — Gastos administración vs primas por empresa"), ("23", "Cuadro 23 — Gastos producción vs primas por ramo")]:
            sub = df_gastos[df_gastos["cuadro_id"] == cid]
            if sub.empty:
                continue
            with st.expander(label, expanded=(cid == "22")):
                try:
                    if "datos" in sub.columns and sub["datos"].notna().any():
                        d = sub["datos"].dropna()
                        if len(d) > 0 and isinstance(d.iloc[0], dict):
                            expand = pd.json_normalize(d.tolist())
                            display = pd.concat([sub.loc[d.index, ["concepto_ramo_o_empresa"]].reset_index(drop=True), expand.reset_index(drop=True)], axis=1)
                        else:
                            display = sub[["concepto_ramo_o_empresa"]].copy()
                    else:
                        display = sub[["concepto_ramo_o_empresa"]].copy()
                    cols_num = [c for c in display.columns if c != "concepto_ramo_o_empresa"]
                    for c in cols_num:
                        display[c] = pd.to_numeric(display[c], errors="coerce")
                    st.dataframe(estilizar_df_numeros(display, cols_num, 2), use_container_width=True, hide_index=True)
                except Exception:
                    st.dataframe(sub, use_container_width=True, hide_index=True)

with tab6:
    st.markdown("**Datos por empresa** (cuadros 27, 28, 34-36, 49-51, 56, 57).")
    df_datos = load_anuario_datos_por_empresa(anio=anio)
    if df_datos.empty:
        st.caption(
            "En esta instancia no hay datos por empresa para el año seleccionado. "
            "En la versión completa del proyecto, esta vista se alimenta de los cuadros 27, 28, 34-36, 49-51, 56 y 57."
        )
    else:
        labels_cuadros = [
            ("27", "Cuadro 27 — Rentabilidad inversiones"), ("28", "Cuadro 28 — Resultados 2019-2023"),
            ("34", "Cuadro 34 — Primas brutas personas"), ("35", "Cuadro 35 — Devolución primas"),
            ("36", "Cuadro 36 — Reservas prestaciones pendientes"),
            ("49", "Cuadro 49 — Ingresos financiadoras"), ("50", "Cuadro 50 — Circulante activo financiadoras"),
            ("51", "Cuadro 51 — Gastos operativos financiadoras"),
            ("56", "Cuadro 56 — Ingresos netos medicina prepagada"), ("57", "Cuadro 57 — Reservas técnicas medicina prepagada"),
        ]
        for cid, label in labels_cuadros:
            sub = df_datos[df_datos["cuadro_id"] == cid]
            if sub.empty:
                continue
            with st.expander(label, expanded=False):
                _tabla_desde_nombre_datos(sub)

with tab7:
    st.markdown("**Cantidad pólizas y siniestros** (cuadros 37, 38).")
    df_pol = load_anuario_cantidad_polizas_siniestros(anio=anio)
    if df_pol.empty:
        st.caption(
            "En esta instancia no hay datos de cantidad de pólizas y siniestros para el año seleccionado. "
            "En la versión completa del proyecto, esta vista se alimenta de los cuadros 37 y 38 del anuario."
        )
    else:
        for cid, label in [("37", "Cuadro 37 — Por ramo"), ("38", "Cuadro 38 — Por empresa")]:
            sub = df_pol[df_pol["cuadro_id"] == cid]
            if sub.empty:
                continue
            with st.expander(label, expanded=(cid == "37")):
                disp = sub[["concepto_ramo_o_empresa", "polizas", "siniestros"]].copy()
                disp["polizas"] = pd.to_numeric(disp["polizas"], errors="coerce")
                disp["siniestros"] = pd.to_numeric(disp["siniestros"], errors="coerce")
                st.dataframe(estilizar_df_numeros(disp, ["polizas", "siniestros"], 0), use_container_width=True, hide_index=True)
