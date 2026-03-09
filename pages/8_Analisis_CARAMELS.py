# pages/10_Analisis_CARAMELS.py — Análisis CARAMELS para compañías de seguro
"""
Marco de supervisión CARAMELS (Capital, Activos, Reaseguro, Actuarial, Management, Earnings, Liquidity, Sensitivity).
Explotación con los datos disponibles del anuario (balances, primas, siniestros, reservas, estados, gestión).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.app.components.data_loader import (
    load_anuario_balances_condensados,
    load_anuario_capital_garantia_por_empresa,
    load_anuario_primas_por_ramo,
    load_anuario_siniestros_por_ramo,
    load_anuario_reservas_tecnicas_agregado,
    load_anuario_estados_ingresos_egresos,
    load_anuario_gestion_general,
)
from src.app.anuario_config import (
    APP_NAME,
    SECTORES,
    BALANCES_CUADRO_POR_SECTOR,
    ORDEN_SECTORES,
    extraer_totales_balance,
    formato_numero_es,
    estilizar_df_numeros,
    render_sidebar_footer,
    LAYOUT_PIE_MODERNO,
    PALETA_PIE_MODERNA,
)

st.set_page_config(page_title=f"Análisis CARAMELS | {APP_NAME}", page_icon="🔍", layout="wide")
st.sidebar.caption(APP_NAME)
anio = st.sidebar.selectbox("Año", [2023, 2022, 2021], index=0, key="caramels_anio")
render_sidebar_footer()

st.title("Análisis CARAMELS")
st.caption("Marco de supervisión para compañías de seguro: Capital, Activos, Reaseguro, Actuarial, Gestión, Rentabilidad, Liquidez, Sensibilidad. **Unidad:** miles de bolívares.")

# Cargar datos
df_bal = load_anuario_balances_condensados(anio=anio)
df_cap = load_anuario_capital_garantia_por_empresa(anio=anio)
df_primas = load_anuario_primas_por_ramo(anio=anio)
df_sini = load_anuario_siniestros_por_ramo(anio=anio)
df_res = load_anuario_reservas_tecnicas_agregado(anio=anio)
df_est = load_anuario_estados_ingresos_egresos(anio=anio)
df_gest = load_anuario_gestion_general(anio=anio)

if df_bal.empty and df_primas.empty:
    st.info("No hay datos suficientes para el análisis CARAMELS. Ejecute el ETL del anuario.")
    st.stop()

# Helpers
def _totales_por_sector():
    out = {}
    for sector_id, cuadro_id in BALANCES_CUADRO_POR_SECTOR.items():
        sub = df_bal[df_bal["cuadro_id"] == cuadro_id][["concepto", "monto"]]
        out[sector_id] = extraer_totales_balance(sub)
    return out

def _primas_siniestros_totales():
    p_total, s_total = None, None
    if not df_primas.empty and "total" in df_primas.columns:
        p3 = df_primas[df_primas["cuadro_id"] == "3"].copy()
        if not p3.empty:
            p3["total"] = pd.to_numeric(p3["total"], errors="coerce")
            tot_row = p3[p3["concepto_ramo"].str.strip().str.upper() == "TOTAL"]
            p_total = tot_row["total"].sum() if not tot_row.empty else p3["total"].sum()
    if not df_sini.empty and "datos" in df_sini.columns:
        sub6 = df_sini[df_sini["cuadro_id"] == "6"]
        tot_row = sub6[sub6["concepto_ramo"].str.strip().str.upper() == "TOTAL"]
        if not tot_row.empty and tot_row["datos"].notna().any():
            try:
                d = tot_row["datos"].iloc[0]
                if isinstance(d, dict):
                    s_total = pd.to_numeric(d.get("TOTAL", d.get("total")), errors="coerce")
            except Exception:
                pass
        elif not sub6.empty and sub6["datos"].notna().any():
            try:
                expand = pd.json_normalize(sub6["datos"].dropna())
                if "TOTAL" in expand.columns:
                    s_total = pd.to_numeric(expand["TOTAL"], errors="coerce").iloc[-1]
                elif "total" in expand.columns:
                    s_total = pd.to_numeric(expand["total"], errors="coerce").iloc[-1]
            except Exception:
                pass
    return p_total, s_total

totales_sector = _totales_por_sector()
primas_total, siniestros_total = _primas_siniestros_totales()

# Tacómetros (gauges): ratio siniestros/primas, reservas/primas, liquidez, resultado agregado
gcol1, gcol2, gcol3, gcol4 = st.columns(4)
with gcol1:
    if primas_total and primas_total > 0 and siniestros_total is not None and siniestros_total >= 0:
        ratio_sp = 100 * siniestros_total / primas_total
        fig_g1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(ratio_sp, 1),
            title={"text": "Siniestros/Primas (%)", "font": {"size": 10}},
            gauge=dict(
                axis=dict(range=[0, 120]),
                bar=dict(color="#4A90D9"),
                steps=[dict(range=[0, 50], color="lightgray"), dict(range=[50, 80], color="gray"), dict(range=[80, 120], color="darkgray")],
                threshold=dict(line=dict(color="red", width=3), value=80),
            ),
        ))
        fig_g1.update_layout(height=260, margin=dict(l=10, r=10, t=50), font=dict(size=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_g1, use_container_width=True)
    else:
        st.caption("Siniestros/Primas: sin datos")
with gcol2:
    tot_res = 0
    if not df_res.empty and "monto" in df_res.columns:
        df_res["monto"] = pd.to_numeric(df_res["monto"], errors="coerce")
        tot_res = df_res["monto"].sum() or 0
    if primas_total and primas_total > 0 and tot_res >= 0:
        ratio_rp = 100 * tot_res / primas_total
        fig_g2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(ratio_rp, 1),
            title={"text": "Reservas/Primas (%)", "font": {"size": 10}},
            gauge=dict(
                axis=dict(range=[0, 150]),
                bar=dict(color="#50C878"),
                steps=[dict(range=[0, 50], color="lightgray"), dict(range=[50, 100], color="gray"), dict(range=[100, 150], color="darkgray")],
                threshold=dict(line=dict(color="green", width=3), value=80),
            ),
        ))
        fig_g2.update_layout(height=260, margin=dict(l=10, r=10, t=50), font=dict(size=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_g2, use_container_width=True)
    else:
        st.caption("Reservas/Primas: sin datos")
with gcol3:
    total_act = totales_sector.get("seguro_directo", {}).get("total_activo")
    pct_liq = None
    if not df_gest.empty and total_act and total_act > 0:
        df_gest["monto"] = pd.to_numeric(df_gest["monto"], errors="coerce")
        liquidez = df_gest[df_gest["concepto"].str.upper().str.contains("DEPÓSITOS A LA VISTA|MESA DE DINERO|Depósitos a la Vista|Mesa de Dinero", na=False)]
        tot_liq = liquidez["monto"].sum() if not liquidez.empty else 0
        if tot_liq >= 0:
            pct_liq = 100 * tot_liq / total_act
    if pct_liq is not None:
        fig_g3 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(pct_liq, 1),
            title={"text": "Liquidez aprox. (%)", "font": {"size": 10}},
            number={"suffix": "%", "font": {"size": 10}},
            gauge=dict(
                axis=dict(range=[0, 50]),
                bar=dict(color="#E8A87C"),
                steps=[dict(range=[0, 15], color="lightgray"), dict(range=[15, 30], color="gray"), dict(range=[30, 50], color="darkgray")],
                threshold=dict(line=dict(color="orange", width=3), value=20),
            ),
        ))
        fig_g3.update_layout(height=260, margin=dict(l=10, r=10, t=50), font=dict(size=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_g3, use_container_width=True)
    else:
        st.caption("Liquidez: sin datos")
with gcol4:
    resul_agreg = 0
    for sector_id in ORDEN_SECTORES:
        if sector_id not in BALANCES_CUADRO_POR_SECTOR:
            continue
        t = totales_sector.get(sector_id, {})
        util = t.get("utilidad_ejercicio") or 0
        perd = t.get("perdida_ejercicio") or 0
        resul_agreg += util - perd
    # Escala 0-100 para “salud” (resultado positivo = mejor)
    val_ref = max(abs(resul_agreg), 1)
    salud = 50 + 50 * min(1, max(-1, resul_agreg / val_ref)) if resul_agreg != 0 else 50
    fig_g4 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(salud, 0),
        number={"suffix": " (índice)", "font": {"size": 10}},
        title={"text": "Resultado agregado (0-100)", "font": {"size": 10}},
        gauge=dict(
            axis=dict(range=[0, 100]),
            bar=dict(color="#7B68EE"),
            steps=[dict(range=[0, 33], color="#ffcccc"), dict(range=[33, 66], color="#ffffcc"), dict(range=[66, 100], color="#ccffcc")],
            threshold=dict(line=dict(color="green", width=3), value=60),
        ),
    ))
    fig_g4.update_layout(height=260, margin=dict(l=10, r=10, t=50), font=dict(size=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_g4, use_container_width=True)
    st.caption("50 = neutro; >50 positivo; <50 negativo.")

# Resumen ejecutivo
st.subheader("Resumen por dimensión")
cols = st.columns(4)
dimensions = [
    ("C", "Capital", totales_sector.get("seguro_directo", {}).get("total_pasivo") or 0),
    ("A", "Activos", totales_sector.get("seguro_directo", {}).get("total_activo") or 0),
    ("E", "Rentabilidad", (totales_sector.get("seguro_directo", {}).get("utilidad_ejercicio") or 0) - (totales_sector.get("seguro_directo", {}).get("perdida_ejercicio") or 0)),
    ("R", "Reaseguro", df_primas[df_primas["cuadro_id"] == "3"]["reaseguro_aceptado"].apply(pd.to_numeric, errors="coerce").sum() if not df_primas.empty and "reaseguro_aceptado" in df_primas.columns else 0),
]
for i, (letra, nombre, valor) in enumerate(dimensions[:4]):
    with cols[i]:
        st.metric(f"{letra} — {nombre}", formato_numero_es(valor, 0) if valor else "—")

st.markdown("---")

# Tabs por dimensión
tabs = st.tabs([
    "Flujos",
    "C — Capital",
    "A — Activos",
    "R — Reaseguro",
    "A — Actuarial",
    "M — Gestión",
    "E — Rentabilidad",
    "L — Liquidez",
    "S — Sensibilidad",
])

with tabs[0]:
    st.markdown("**Flujo de primas: seguro directo vs reaseguro**")
    st.caption("Distribución de las primas totales (Cuadro 3) entre operaciones de **seguro directo** (retenidas por la empresa) y **reaseguro aceptado** (cedidas a reaseguradores). Unidad: miles de bolívares.")
    if not df_primas.empty and "seguro_directo" in df_primas.columns and "reaseguro_aceptado" in df_primas.columns:
        p3 = df_primas[df_primas["cuadro_id"] == "3"].copy()
        p3["seguro_directo"] = pd.to_numeric(p3["seguro_directo"], errors="coerce")
        p3["reaseguro_aceptado"] = pd.to_numeric(p3["reaseguro_aceptado"], errors="coerce")
        tot_directo = p3["seguro_directo"].sum()
        tot_reaseg = p3["reaseguro_aceptado"].sum()
        if tot_directo + tot_reaseg > 0:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Seguro directo (retenido)", formato_numero_es(tot_directo, 0))
            with c2:
                st.metric("Reaseguro aceptado (cedido)", formato_numero_es(tot_reaseg, 0))
            df_barras = pd.DataFrame({
                "Concepto": ["Seguro directo", "Reaseguro aceptado"],
                "Monto (miles Bs.)": [tot_directo, tot_reaseg],
            })
            fig_barras = px.bar(
                df_barras, x="Concepto", y="Monto (miles Bs.)",
                color="Monto (miles Bs.)",
                color_continuous_scale="Blues",
                text_auto=",.0f",
            )
            fig_barras.update_layout(
                title="Primas: seguro directo vs reaseguro aceptado",
                height=320,
                margin=dict(t=40, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis_title="",
            )
            fig_barras.update_traces(textposition="outside")
            st.plotly_chart(fig_barras, use_container_width=True)
        else:
            st.caption("Sin montos de primas en el Cuadro 3.")
    else:
        st.caption("Sin datos de primas (Cuadro 3) para el flujo.")

with tabs[1]:
    st.markdown("**Capital (solvencia y suficiencia de capital)**")
    st.caption("Capital social, garantías y recursos propios frente a pasivos y riesgos.")
    if not df_cap.empty:
        cap_cols = [c for c in ["nombre_empresa", "capital_social_suscrito", "garantia_total", "garantia_operaciones_seguros"] if c in df_cap.columns]
        if cap_cols:
            disp = df_cap[cap_cols].copy()
            for c in ["capital_social_suscrito", "garantia_total", "garantia_operaciones_seguros"]:
                if c in disp.columns:
                    disp[c] = pd.to_numeric(disp[c], errors="coerce")
            st.dataframe(estilizar_df_numeros(disp, [c for c in disp.columns if c != "nombre_empresa"], 0), use_container_width=True, hide_index=True)
    for sector_id in ORDEN_SECTORES:
        if sector_id not in BALANCES_CUADRO_POR_SECTOR:
            continue
        t = totales_sector.get(sector_id, {})
        cap = t.get("total_pasivo")  # aproximación: pasivo como referencia
        if cap is not None:
            st.caption(f"**{SECTORES.get(sector_id, sector_id)}** — Total pasivo (referencia): {formato_numero_es(cap, 0)}")
    if df_bal.empty and df_cap.empty:
        st.info("Sin datos de capital/garantía. Cargue Cuadro 2 y balances.")

with tabs[2]:
    st.markdown("**Calidad de activos**")
    st.caption("Composición del activo: inversiones, cuentas por reaseguro, otros activos.")
    sector_activo = "seguro_directo"
    cuadro_id = BALANCES_CUADRO_POR_SECTOR.get(sector_activo)
    if cuadro_id and not df_bal.empty:
        sub = df_bal[df_bal["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
        sub["monto"] = pd.to_numeric(sub["monto"], errors="coerce")
        # Filtrar solo líneas de activo (hasta TOTAL ACTIVO)
        idx_total = sub[sub["concepto"].str.strip().str.upper() == "TOTAL ACTIVO"].index
        if len(idx_total) > 0:
            idx = sub.index.get_loc(idx_total[0])
            sub = sub.iloc[: idx + 1]
        sub = sub[sub["monto"].notna() & (sub["monto"] > 0)]
        if not sub.empty:
            sub = sub[sub["concepto"].str.strip().str.upper() != "ACTIVO"]
            st.dataframe(estilizar_df_numeros(sub, ["monto"], 0), use_container_width=True, hide_index=True)
        total_act = totales_sector.get(sector_activo, {}).get("total_activo")
        if total_act:
            st.metric("Total activo (Empresas de Seguro)", formato_numero_es(total_act, 0))
    else:
        st.info("Sin datos de balance para activos.")

with tabs[3]:
    st.markdown("**Reaseguro y retención de riesgo**")
    st.caption("Primas cedidas vs. retenidas; exposición a reaseguradores.")
    if not df_primas.empty and "seguro_directo" in df_primas.columns and "reaseguro_aceptado" in df_primas.columns:
        p3 = df_primas[df_primas["cuadro_id"] == "3"].copy()
        p3["seguro_directo"] = pd.to_numeric(p3["seguro_directo"], errors="coerce")
        p3["reaseguro_aceptado"] = pd.to_numeric(p3["reaseguro_aceptado"], errors="coerce")
        tot_directo = p3["seguro_directo"].sum()
        tot_reaseg = p3["reaseguro_aceptado"].sum()
        tot = tot_directo + tot_reaseg
        if tot > 0:
            pct_reaseg = 100 * tot_reaseg / tot
            st.metric("Primas seguro directo", formato_numero_es(tot_directo, 0))
            st.metric("Primas reaseguro aceptado", formato_numero_es(tot_reaseg, 0))
            st.metric("% reaseguro sobre total", f"{pct_reaseg:.2f}%")
            fig_r = go.Figure(data=[go.Pie(
                labels=["Seguro directo", "Reaseguro aceptado"],
                values=[tot_directo, tot_reaseg],
                hole=0.58,
                marker=dict(
                    colors=[PALETA_PIE_MODERNA[0], PALETA_PIE_MODERNA[1]],
                    line=dict(color="white", width=1.8),
                ),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )])
            fig_r.update_layout(**LAYOUT_PIE_MODERNO, title="Composición primas (Cuadro 3)", height=320)
            st.plotly_chart(fig_r, use_container_width=True)
    # Cuentas reaseguro en balance
    reaseg_bal = pd.DataFrame()
    if not df_bal.empty and BALANCES_CUADRO_POR_SECTOR.get("seguro_directo"):
        cid = BALANCES_CUADRO_POR_SECTOR["seguro_directo"]
        sub = df_bal[df_bal["cuadro_id"] == cid][["concepto", "monto"]]
        sub["monto"] = pd.to_numeric(sub["monto"], errors="coerce")
        reaseg_bal = sub[sub["concepto"].str.upper().str.contains("REASEGURO", na=False)]
        if not reaseg_bal.empty:
            st.caption("**Conceptos vinculados a reaseguro en balance (Empresas de Seguro)**")
            st.dataframe(estilizar_df_numeros(reaseg_bal, ["monto"], 0), use_container_width=True, hide_index=True)
    if (df_primas.empty or df_primas[df_primas["cuadro_id"] == "3"].empty) and reaseg_bal.empty:
        st.info("Sin datos de reaseguro. Cargue primas por ramo (Cuadro 3).")

with tabs[4]:
    st.markdown("**Actuarial (reservas, primas, siniestros)**")
    st.caption("Reservas técnicas, ratio siniestros/primas, adecuación de provisiones.")
    if primas_total and primas_total > 0 and siniestros_total is not None:
        ratio_sini = 100 * siniestros_total / primas_total
        st.metric("Primas totales (Cuadro 3)", formato_numero_es(primas_total, 0))
        st.metric("Siniestros pagados (Cuadro 6)", formato_numero_es(siniestros_total, 0))
        st.metric("Ratio siniestros/primas (%)", f"{ratio_sini:.1f}%")
    if not df_res.empty:
        df_res["monto"] = pd.to_numeric(df_res["monto"], errors="coerce")
        tot_res = df_res["monto"].sum()
        st.metric("Reservas técnicas agregado (Cuadro 9)", formato_numero_es(tot_res, 0))
        if primas_total and primas_total > 0:
            st.metric("Ratio reservas técnicas/primas (%)", f"{100 * tot_res / primas_total:.1f}%")
        sub_res = df_res[["concepto", "monto"]].dropna(subset=["monto"]).query("monto > 0")
        if not sub_res.empty:
            st.dataframe(estilizar_df_numeros(sub_res, ["monto"], 0), use_container_width=True, hide_index=True)
    if (not primas_total or not siniestros_total) and df_res.empty:
        st.info("Cargue primas, siniestros y reservas técnicas para indicadores actuariales.")

with tabs[5]:
    st.markdown("**Gestión (Management)**")
    st.caption("Producto de inversiones, ingresos y egresos de la gestión general.")
    if not df_gest.empty:
        df_gest["monto"] = pd.to_numeric(df_gest["monto"], errors="coerce")
        producto = df_gest[df_gest["concepto"].str.upper().str.contains("PRODUCTO DE INVERSIONES|PRODUCTO BRUTO|PRODUCTO NETO", na=False)]
        if not producto.empty:
            st.dataframe(estilizar_df_numeros(producto[["concepto", "monto"]], ["monto"], 0), use_container_width=True, hide_index=True)
        st.caption("**Desglose gestión general (Cuadro 26)**")
        disp_gest = df_gest[["concepto", "monto"]].copy()
        disp_gest = disp_gest[disp_gest["monto"].notna() & (disp_gest["monto"] != 0)]
        if not disp_gest.empty:
            st.dataframe(estilizar_df_numeros(disp_gest, ["monto"], 0), use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos de gestión general (Cuadro 26).")

with tabs[6]:
    st.markdown("**Rentabilidad (Earnings)**")
    st.caption("Utilidad o pérdida del ejercicio por sector.")
    filas = []
    for sector_id in ORDEN_SECTORES:
        if sector_id not in BALANCES_CUADRO_POR_SECTOR:
            continue
        t = totales_sector.get(sector_id, {})
        util = t.get("utilidad_ejercicio") or 0
        perd = t.get("perdida_ejercicio") or 0
        resultado = util - perd
        filas.append({"Sector": SECTORES.get(sector_id, sector_id), "Resultado": resultado})
    if filas:
        df_resul = pd.DataFrame(filas)
        df_resul = df_resul[df_resul["Resultado"] != 0]
        if not df_resul.empty:
            fig_e = px.bar(df_resul, x="Sector", y="Resultado", title="Resultado del ejercicio por sector", color="Resultado", color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
            fig_e.update_layout(showlegend=False, height=360, margin=dict(b=120))
            st.plotly_chart(fig_e, use_container_width=True)
        st.dataframe(estilizar_df_numeros(pd.DataFrame(filas), ["Resultado"], 0), use_container_width=True, hide_index=True)
    if not filas or all(f["Resultado"] == 0 for f in filas):
        st.info("Sin datos de resultado por sector. Cargue balances condensados.")

with tabs[7]:
    st.markdown("**Liquidez**")
    st.caption("Activos de mayor liquidez (depósitos, mesa de dinero) vs. total activo.")
    total_act = totales_sector.get("seguro_directo", {}).get("total_activo")
    if not df_gest.empty and total_act and total_act > 0:
        df_gest["monto"] = pd.to_numeric(df_gest["monto"], errors="coerce")
        liquidez = df_gest[df_gest["concepto"].str.upper().str.contains("DEPÓSITOS A LA VISTA|MESA DE DINERO|Depósitos a la Vista|Mesa de Dinero", na=False)]
        tot_liq = liquidez["monto"].sum() if not liquidez.empty else 0
        if tot_liq >= 0:
            pct_liq = 100 * tot_liq / total_act
            st.metric("Total activo (referencia)", formato_numero_es(total_act, 0))
            st.metric("Conceptos de alta liquidez (gestión)", formato_numero_es(tot_liq, 0))
            st.metric("Proporción aproximada sobre activo (%)", f"{pct_liq:.2f}%")
        st.caption("Indicador aproximado a partir de Cuadro 26 (gestión) y balance. No sustituye el análisis de flujo de caja.")
    else:
        st.info("Insuciente información para estimar liquidez. Se requieren balance y gestión general.")

with tabs[8]:
    st.markdown("**Sensibilidad al riesgo de mercado**")
    st.caption("Composición de inversiones: valores públicos/privados, inmuebles, préstamos.")
    if not df_gest.empty:
        df_gest["monto"] = pd.to_numeric(df_gest["monto"], errors="coerce")
        inv = df_gest[df_gest["concepto"].str.upper().str.contains("INVERSIONES|VALORES|Depósitos|Préstamos|Inmuebles|Muebles|ALQUILERES|DIVIDENDOS", na=False)]
        inv = inv[inv["monto"].notna() & (inv["monto"] > 0)]
        if not inv.empty:
            inv = inv.sort_values("monto", ascending=False)
            fig_s = px.pie(
                inv, values="monto", names="concepto",
                title="Composición de ingresos por tipo de inversión/activo (Cuadro 26)",
                hole=0.55,
                color_discrete_sequence=PALETA_PIE_MODERNA,
            )
            fig_s.update_traces(
                textposition="inside", textinfo="percent+label",
                marker=dict(line=dict(color="white", width=1.5)),
            )
            fig_s.update_layout(**LAYOUT_PIE_MODERNO, height=420)
            st.plotly_chart(fig_s, use_container_width=True)
            st.dataframe(estilizar_df_numeros(inv[["concepto", "monto"]], ["monto"], 0), use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos de gestión general para composición de inversiones.")

st.markdown("---")
st.caption("**CARAMELS** es un marco de supervisión usado en la evaluación de entidades de seguro. Este análisis se basa únicamente en los cuadros del anuario estadístico disponibles en el dashboard; no sustituye la evaluación oficial del supervisor.")
