# Dashboard centrado en Anuario "Seguro en Cifras"

Estructura del dashboard enfocada **solo en la información de los anuarios**, con flujo de lo general a lo detallado (macro → micro) y posibilidad de expandir después con otras fuentes.

---

## 1. Principios

- **Una sola fuente inicial**: anuario (schema `anuario` en Supabase). Otras fuentes (primas mensuales, Excel) se integrarán después.
- **Misma lógica que los cuadros**: de lo **macro** (indicadores agregados, resúmenes por sector) a lo **micro** (detalle por ramo, por empresa, cuadros específicos).
- **Por sector** en cada sección cuando aplique: **Seguro directo**, **Reaseguro**, **Financiadoras de primas**, **Medicina prepagada**.
- **Subpestañas** dentro de cada sección (Primas, Siniestros, Reservas, Balances, etc.) para no saturar el menú y mantener el orden general → detalle.

---

## 2. Navegación (sidebar)

```
Anuario Seguro en Cifras
────────────────────────────────────
  Inicio              (resumen macro)
  Primas              (subpestañas internas)
  Siniestros          (subpestañas internas)
  Reservas            (subpestañas internas)
  Balances            (subpestañas internas)
  Estados de resultado
  Indicadores y gestión
  Listados y empresas
  Catálogo de cuadros
────────────────────────────────────
  [Año: 2023 ▼]
```

- **Año**: selector único en sidebar; aplica a todas las vistas que usen filtro por año.

---

## 3. Estructura por sección (macro → micro)

### 3.1 Inicio
- **Indicadores macro**: total cuadros en catálogo, años disponibles, filas cargadas por tabla temática (balances, listados, etc.), sectores con datos.
- **Gráfico o resumen** opcional: por ejemplo totales de balance por sector (activo/pasivo) si hay datos.
- Enlace rápido a cada sección (Primas, Siniestros, Reservas, Balances, Listados).

### 3.2 Primas
- **Indicadores macro** (arriba): primas totales por sector cuando existan datos (tabla `primas_por_ramo`).
- **Subpestañas**:
  - **Por ramo** (cuadros 3, 5-A, 5-B, 5-C): tabla por sector; columnas ramo, seguro_directo, reaseguro, total, %.
  - **Por ramo y empresa** (cuadro 4): desglose por empresa.
- Dentro de cada subpestaña: filtro o tabs por **sector** (Seguro directo / Reaseguro / Financiadoras / Medicina prepagada) cuando el cuadro aplique a varios sectores.
- *Hoy*: sin datos cargados → mensaje "Próximamente" o "Cargar ETL primas_por_ramo".

### 3.3 Siniestros
- **Indicadores macro**: totales por sector si hay datos (`siniestros_por_ramo`).
- **Subpestañas**:
  - **Por ramo** (cuadro 6).
  - **Por ramo y empresa** (cuadro 7).
  - **Personas / Patrimoniales / Obligacionales** (cuadros 8-A, 8-B, 8-C).
- En cada una: vista por sector (tabs o filtro) y tabla detalle.
- *Hoy*: sin datos → "Próximamente".

### 3.4 Reservas
- **Indicadores macro**: agregados de reservas técnicas, prima, prestaciones (cuando existan tablas cargadas).
- **Subpestañas**:
  - **Técnicas agregado** (9).
  - **Prima por ramo** (10).
  - **Prima por empresa** (11 a 14).
  - **Prestaciones por ramo** (15).
  - **Prestaciones por empresa** (16 a 19).
  - **Detalle por ramo/empresa** (20-A a 20-F).
  - **Inversiones reservas técnicas** (21).
  - **Hospitalización** (32, 33).
- En cada subpestaña: indicadores si aplican, luego tabla por sector/cuadro.
- *Hoy*: sin datos → "Próximamente".

### 3.5 Balances
- **Indicadores macro**: totales activo/pasivo por sector (cuadros 24, 40, 47, 54) — **con datos hoy**.
- **Subpestañas**:
  - **Resumen por sector**: los cuatro balances en una vista (tabs: Seguro directo, Reaseguro, Financiadoras, Medicina prepagada); en cada tab, tabla concepto / monto.
  - **Balance por empresa (reaseguros)** (cuadro 42): cuando se cargue.
- Gráficos opcionales: barras activo vs pasivo por sector.
- *Hoy*: balances_condensados cargados → contenido real por sector.

### 3.6 Estados de resultado (ingresos y egresos)
- **Indicadores macro**: totales ingresos/egresos por sector si hay datos.
- **Subpestañas por sector** (o por cuadro):
  - Seguro directo (25-A, 25-B).
  - Reaseguro (41-A, 41-B).
  - Financiadoras (48).
  - Medicina prepagada (55-A, 55-B).
- *Hoy*: sin datos → "Próximamente".

### 3.7 Indicadores y gestión
- **Indicadores macro**: resumen de indicadores financieros, suficiencia patrimonio (cuando existan).
- **Subpestañas**:
  - **Gestión general** (26).
  - **Indicadores financieros por empresa** (29, 44, 52, 58) — por sector.
  - **Suficiencia patrimonio** (30, 45).
  - **Series históricas primas** (31-A, 31-B).
  - **Gastos vs primas** (22, 23, 23-A a 23-F).
  - **Datos por empresa** (27, 28, 34, 35, 36, 49, 50, 51, 56, 57).
  - **Cantidad pólizas y siniestros** (37, 38).
- *Hoy*: sin datos → "Próximamente".

### 3.8 Listados y empresas
- **Indicadores macro**: número de empresas por sector (reaseguro, financiadoras, medicina prepagada) — **con datos hoy**.
- **Subpestañas por sector**:
  - **Reaseguro** (cuadro 39): empresas autorizadas.
  - **Financiadoras de primas** (cuadro 46).
  - **Medicina prepagada** (cuadro 53).
- En cada tab: tabla número de orden, nombre de empresa.
- *Hoy*: listados_empresas cargado → contenido real.

### 3.9 Catálogo de cuadros
- Tabla completa `anuario.cuadros`: cuadro_id, nombre, sector.
- Filtro por sector.
- Referencia para saber qué cuadro corresponde a cada vista.

---

## 4. Patrón de cada página

1. **Título** de la sección.
2. **Selector de año** (sidebar o arriba) aplicado a todas las tablas con `anio`.
3. **Bloque de indicadores macro** (métricas en columnas): totales, conteos, por sector si aplica.
4. **Subpestañas** (Streamlit `st.tabs`): cada una con nombre claro (cuadro o tema).
5. Dentro de cada subpestaña:
   - Opcional: mini indicadores o texto explicativo.
   - **Por sector** si aplica: tabs o selectbox (Seguro directo, Reaseguro, Financiadoras, Medicina prepagada).
   - **Tabla** de detalle (dataframe con formato numérico).
   - Opcional: **gráfico** (barras, líneas) cuando los datos lo permitan.
6. Si no hay datos: mensaje único "No hay datos cargados para esta sección. Ejecute el ETL correspondiente." y referencia al cuadro/tabla temática.

---

## 5. Sectores (etiquetas)

| Código schema | Etiqueta en dashboard |
|---------------|------------------------|
| seguro_directo | Seguro directo |
| reaseguro | Reaseguro |
| financiadoras_primas | Financiadoras de primas |
| medicina_prepagada | Medicina prepagada |

---

## 6. Datos cargados hoy vs preparado para después

| Sección | Tabla(s) anuario | Estado |
|---------|-------------------|--------|
| Inicio | cuadros, conteos | Catálogo y conteos OK; métricas por tabla según carga. |
| Primas | primas_por_ramo, primas_por_ramo_empresa | Estructura lista; sin ETL → "Próximamente". |
| Siniestros | siniestros_por_ramo | Idem. |
| Reservas | 9 tablas temáticas | Idem. |
| Balances | balances_condensados | **Con datos** (24, 40, 47, 54). |
| Estados resultado | estados_ingresos_egresos | Estructura lista; sin datos. |
| Indicadores y gestión | varias | Estructura lista; sin datos. |
| Listados y empresas | listados_empresas | **Con datos** (39, 46, 53). |
| Catálogo | cuadros | **Con datos**. |

---

## 7. Expansión futura

- Añadir **otras fuentes** (primas mensuales, Excel): nueva sección en sidebar o submenú "Datos operativos" sin cambiar la lógica de las secciones del anuario.
- Cargar más tablas temáticas vía ETL: las páginas ya tienen subpestañas y sectores definidos; solo conectar a las nuevas tablas y quitar el mensaje "Próximamente".
- Añadir **más años**: el selector de año ya está previsto; al cargar más años en Supabase, las vistas los mostrarán.

---

## 8. Implementación (Streamlit)

- **Entrada**: `app.py` = Inicio (indicadores macro, enlaces a secciones).
- **Páginas** (carpeta `pages/`):  
  `1_Primas.py`, `2_Siniestros.py`, `3_Reservas.py`, `4_Balances.py`, `5_Estados_Resultado.py`, `6_Indicadores_Gestion.py`, `7_Listados_Empresas.py`, `8_Catalogo_Cuadros.py`.
- **Config compartida**: `src/app/anuario_config.py` (sectores, cuadros por sector para balances y listados).
- Las páginas de datos operativos anteriores (Resumen, Primas/Siniestros, Por Empresa, Anuario único) se sustituyeron por esta estructura centrada en el anuario.
- **Ejecución local**: `streamlit run app.py`
