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
        st.image(logo_url, width=280)
    except Exception:
        pass
st.markdown("---")
st.title("Inicio")

with st.expander("Short English summary", expanded=True):
    st.markdown(
        "This demo turns the Venezuelan insurance supervisor’s statistical yearbook **“Seguro en Cifras”** "
        "into an interactive analytical dashboard. It consolidates historical data from PDF and Excel files into "
        "a relational database, builds technical and regulatory indicators under a **CARAMELS**-inspired framework, "
        "and illustrates how similar tools can be adapted to insurers, reinsurers, prepaid medicine companies and "
        "service providers to obtain tailored, near real-time financial and risk insights.\n\n"
        "The project is developed within **Actuarial Cortex**, a personal hub of actuarial knowledge and technology "
        "([https://actuarial-cortex.pages.dev](https://actuarial-cortex.pages.dev))."
    )

st.markdown("---")

st.markdown("""
**[Actuarial Cortex](https://actuarial-cortex.pages.dev/)** es un hub de conocimiento y tecnología actuarial. Este **dashboard** forma parte de su oferta para el sector asegurador: explota el anuario «Seguro en Cifras» de la Superintendencia de la Actividad Aseguradora.

*Los datos mostrados provienen del anuario estadístico oficial «Seguro en Cifras» (SUDEASEG).*

_El sitio web de Actuarial Cortex está en construcción, pero ya permite explorar el contexto general del proyecto y otros demos relacionados._
""")
st.markdown("---")
st.subheader("¿Qué es este aplicativo?")
st.markdown("""
El anuario estadístico **«Seguro en Cifras»** concentra la mejor fotografía disponible del mercado asegurador venezolano, pero durante años ha estado distribuido en anuarios PDF y, más recientemente, en libros Excel que heredan decisiones de indexación que dificultan el análisis histórico fino (como cuadros que fijan 2007 como año base y dejan períodos completos en cero). Este proyecto busca transformar ese insumo en una base analítica coherente y explotable.

Este demo es el primer bloque de una suite de análisis actuarial y regulatorio que persigue:

- Integrar la serie histórica del anuario (PDF + Excel) en una **base de datos relacional** estructurada, apoyada en procesos de **extracción, transformación y carga (ETL)** que convierten tablas de los anuarios y archivos PDF en datos accionables.
- Reorganizar la lectura sectorial en vistas claras de **primas**, **siniestros**, **reservas**, **balances**, **estados de resultado**, **indicadores de gestión** e interpretación bajo un marco **CARAMELS** adaptado al contexto venezolano.
- Generar indicadores derivados que respeten la trazabilidad con los cuadros oficiales, pero que acerquen el lenguaje del anuario a la gestión diaria del riesgo y la solvencia.
- Preparar el terreno para un segundo demo centrado en **estados financieros analíticos por empresa**, con indicadores profundos de solvencia, rentabilidad y eficiencia.

Más allá del anuario, este demo ilustra el tipo de soluciones que pueden desplegarse sobre los estados financieros propios de cada actor del ecosistema: aseguradoras, reaseguradoras, empresas de medicina prepagada, prestadores de servicios y otras organizaciones que necesiten ver sus datos contables como paneles de control vivos, adaptados a su realidad y con métricas accionables en tiempo casi real.
""")

with st.expander("Short English summary"):
    st.markdown(
        "This demo turns the Venezuelan insurance supervisor’s statistical yearbook **“Seguro en Cifras”** "
        "into an interactive analytical dashboard. It consolidates historical data from PDF and Excel files into "
        "a relational database, builds technical and regulatory indicators under a **CARAMELS**-inspired framework, "
        "and illustrates how similar tools can be adapted to insurers, reinsurers, prepaid medicine companies and "
        "service providers to obtain tailored, near real-time financial and risk insights.\n\n"
        "The project is developed within **Actuarial Cortex**, a personal hub of actuarial knowledge and technology "
        "([https://actuarial-cortex.pages.dev](https://actuarial-cortex.pages.dev))."
    )

st.subheader("¿Cómo usar este dashboard?")
st.markdown("""
1. Seleccione el **año** en la barra lateral.
2. Revise el módulo de **Cifras por sector** para tener una visión panorámica de activos, pasivos y resultados por tipo de entidad.
3. Profundice en **Primas**, **Siniestros**, **Reservas**, **Balances** y **Estados de resultado** según el foco de análisis.
4. Utilice **Indicadores y gestión** y el **Análisis CARAMELS** para una lectura estructurada del perfil de riesgo y desempeño.
""")

st.subheader("¿Quiénes pueden aprovecharlo?")
st.markdown("""
- **Reguladores y supervisores**: para apoyar la vigilancia del mercado, la lectura CARAMELS y la comparación de indicadores entre sectores.
- **Compañías de seguros, reaseguros y medicina prepagada**: como referencia para diseñar tableros propios a partir de sus estados financieros analíticos.
- **Academia y analistas**: para estudiar la evolución del mercado y construir casos de estudio en cursos de seguros, riesgo y regulación.
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

st.subheader("Glosario rápido")
st.markdown("""
- **Reservas técnicas**: obligaciones estimadas que respaldan los compromisos con los asegurados (prima no devengada, prestaciones, otras reservas).
- **IBNR**: siniestros ocurridos pero no reportados; parte clave de las reservas de prestaciones.
- **Capital y garantía**: recursos propios y exigencias patrimoniales que respaldan la operación de las entidades supervisadas.
- **CARAMELS**: marco de supervisión que resume la situación de una entidad en ocho dimensiones: Capital, Activos, Reaseguro, Actuarial, Gestión, Rentabilidad, Liquidez y Sensibilidad.
""")

st.info(
    "Esta es una **versión demo** basada en datos consolidados del anuario «Seguro en Cifras». "
    "El despliegue productivo puede adaptarse a los estados financieros y necesidades específicas de cada entidad."
)

with st.expander("Short English summary"):
    st.markdown(
        "This demo turns the Venezuelan insurance supervisor’s statistical yearbook **“Seguro en Cifras”** "
        "into an interactive analytical dashboard. It consolidates historical data from PDF and Excel files into "
        "a relational database, builds technical and regulatory indicators under a **CARAMELS**-inspired framework, "
        "and illustrates how similar tools can be adapted to insurers, reinsurers, prepaid medicine companies and "
        "service providers to obtain tailored, near real-time financial and risk insights.\n\n"
        "The project is developed within **Actuarial Cortex**, a personal hub of actuarial knowledge and technology "
        "([https://actuarial-cortex.pages.dev](https://actuarial-cortex.pages.dev))."
    )

st.markdown("---")
st.subheader("Elaborado por")
st.markdown("""
**Prof. Angel Colmenares**

- Correo: **angelc.ucv@gmail.com**
- Perfil en LinkedIn: [angel-colmenares-a2ab06204](https://ve.linkedin.com/in/angel-colmenares-a2ab06204)
""")
st.markdown("---")

st.subheader("Próximos pasos")
st.markdown("""
- Ampliar la serie histórica incorporando progresivamente los años previos a 2023 a partir de los anuarios en PDF.
- Integrar de forma sistemática los libros Excel publicados por SUDEASEG a partir de 2024.
- Desarrollar un **segundo demo** orientado a estados financieros analíticos por empresa, con indicadores avanzados de solvencia, rentabilidad y eficiencia, conectado con este dashboard sectorial.
""")
