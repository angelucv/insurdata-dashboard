# pages/3_Reservas.py — Anuario: Reservas (técnicas, prima, prestaciones, detalle, inversiones, hospitalización)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from src.app.components.data_loader import (
    load_anuario_reservas_tecnicas_agregado,
    load_anuario_reservas_prima_por_ramo,
    load_anuario_reservas_prestaciones_por_ramo,
    load_anuario_reservas_prima_por_empresa,
    load_anuario_reservas_prestaciones_por_empresa,
)
from src.app.anuario_config import APP_NAME, estilizar_df_numeros, render_sidebar_footer

st.set_page_config(page_title=f"Reservas | {APP_NAME}", page_icon="📋", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="anuario_anio")
render_sidebar_footer()

st.title("Reservas")
st.caption("Cuadros 9 a 21, 32, 33 — Técnicas, prima, prestaciones, detalle, inversiones, hospitalización. **Unidad:** miles de bolívares.")

df_tec = load_anuario_reservas_tecnicas_agregado(anio=anio)
df_prima = load_anuario_reservas_prima_por_ramo(anio=anio)
df_prest = load_anuario_reservas_prestaciones_por_ramo(anio=anio)
df_prima_emp = load_anuario_reservas_prima_por_empresa(anio=anio)
df_prest_emp = load_anuario_reservas_prestaciones_por_empresa(anio=anio)

if df_tec.empty and df_prima.empty and df_prest.empty and df_prima_emp.empty and df_prest_emp.empty:
    st.info("Ejecute el ETL para cargar reservas: `python scripts/etl_anuario_a_supabase.py --year 2023`.")
    st.stop()

tabs = st.tabs([
    "Técnicas agregado (9)",
    "Prima por ramo (10)",
    "Prima por empresa (11-14)",
    "Prestaciones por ramo (15)",
    "Prestaciones por empresa (16-19)",
    "Detalle por ramo/empresa (20-A a 20-F)",
    "Inversiones reservas (21)",
    "Hospitalización (32, 33)",
])

with tabs[0]:
    st.markdown("**Cuadro 9:** reservas técnicas agregado.")
    if df_tec.empty:
        st.info("No hay datos. Ejecute el ETL.")
    else:
        display = df_tec[["concepto", "monto", "tipo"]].copy()
        display["monto"] = pd.to_numeric(display["monto"], errors="coerce")
        treemap_df = display[display["monto"].notna() & (display["monto"] > 0)].copy()
        if not treemap_df.empty and len(treemap_df) <= 25:
            import plotly.express as px
            path_cols = ["tipo", "concepto"] if "tipo" in treemap_df.columns and treemap_df["tipo"].notna().any() else ["concepto"]
            fig_treemap_r = px.treemap(
                treemap_df, path=path_cols, values="monto",
                title="Reservas técnicas por concepto (Treemap)",
                color="monto", color_continuous_scale="Viridis",
            )
            fig_treemap_r.update_traces(textinfo="label+value+percent parent")
            fig_treemap_r.update_layout(margin=dict(t=40, b=20), height=400, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_treemap_r, use_container_width=True)
        st.dataframe(estilizar_df_numeros(display, ["monto"], 0), use_container_width=True, hide_index=True)

with tabs[1]:
    st.markdown("**Cuadro 10:** reservas de prima por ramo.")
    if df_prima.empty:
        st.info("No hay datos. Ejecute el ETL.")
    else:
        try:
            if "datos" in df_prima.columns and df_prima["datos"].notna().any():
                d = df_prima["datos"].dropna()
                if len(d) > 0 and isinstance(d.iloc[0], dict):
                    expand = pd.json_normalize(d.tolist())
                    display = pd.concat([df_prima.loc[d.index, ["concepto_ramo"]].reset_index(drop=True), expand.reset_index(drop=True)], axis=1)
                else:
                    display = df_prima[["concepto_ramo"]].copy()
            else:
                display = df_prima[["concepto_ramo"]].copy()
            cols_num = [c for c in display.columns if c != "concepto_ramo"]
            for c in cols_num:
                display[c] = pd.to_numeric(display[c], errors="coerce")
            st.dataframe(estilizar_df_numeros(display, cols_num, 0), use_container_width=True, hide_index=True)
        except Exception:
            st.dataframe(df_prima[["concepto_ramo"]], use_container_width=True, hide_index=True)

with tabs[2]:
    st.markdown("**Cuadros 11-14:** reservas de prima por empresa (general, Personas, Patrimoniales, Obligacionales).")
    if df_prima_emp.empty:
        st.caption("Sin datos. Ejecute el ETL: `python scripts/etl_anuario_a_supabase.py --year 2023`.")
    else:
        for cuadro_id, label in [("11", "Cuadro 11 — General"), ("12", "Cuadro 12 — Personas"), ("13", "Cuadro 13 — Patrimoniales"), ("14", "Cuadro 14 — Obligacionales")]:
            sub = df_prima_emp[df_prima_emp["cuadro_id"] == cuadro_id]
            if sub.empty:
                continue
            with st.expander(label, expanded=(cuadro_id == "11")):
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

with tabs[3]:
    st.markdown("**Cuadro 15:** reservas de prestaciones/siniestros por ramo.")
    if df_prest.empty:
        st.info("No hay datos. Ejecute el ETL.")
    else:
        try:
            if "datos" in df_prest.columns and df_prest["datos"].notna().any():
                d = df_prest["datos"].dropna()
                if len(d) > 0 and isinstance(d.iloc[0], dict):
                    expand = pd.json_normalize(d.tolist())
                    display = pd.concat([df_prest.loc[d.index, ["concepto_ramo"]].reset_index(drop=True), expand.reset_index(drop=True)], axis=1)
                else:
                    display = df_prest[["concepto_ramo"]].copy()
            else:
                display = df_prest[["concepto_ramo"]].copy()
            cols_num = [c for c in display.columns if c != "concepto_ramo"]
            for c in cols_num:
                display[c] = pd.to_numeric(display[c], errors="coerce")
            st.dataframe(estilizar_df_numeros(display, cols_num, 0), use_container_width=True, hide_index=True)
        except Exception:
            st.dataframe(df_prest[["concepto_ramo"]], use_container_width=True, hide_index=True)

with tabs[4]:
    st.markdown("**Cuadros 16-19:** reservas de prestaciones por empresa (general, Personas, Patrimoniales, Obligacionales).")
    if df_prest_emp.empty:
        st.caption("Sin datos. Ejecute el ETL: `python scripts/etl_anuario_a_supabase.py --year 2023`.")
    else:
        for cuadro_id, label in [("16", "Cuadro 16 — General"), ("17", "Cuadro 17 — Personas"), ("18", "Cuadro 18 — Patrimoniales"), ("19", "Cuadro 19 — Obligacionales")]:
            sub = df_prest_emp[df_prest_emp["cuadro_id"] == cuadro_id]
            if sub.empty:
                continue
            with st.expander(label, expanded=(cuadro_id == "16")):
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

with tabs[5]:
    st.markdown("**Cuadros 20-A a 20-F:** detalle por ramo y empresa. Próximamente.")

with tabs[6]:
    st.markdown("**Cuadro 21:** inversiones representativas de las reservas técnicas. Próximamente.")

with tabs[7]:
    st.markdown("**Cuadros 32, 33:** reservas hospitalización individual y colectivo. Próximamente.")
