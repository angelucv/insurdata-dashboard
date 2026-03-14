# pages/1_Cifras_por_Sector.py — Cifras por sector (resumen balances, totales, empresas)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_env = Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.app.components.data_loader import load_anuario_cuadros, load_anuario_balances_condensados, load_anuario_listados_empresas
from src.app.anuario_config import (
    APP_NAME,
    SECTORES,
    BALANCES_CUADRO_POR_SECTOR,
    LISTADOS_CUADRO_POR_SECTOR,
    ORDEN_SECTORES,
    filtrar_encabezados_balance,
    extraer_totales_balance,
    formato_numero_es,
    estilizar_df_numeros,
    render_sidebar_footer,
    render_sidebar_logo,
)

st.set_page_config(
    page_title=f"Cifras por sector | {APP_NAME}",
    page_icon="📊",
    layout="wide",
)

COLORES_SECTOR = {
    "seguro_directo": {"borde": "#1e40af", "fondo": "rgba(30, 64, 175, 0.08)"},
    "reaseguro": {"borde": "#475569", "fondo": "rgba(71, 85, 105, 0.08)"},
    "financiadoras_primas": {"borde": "#0f766e", "fondo": "rgba(15, 118, 110, 0.08)"},
    "medicina_prepagada": {"borde": "#6b21a8", "fondo": "rgba(107, 33, 168, 0.08)"},
}

st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }
    .macro-card { padding: 1rem 1.25rem; border-radius: 8px; border-left: 4px solid; margin-bottom: 1rem;
                  font-family: system-ui, sans-serif; }
    .macro-card .macro-label { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.02em; opacity: 0.9; margin-bottom: 0.35rem; }
    .macro-card .macro-valor { font-size: 1.5rem; font-weight: 700; }
    .macro-card .macro-sub { font-size: 0.75rem; opacity: 0.8; margin-top: 0.25rem; }
</style>
""", unsafe_allow_html=True)

render_sidebar_logo()
st.sidebar.caption(APP_NAME)
anio_sel = st.sidebar.selectbox("Año", options=[2023, 2022, 2021], index=0, key="cifras_anio")
render_sidebar_footer()

st.title("Cifras por sector")
st.caption("Superintendencia de la Actividad Aseguradora — Explotación de datos del anuario estadístico. **Año de corte:** datos al cierre del año seleccionado. **Unidad monetaria:** miles de bolívares (salvo indicación contraria en el cuadro).")

df_cuadros = load_anuario_cuadros()
df_balances = load_anuario_balances_condensados(anio=anio_sel)
df_listados = load_anuario_listados_empresas(anio=anio_sel)

if df_cuadros.empty:
    st.warning(
        "No hay datos del anuario. Ejecute en Supabase los DDL (001 a 005), exponga el schema **anuario** "
        "y ejecute: `python scripts/etl_anuario_a_supabase.py --year 2023`."
    )
    st.stop()

df_bal = df_balances.copy()
sectores_bal = [s for s in ORDEN_SECTORES if s in BALANCES_CUADRO_POR_SECTOR]

if not df_balances.empty and sectores_bal:
    resultados_sector = []
    for sector_id in sectores_bal:
        cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
        sub = df_bal[df_bal["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
        t = extraer_totales_balance(sub)
        util = t["utilidad_ejercicio"]
        perd = t["perdida_ejercicio"]
        util_val = util if util is not None and pd.notna(util) else 0
        perd_val = perd if perd is not None and pd.notna(perd) else 0
        resultado_num = util_val - perd_val
        if resultado_num > 0:
            texto_valor = f"Utilidad {formato_numero_es(resultado_num, 0)}"
            texto_sub = "Resultado positivo del ejercicio"
        elif resultado_num < 0:
            texto_valor = f"Pérdida {formato_numero_es(abs(resultado_num), 0)}"
            texto_sub = "Resultado negativo del ejercicio"
        else:
            texto_valor = "—"
            texto_sub = "Sin resultado reportado"
        resultados_sector.append({
            "sector_id": sector_id,
            "valor": texto_valor,
            "sub": texto_sub,
        })
    cols_macro = st.columns(len(resultados_sector))
    for i, r in enumerate(resultados_sector):
        cfg = COLORES_SECTOR.get(r["sector_id"], {"borde": "#64748b", "fondo": "rgba(100, 116, 139, 0.08)"})
        nombre_sector = SECTORES.get(r["sector_id"], r["sector_id"])
        with cols_macro[i]:
            st.markdown(
                f'<div class="macro-card" style="border-left-color: {cfg["borde"]}; background: {cfg["fondo"]};">'
                f'<div class="macro-label">{nombre_sector}</div>'
                f'<div class="macro-valor">{r["valor"]}</div>'
                f'<div class="macro-sub">{r["sub"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
    st.caption("Resultado del ejercicio por sector (balance condensado). Utilidad = positivo; Pérdida = negativo.")
    st.markdown("---")

if not df_balances.empty:
    st.subheader("Totales por sector (balance condensado)")
    st.caption(
        "**Unidad:** miles de bolívares. Valores extraídos del balance condensado de cada sector (cuadros 24, 40, 47, 54)."
    )
    filas = []
    chart_barras = []
    for sector_id in sectores_bal:
        cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
        sub = df_bal[df_bal["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
        t = extraer_totales_balance(sub)
        label = SECTORES.get(sector_id, sector_id)
        total_activo = t["total_activo"]
        total_pasivo = t["total_pasivo"]
        act_num = float(total_activo) if total_activo is not None and pd.notna(total_activo) else 0
        pas_num = float(total_pasivo) if total_pasivo is not None and pd.notna(total_pasivo) else 0
        chart_barras.append({"Sector": label, "Activo": act_num, "Pasivo": pas_num})
        util = t["utilidad_ejercicio"]
        perd = t["perdida_ejercicio"]
        util_val = util if util is not None and pd.notna(util) else 0
        perd_val = perd if perd is not None and pd.notna(perd) else 0
        if util_val != 0 or perd_val != 0:
            resultado = util_val - perd_val
            if resultado > 0:
                resultado_txt = f"Utilidad {formato_numero_es(resultado, 0)}"
            elif resultado < 0:
                resultado_txt = f"Pérdida {formato_numero_es(abs(resultado), 0)}"
            else:
                resultado_txt = "0"
        else:
            resultado_txt = "—"
        filas.append({
            "Sector": label,
            "Total Activo": formato_numero_es(total_activo, 0) if total_activo is not None and pd.notna(total_activo) else "—",
            "Total Pasivo": formato_numero_es(total_pasivo, 0) if total_pasivo is not None and pd.notna(total_pasivo) else "—",
            "Utilidad ejercicio": formato_numero_es(util, 0) if util is not None and pd.notna(util) and util != 0 else "—",
            "Pérdida ejercicio": formato_numero_es(perd, 0) if perd is not None and pd.notna(perd) and perd != 0 else "—",
            "Resultado": resultado_txt,
        })
    if filas:
        df_totales = pd.DataFrame(filas)
        cols_num = ["Total Activo", "Total Pasivo", "Utilidad ejercicio", "Pérdida ejercicio", "Resultado"]
        st.dataframe(df_totales.style.set_properties(subset=[c for c in cols_num if c in df_totales.columns], **{"text-align": "right"}), use_container_width=True, hide_index=True)
        # Barras agrupadas: Activo vs Pasivo por sector
        if chart_barras and any(r["Activo"] > 0 or r["Pasivo"] > 0 for r in chart_barras):
            df_barras = pd.DataFrame(chart_barras)
            fig_barras = go.Figure()
            fig_barras.add_trace(go.Bar(
                x=df_barras["Sector"],
                y=df_barras["Activo"],
                name="Total activo",
                marker_color="#1e40af",
                text=df_barras["Activo"].apply(lambda v: formato_numero_es(v, 0)),
                textposition="outside",
            ))
            fig_barras.add_trace(go.Bar(
                x=df_barras["Sector"],
                y=df_barras["Pasivo"],
                name="Total pasivo",
                marker_color="#64748b",
                text=df_barras["Pasivo"].apply(lambda v: formato_numero_es(v, 0)),
                textposition="outside",
            ))
            fig_barras.update_layout(
                barmode="group",
                title="Activo vs Pasivo por sector",
                xaxis_title="",
                yaxis_title="Miles de bolívares",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                height=400,
                margin=dict(t=60, b=50),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_barras, use_container_width=True)
            st.caption("Comparación de total activo y total pasivo por sector (balance condensado). Unidad: miles de bolívares.")

    st.markdown("---")
    st.subheader("Datos técnicos — Balances condensados (resumen)")
    st.caption(f"Año {anio_sel}. Primeros conceptos y montos por sector. Para el detalle completo use **Balances** en el menú.")
    # Gráficos resumen: resultado por sector + participación en total activo
    resumen_bal = []
    for sector_id in sectores_bal:
        cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
        sub = df_bal[df_bal["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
        t = extraer_totales_balance(sub)
        act = t.get("total_activo") or 0
        util = t.get("utilidad_ejercicio") or 0
        perd = t.get("perdida_ejercicio") or 0
        resumen_bal.append({
            "Sector": SECTORES.get(sector_id, sector_id),
            "Total_activo": float(act),
            "Resultado": (float(util) if util else 0) - (float(perd) if perd else 0),
        })
    if resumen_bal:
        df_res = pd.DataFrame(resumen_bal)
        c1, c2 = st.columns(2)
        with c1:
            if df_res["Resultado"].abs().sum() > 0:
                fig_res = px.bar(
                    df_res, y="Sector", x="Resultado", orientation="h",
                    title="Resultado del ejercicio por sector",
                    color="Resultado",
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                )
                fig_res.update_layout(showlegend=False, height=280, margin=dict(t=40, b=40), xaxis_title="Miles Bs.", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_res, use_container_width=True)
        with c2:
            if df_res["Total_activo"].sum() > 0:
                df_res["Pct_activo"] = (df_res["Total_activo"] / df_res["Total_activo"].sum() * 100).round(1)
                fig_pct = px.bar(
                    df_res, x="Sector", y="Pct_activo",
                    title="Participación en el total de activos (%)",
                    text="Pct_activo",
                    labels={"Pct_activo": "%"},
                )
                fig_pct.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig_pct.update_layout(showlegend=False, height=280, margin=dict(t=40, b=50), yaxis_title="% del total", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pct, use_container_width=True)
    for sector_id in sectores_bal:
        cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
        sub = df_bal[df_bal["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
        sub = filtrar_encabezados_balance(sub).head(12)
        if sub.empty:
            continue
        label = SECTORES.get(sector_id, sector_id)
        with st.expander(f"**{label}** (cuadro {cuadro_id}) — vista previa", expanded=(sector_id == "seguro_directo")):
            sub_display = sub.copy()
            sub_display["monto"] = pd.to_numeric(sub_display["monto"], errors="coerce")
            st.dataframe(estilizar_df_numeros(sub_display, ["monto"], 0), use_container_width=True, hide_index=True)

if not df_listados.empty:
    st.markdown("---")
    st.subheader("Datos técnicos — Empresas autorizadas por sector")
    n_seguro = len(df_listados[df_listados["cuadro_id"] == LISTADOS_CUADRO_POR_SECTOR.get("seguro_directo", "1")])
    if n_seguro == 1:
        st.caption("Si solo aparece 1 empresa en Empresas de Seguro, ejecute el ETL para cargar el Cuadro 1 actualizado y luego en Streamlit: **Ejecutar** → **Limpiar caché**.")
    for sector_id, cuadro_id in LISTADOS_CUADRO_POR_SECTOR.items():
        sub = df_listados[df_listados["cuadro_id"] == cuadro_id][["numero_orden", "nombre_empresa"]]
        if sub.empty:
            continue
        label = SECTORES.get(sector_id, sector_id)
        if sector_id == "seguro_directo":
            label_expander = f"**{label}** (Cuadro 1 — Empresas de seguros autorizadas) — {len(sub)} empresas"
        else:
            label_expander = f"**{label}** — {len(sub)} empresas (cuadro {cuadro_id})"
        with st.expander(label_expander):
            sub_lep = sub.copy()
            sub_lep["numero_orden"] = pd.to_numeric(sub_lep["numero_orden"], errors="coerce")
            st.dataframe(estilizar_df_numeros(sub_lep, ["numero_orden"], 0), use_container_width=True, hide_index=True)
