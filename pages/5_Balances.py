# pages/4_Balances.py — Anuario: Balances condensados por sector (macro -> detalle)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from src.app.components.data_loader import load_anuario_balances_condensados
from src.app.anuario_config import (
    APP_NAME,
    SECTORES,
    BALANCES_CUADRO_POR_SECTOR,
    ORDEN_SECTORES,
    filtrar_encabezados_balance,
    estilizar_df_numeros,
    extraer_totales_balance,
    formato_numero_es,
    render_sidebar_footer,
    render_sidebar_logo,
)

st.set_page_config(page_title=f"Balances | {APP_NAME}", page_icon="📊", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="anuario_anio")
render_sidebar_footer()

st.title("Balances condensados")
st.caption("Cuadros 24, 40, 47, 54 — Por sector. **Unidad:** miles de bolívares.")

df = load_anuario_balances_condensados(anio=anio)

if df.empty:
    st.warning(f"No hay datos de balances para el año {anio}. Ejecute el ETL: `python scripts/etl_anuario_a_supabase.py --year {anio}`.")
    st.stop()

# Resumen compacto por sector: tabla + gráfico (evita bloque truncado)
sectores_balance = [s for s in ORDEN_SECTORES if s in BALANCES_CUADRO_POR_SECTOR]
filas_bal = []
for sector_id in sectores_balance:
    cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
    sub = df[df["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
    t = extraer_totales_balance(sub)
    label = SECTORES.get(sector_id, sector_id)
    total_activo = t.get("total_activo")
    total_pasivo = t.get("total_pasivo")
    util = t.get("utilidad_ejercicio") or 0
    perd = t.get("perdida_ejercicio") or 0
    resultado = util - perd
    filas_bal.append({
        "Sector": label,
        "Total activo": formato_numero_es(total_activo, 0) if total_activo is not None else "—",
        "Total pasivo": formato_numero_es(total_pasivo, 0) if total_pasivo is not None else "—",
        "Resultado ejercicio": formato_numero_es(resultado, 0) if resultado != 0 else "—",
    })
if filas_bal:
    df_resumen = pd.DataFrame(filas_bal)
    st.dataframe(df_resumen.style.set_properties(subset=["Total activo", "Total pasivo", "Resultado ejercicio"], **{"text-align": "right"}), use_container_width=True, hide_index=True)
    # Gráfico resultado por sector (barras horizontales)
    resultado_nums = []
    for sector_id in sectores_balance:
        cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
        sub = df[df["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
        t = extraer_totales_balance(sub)
        util = t.get("utilidad_ejercicio") or 0
        perd = t.get("perdida_ejercicio") or 0
        resultado_nums.append({"Sector": SECTORES.get(sector_id, sector_id), "Resultado": util - perd})
    if resultado_nums and any(r["Resultado"] != 0 for r in resultado_nums):
        import plotly.express as px
        df_res = pd.DataFrame(resultado_nums)
        fig_bal = px.bar(df_res, y="Sector", x="Resultado", orientation="h", title="Resultado del ejercicio por sector", color="Resultado", color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
        fig_bal.update_layout(showlegend=False, height=220, margin=dict(t=30, b=30), xaxis_title="Miles Bs.", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bal, use_container_width=True)

st.markdown("---")
st.subheader("Detalle por sector")

# Tabs por sector (de lo general al detalle)
tab_names = [SECTORES.get(s, s) for s in sectores_balance]
tabs = st.tabs(tab_names)

for i, sector_id in enumerate(sectores_balance):
    cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
    sub = df[df["cuadro_id"] == cuadro_id].copy()
    if sub.empty:
        with tabs[i]:
            st.info(f"Sin datos para cuadro {cuadro_id}.")
        continue
    sub = sub[["concepto", "monto", "tipo"]].copy()
    sub = filtrar_encabezados_balance(sub)
    sub["monto"] = pd.to_numeric(sub["monto"], errors="coerce")
    with tabs[i]:
        st.dataframe(estilizar_df_numeros(sub, ["monto"], 0), use_container_width=True, hide_index=True)

st.caption("Balance por empresa reaseguros (cuadro 42) — próximamente cuando se cargue la tabla.")
