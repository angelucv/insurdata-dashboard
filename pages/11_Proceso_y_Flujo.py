# pages/9_Proceso_y_Flujo.py — Descripción general del flujo de proceso del anuario
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.app.anuario_config import APP_NAME, render_sidebar_footer

st.set_page_config(page_title=f"Proceso y flujo | {APP_NAME}", page_icon="🔄", layout="wide")
st.sidebar.caption(APP_NAME)
render_sidebar_footer()

st.title("Proceso y flujo del anuario")
st.caption("Descripción general del flujo de datos y procesos utilizados en este demo.")

st.markdown("---")

st.subheader("1. Extracción tabla a tabla")
st.markdown("""
Los datos del anuario estadístico se obtienen a partir de documentos oficiales (PDF).  
Se realiza una **extracción tabla a tabla**: cada cuadro o tabla del documento se procesa de forma independiente, 
conservando estructura, encabezados y filas. El resultado de cada cuadro se almacena en archivos intermedios 
normalizados (por ejemplo, por año y por número de cuadro) para poder revisarlos y validarlos antes de integrarlos.
""")

st.subheader("2. Criterios de cruce inter e intra tablas")
st.markdown("""
- **Intra tabla:** Dentro de un mismo cuadro se mantienen las relaciones entre columnas (conceptos, montos, tipos de línea) 
  y se identifican filas de subtotal o sección (por ejemplo, totales por ramo o por tipo de seguro) para poder 
  explotarlos en indicadores y gráficos.
- **Inter tablas:** Las tablas se relacionan mediante **identificadores de cuadro** y **año**. Sectores (seguro directo, 
  reaseguro, financiadoras de primas, medicina prepagada) y tipos de dato (primas, siniestros, reservas, balances, 
  estados de resultado) permiten cruzar y filtrar la información de forma coherente en todo el anuario.
""")

st.subheader("3. Consolidación de la información")
st.markdown("""
La información extraída se **consolida** en estructuras temáticas: no se guarda “cuadro por cuadro” suelto, 
sino que se agrupa por tema (por ejemplo, primas por ramo, primas por ramo y empresa, siniestros por ramo, 
reservas técnicas, balances condensados, estados de ingresos y egresos). Así se facilita la consulta, 
el análisis y la presentación en un mismo lugar de todos los datos relacionados con un mismo concepto.
""")

st.subheader("4. Conformación del esquema para la base de datos")
st.markdown("""
Se diseña un **esquema de base de datos** que refleja esas estructuras temáticas: tablas por dimensión (por ejemplo, 
catálogo de cuadros, sectores) y tablas de hechos (primas, siniestros, reservas, balances, etc.) con columnas 
que permiten año, cuadro de origen y datos numéricos o textuales. Se definen claves, índices y políticas de 
acceso para que la información sea consultable de forma segura y eficiente.
""")

st.subheader("5. Carga en nube")
st.markdown("""
Los datos consolidados se **cargan en una base de datos en la nube**. El proceso de carga está pensado para 
ejecutarse por año (o por lotes), de forma que se pueda actualizar o ampliar la información sin duplicar 
registros. La conexión se hace mediante credenciales seguras y solo se exponen los esquemas y tablas 
necesarios para la lectura desde el dashboard.
""")

st.subheader("6. Configuración del dashboard y conexión con la base de datos")
st.markdown("""
El **dashboard** se configura para leer únicamente desde la base de datos en la nube (no desde archivos locales 
en tiempo de ejecución). La conexión se realiza mediante una capa de acceso a datos que centraliza la lectura 
por tabla temática y aplica caché para no saturar la base. Las pantallas se organizan por secciones (Primas, 
Siniestros, Reservas, Balances, Estados de resultado, Listados, etc.) y permiten filtrar por año y, cuando 
aplica, por sector o tipo de cuadro.
""")

st.subheader("7. Procesos ETL intermedios")
st.markdown("""
Entre la extracción y la carga en nube existen **procesos ETL intermedios** (extracción, transformación y carga):
- **Extracción:** lectura de los archivos ya generados por cuadro.
- **Transformación:** normalización de nombres de columnas, tipos de dato (números, fechas), y en algunos casos 
  agregación (por ejemplo, sumar por ramo cuando el origen es por empresa) para alimentar tablas resumen.
- **Carga:** borrado o actualización por año (o por cuadro) y posterior inserción en las tablas de la base en la nube, 
  de forma que cada ejecución sea repetible y controlable.
""")

st.subheader("8. Ampliación y mejora gradual")
st.markdown("""
El flujo está pensado para **ampliarse y mejorarse de forma gradual**:
- Incorporar nuevos cuadros o nuevos años sin cambiar la lógica general.
- Añadir más tablas temáticas o más columnas cuando el anuario lo permita.
- Mejorar la extracción (por ejemplo, manejo de PDF con tablas complejas o escaneados).
- Incluir validaciones (totales vs. sumas de filas, cruces entre cuadros) y alertas cuando no cuadren.
- Extender el dashboard con más gráficos, exportación o comparativas entre años o sectores.
""")

st.markdown("---")
st.info("""
**Demo inicial** — Este dashboard es una primera versión de explotación del anuario estadístico, 
desarrollada por el **Profesor Angel Colmenares**, con fines docentes y de divulgación. 
La información mostrada proviene de los cuadros oficiales del anuario; para uso institucional 
o publicación se recomienda contrastar siempre con las fuentes originales.
""")
