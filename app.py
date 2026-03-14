# app.py — Página de inicio (para que el menú muestre "Inicio", ejecute: streamlit run Inicio.py)
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
from src.app.anuario_config import APP_NAME, render_sidebar_footer, render_sidebar_logo, get_inicio_logo_url

st.set_page_config(
    page_title=f"Inicio | {APP_NAME}",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

if check_auth_required() and not render_login_or_session():
    st.stop()

logout_button()

render_sidebar_logo()
st.sidebar.title(APP_NAME)
st.sidebar.caption("Datos del anuario estadístico")
st.sidebar.markdown("---")
st.sidebar.selectbox("Año", options=[2023, 2022, 2021], index=0, key="inicio_anio")
render_sidebar_footer()

# Logo principal Actuarial Cortex (logo-actuarial-cortex-principal-blanco) en la página de inicio
logo_url = get_inicio_logo_url()
if logo_url:
    try:
        st.image(logo_url, use_container_width=True)
    except Exception:
        pass
st.markdown("---")
st.title("Inicio")
st.markdown("---")

st.subheader("¿Qué es este aplicativo?")
st.markdown("""
Este **dashboard** explota los datos del **anuario estadístico «Seguro en Cifras»** de la Superintendencia de la Actividad Aseguradora.  
Permite consultar, por año y por sector, las cifras de **primas**, **siniestros**, **reservas**, **balances**, **estados de resultado**, **listados de empresas** y **capital y garantía**, además de un **análisis CARAMELS** y la descripción del **proceso y flujo** de los datos.
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
st.subheader("Elaborado por")
st.markdown("""
**Prof. Angel Colmenares**

- Correo: **angelc.ucv@gmail.com**
- Perfil en LinkedIn: [angel-colmenares-a2ab06204](https://ve.linkedin.com/in/angel-colmenares-a2ab06204)
""")
st.markdown("---")
