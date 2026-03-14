# Inicio.py — Página de inicio del aplicativo (ejecutar: streamlit run Inicio.py)
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_env = ROOT / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

import streamlit as st

from src.app.components.auth import check_auth_required, render_login_or_session, logout_button
from src.app.anuario_config import APP_NAME, render_sidebar_footer, render_sidebar_logo, LOGO_ACTUARIAL_CORTEX_INICIO

st.set_page_config(
    page_title=f"Inicio | {APP_NAME}",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

if check_auth_required() and not render_login_or_session():
    st.stop()

logout_button()

st.sidebar.title(APP_NAME)
st.sidebar.caption("Datos del anuario estadístico")
st.sidebar.markdown("---")
anio = st.sidebar.selectbox("Año", options=[2023, 2022, 2021], index=0, key="inicio_anio")
render_sidebar_footer()

st.title("Inicio")
try:
    st.image(LOGO_ACTUARIAL_CORTEX_INICIO, width=280)
except Exception:
    pass
st.markdown("---")
st.markdown("""
**[Actuarial Cortex](https://actuarial-cortex.pages.dev/)** es un hub de conocimiento y tecnología actuarial. Este **dashboard** forma parte de su oferta para el sector asegurador: explota el anuario «Seguro en Cifras» de la Superintendencia de la Actividad Aseguradora.
""")
st.markdown("---")
st.subheader("¿Qué es este aplicativo?")
st.markdown("""
Este dashboard permite consultar, por año y por sector, las cifras de **primas**, **siniestros**, **reservas**, **balances**, **estados de resultado**, **listados de empresas** y **capital y garantía**, además de un **análisis CARAMELS** y la descripción del **proceso y flujo** de los datos.
""")

st.subheader("Secciones que lo conforman")
st.markdown("""
- **Cifras por sector** — Resumen con resultado por sector, totales de balance (activo, pasivo, utilidad/pérdida) y vista previa de balances y empresas autorizadas.
- **Primas** — Cuadros por ramo (general, Personas, Patrimoniales, Obligacionales) y por ramo y empresa; gráficos de distribución.
- **Siniestros** — Por ramo, por ramo y empresa, y por tipo (Personas, Patrimoniales, Obligacionales).
- **Reservas** — Reservas técnicas agregado, de prima por ramo, de prestaciones por ramo y otras tablas temáticas.
- **Balances** — Balances condensados por sector (Empresas de Seguro, Reaseguro, Financiadoras de Primas, Medicina Prepagada) con indicadores y detalle.
- **Estados de resultado** — Ingresos y egresos por sector.
- **Indicadores y gestión** — Gestión general (Cuadro 26) y otras secciones de indicadores.
- **Análisis CARAMELS** — Evaluación por dimensiones: Capital, Activos, Reaseguro, Actuarial, Gestión, Rentabilidad, Liquidez, Sensibilidad.
- **Listados y empresas** — Empresas autorizadas por sector y tabla de capital y garantía por empresa.
- **Catálogo de cuadros** — Referencia de todos los cuadros del anuario.
- **Proceso y flujo** — Descripción del flujo de datos (extracción, consolidación, esquema, ETL, dashboard).
""")

st.markdown("---")
st.subheader("Datos técnicos — Balances condensados por sector")
st.caption(f"Resumen del balance por tipo de empresa (año {anio}). Unidad: miles de bolívares. Tres indicadores por sector y detalle desplegable.")

# Cargar balances y mostrar 3 tacómetros + data desplegable por sector
from src.app.components.data_loader import load_anuario_balances_condensados
from src.app.anuario_config import (
    SECTORES,
    BALANCES_CUADRO_POR_SECTOR,
    ORDEN_SECTORES,
    extraer_totales_balance,
    formato_numero_es,
    filtrar_encabezados_balance,
    estilizar_df_numeros,
)
import pandas as pd
import plotly.graph_objects as go

df_balances_inicio = load_anuario_balances_condensados(anio=anio)
sectores_bal_inicio = [s for s in ORDEN_SECTORES if s in BALANCES_CUADRO_POR_SECTOR]

if not df_balances_inicio.empty and sectores_bal_inicio:
    # Calcular máximos para escalar gauges (0-100)
    totales_inicio = {}
    for sid in sectores_bal_inicio:
        cid = BALANCES_CUADRO_POR_SECTOR[sid]
        sub = df_balances_inicio[df_balances_inicio["cuadro_id"] == cid][["concepto", "monto"]].copy()
        totales_inicio[sid] = extraer_totales_balance(sub)
    max_act = max((t.get("total_activo") or 0) for t in totales_inicio.values())
    max_pas = max((t.get("total_pasivo") or 0) for t in totales_inicio.values())
    resultados = [(t.get("utilidad_ejercicio") or 0) - (t.get("perdida_ejercicio") or 0) for t in totales_inicio.values()]
    r_min, r_max = min(resultados), max(resultados)
    r_range = (r_max - r_min) or 1

    for sector_id in sectores_bal_inicio:
        nombre_sector = SECTORES.get(sector_id, sector_id)
        cuadro_id = BALANCES_CUADRO_POR_SECTOR[sector_id]
        sub_bal = df_balances_inicio[df_balances_inicio["cuadro_id"] == cuadro_id][["concepto", "monto"]].copy()
        t = totales_inicio[sector_id]
        act = t.get("total_activo") or 0
        pas = t.get("total_pasivo") or 0
        util = t.get("utilidad_ejercicio") or 0
        perd = t.get("perdida_ejercicio") or 0
        res = util - perd
        pct_act = 100 * act / max_act if max_act > 0 else 0
        pct_pas = 100 * pas / max_pas if max_pas > 0 else 0
        pct_res = 100 * (res - r_min) / r_range if r_range else 50

        st.markdown(f"**{nombre_sector}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            fig_a = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(pct_act, 0),
                number={"suffix": "%", "font": {"size": 14}},
                title={"text": "Peso en total activo", "font": {"size": 11}},
                gauge=dict(
                    axis=dict(range=[0, 100]),
                    bar=dict(color="#1e40af"),
                    steps=[dict(range=[0, 100], color="rgba(30, 64, 175, 0.15)")],
                    threshold=dict(line=dict(color="navy", width=2), value=pct_act),
                ),
            ))
            fig_a.update_layout(height=200, margin=dict(l=20, r=20, t=45, b=10), font=dict(size=11), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_a, use_container_width=True)
            st.caption(formato_numero_es(act, 0))
        with col2:
            fig_p = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(pct_pas, 0),
                number={"suffix": "%", "font": {"size": 14}},
                title={"text": "Peso en total pasivo", "font": {"size": 11}},
                gauge=dict(
                    axis=dict(range=[0, 100]),
                    bar=dict(color="#64748b"),
                    steps=[dict(range=[0, 100], color="rgba(100, 116, 139, 0.15)")],
                    threshold=dict(line=dict(color="gray", width=2), value=pct_pas),
                ),
            ))
            fig_p.update_layout(height=200, margin=dict(l=20, r=20, t=45, b=10), font=dict(size=11), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_p, use_container_width=True)
            st.caption(formato_numero_es(pas, 0))
        with col3:
            fig_r = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(pct_res, 0),
                number={"suffix": "%", "font": {"size": 14}},
                title={"text": "Resultado (relativo)", "font": {"size": 11}},
                gauge=dict(
                    axis=dict(range=[0, 100]),
                    bar=dict(color="#0f766e" if res >= 0 else "#b91c1c"),
                    steps=[dict(range=[0, 100], color="rgba(15, 118, 110, 0.1)")],
                    threshold=dict(line=dict(color="teal" if res >= 0 else "darkred", width=2), value=pct_res),
                ),
            ))
            fig_r.update_layout(height=200, margin=dict(l=20, r=20, t=45, b=10), font=dict(size=11), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_r, use_container_width=True)
            st.caption(formato_numero_es(res, 0) + (" (utilidad)" if res >= 0 else " (pérdida)"))

        with st.expander(f"Ver detalle balance — {nombre_sector}", expanded=False):
            sub_det = sub_bal.copy()
            sub_det["monto"] = pd.to_numeric(sub_det["monto"], errors="coerce")
            sub_det = filtrar_encabezados_balance(sub_det).head(20)
            if not sub_det.empty:
                st.dataframe(estilizar_df_numeros(sub_det, ["monto"], 0), use_container_width=True, hide_index=True)
            else:
                st.caption("Sin detalle.")

        st.markdown("---")
else:
    st.caption("Sin datos de balances. Ejecute el ETL: `python scripts/etl_anuario_a_supabase.py --year 2023` y limpie caché.")

st.markdown("---")
st.subheader("¿Por qué algunas tablas o pestañas están vacías?")
with st.expander("Cómo cargar los datos del anuario", expanded=False):
    st.markdown("""
    El dashboard **lee desde Supabase** (schema `anuario`). Si las tablas están vacías, es porque aún no se han cargado los datos.

    **Pasos para que aparezcan los datos:**

    1. **Configurar Supabase:** En el proyecto de Supabase, tener el schema `anuario` expuesto en la Data API y las variables de entorno `SUPABASE_URL` y `SUPABASE_KEY` en el `.env` del proyecto.

    2. **Ejecutar las migraciones en Supabase:** En el SQL Editor de Supabase, ejecutar los scripts en `data/db/schema/` en orden (001, 002, …). Para el **Cuadro 7** (siniestros por ramo y empresa) hace falta ejecutar además la **migración 007** (`007_anuario_siniestros_por_ramo_empresa.sql`), que crea la tabla `siniestros_por_ramo_empresa`.

    3. **Tener los CSV del anuario:** Los archivos CSV verificados del anuario deben estar en la carpeta **`data/staged/<año>/verificadas/`** (por ejemplo `data/staged/2023/verificadas/`), con los nombres esperados por el ETL (p. ej. `cuadro_07_siniestros_por_ramo_empresa.csv`, etc.).

    4. **Ejecutar el ETL:** Desde la raíz del proyecto ejecutar:
    ```bash
    python scripts/etl_anuario_a_supabase.py --year 2023
    ```
    (o el año que corresponda). El script carga en Supabase: listados, capital y garantía, balances, cuadros, primas por ramo y por empresa, estados de resultado, gestión general, siniestros por ramo y por empresa (Cuadro 7), reservas técnicas, reservas prima por ramo (Cuadro 10) y reservas prestaciones por ramo (Cuadro 15).

    5. **Limpiar caché del dashboard:** En Streamlit, menú **Ejecutar → Limpiar caché** para que el dashboard vuelva a leer de Supabase.

    **Cuadros que aún no tienen ETL:** Los **Cuadros 11-14** (reservas de prima por empresa) y **16-19** (reservas de prestaciones por empresa) no están incluidos en el ETL actual; esas pestañas seguirán vacías hasta que se añada la carga para esos cuadros.
    """)
st.caption("Si ya ejecutaste las migraciones y el ETL y sigues viendo tablas vacías, revisa que los CSV estén en `data/staged/<año>/verificadas/` y que en Supabase el schema **anuario** esté expuesto en la Data API.")

st.markdown("---")
st.subheader("Elaborado por")
st.markdown("""
**Prof. Angel Colmenares**

- Correo: **angelc.ucv@gmail.com**
- Perfil en LinkedIn: [angel-colmenares-a2ab06204](https://ve.linkedin.com/in/angel-colmenares-a2ab06204)
""")
st.markdown("---")
