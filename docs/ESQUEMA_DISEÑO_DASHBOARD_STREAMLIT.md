# Esquema de diseño: Dashboard Streamlit SUDEASEG

Propuesta de estructura del dashboard antes de publicar, alineada con las fuentes de datos actuales (primas/entidades en `public` y anuario en schema `anuario`). Revisar y aprobar antes de implementar.

---

## 1. Fuentes de datos (resumen)

| Fuente | Schema / tablas | Uso en dashboard |
|--------|-----------------|------------------|
| **Datos operativos** | `public`: primas_mensuales, entities, series_historicas | Resumen, Primas/Siniestros, Por empresa |
| **Anuario "Seguro en Cifras"** | `anuario`: cuadros, balances_condensados, listados_empresas (+ 20 tablas temáticas futuras) | Sección Anuario |

---

## 2. Navegación general (sidebar)

```
📊 SUDEASEG Dashboard
   Inteligencia de datos del sector asegurador venezolano
────────────────────────────────────────────
🏠 Inicio
📈 Resumen
💰 Primas y Siniestros
🏢 Por Empresa
────────────────────────────────────────────
📋 Anuario Seguro en Cifras   ← bloque anuario
   ├── Resumen anuario
   ├── Por sector
   └── Catálogo de cuadros
────────────────────────────────────────────
[Login/Logout según REQUIRE_AUTH]
```

- **Inicio**: página principal (actual `app.py`).
- **Resumen / Primas / Por Empresa**: sin cambios de lógica; solo revisión visual y mensajes cuando no hay datos.
- **Anuario**: agrupado en una sección clara; dentro, subvistas o una sola página con pestañas (según preferencia).

---

## 3. Estructura propuesta por página

### 3.1 Inicio (`app.py`)

| Elemento | Contenido |
|----------|-----------|
| **Título** | Inteligencia de Datos del Sector Asegurador Venezolano |
| **Subtítulo** | Superintendencia de la Actividad Aseguradora — Extracción, modelado y visualización |
| **Si hay primas** | 3 métricas: Registros, Periodos, Entidades + vista previa tabla (primeras filas) |
| **Si no hay primas** | Mensaje claro: ejecutar ETL o configurar Supabase + enlace a documentación |
| **Bloque Anuario** | Breve resumen: “Anuario Seguro en Cifras: X cuadros, datos 2023” con enlace a la página Anuario (si hay datos en `anuario`) |

Objetivo: que en una sola pantalla se vea el estado de ambas fuentes (operativos + anuario).

---

### 3.2 Resumen (`1_Resumen.py`)

- Mantener: KPIs (registros, entidades, periodos, primas totales), gráfico de evolución, series históricas.
- Mejoras: mensaje explícito si no hay datos; formato numérico consistente (separadores de miles, decimales).

---

### 3.3 Primas y Siniestros (`2_Primas_Siniestros.py`)

- Mantener: filtro por periodo, selector de métrica, histograma, top entidades, tabla.
- Mejoras: etiquetas claras (ej. “Primas netas VES”), manejo cuando no hay columnas numéricas.

---

### 3.4 Por Empresa (`3_Por_Empresa.py`)

- Mantener: selector de entidad, evolución temporal, tabla.
- Mejoras: opcional mostrar nombre de entidad (si existe `entities`) y mensaje cuando no hay datos.

---

### 3.5 Anuario Seguro en Cifras (`4_Anuario_Seguro_En_Cifras.py`) — rediseño

Objetivo: mostrar la información del anuario de forma **minuciosa** y alineada con la estructura de datos (catálogo, sectores, tablas temáticas).

#### 3.5.1 Contenido de la página (una sola página con secciones)

| Orden | Sección | Contenido |
|-------|---------|-----------|
| 1 | **Cabecera** | Título “Anuario Seguro en Cifras”, nota de que los datos vienen del schema `anuario` (Supabase), selector de **Año** en sidebar (2023, 2022, …). |
| 2 | **Resumen numérico** | Métricas: “Cuadros en catálogo”, “Filas balances (año X)”, “Empresas listadas (año X)”. Si en el futuro se cargan más tablas, añadir métricas por tabla temática. |
| 3 | **Catálogo de cuadros** | Tabla `anuario.cuadros`: columnas `cuadro_id`, `nombre`, `sector`. Filtro opcional por **sector** (seguro_directo, reaseguro, financiadoras_primas, medicina_prepagada). Dentro de un expander “Catálogo de cuadros (56 cuadros)”. |
| 4 | **Balances condensados** | Datos de `anuario.balances_condensados` para el año elegido. **Agrupación por sector**: usar `cuadro_id` → sector según catálogo (24=seguro_directo, 40=reaseguro, 47=financiadoras_primas, 54=medicina_prepagada). Opciones: **Tabs por sector** (Seguro directo, Reaseguro, Financiadoras de primas, Medicina prepagada) y dentro de cada tab una tabla concepto / monto (y tipo si aplica). Formato numérico en montos. |
| 5 | **Listados de empresas** | Datos de `anuario.listados_empresas` para el año elegido. **Tabs por sector** (cuadros 39, 46, 53) con etiquetas: “Reaseguro (cuadro 39)”, “Financiadoras de primas (cuadro 46)”, “Medicina prepagada (cuadro 53)”. Tabla: número de orden, nombre de empresa. |
| 6 | **Extensión futura** | Cuando se carguen más tablas temáticas (primas_por_ramo, indicadores_financieros_empresa, etc.), añadir secciones similares: filtro año, agrupación por cuadro_id o sector, tablas con columnas relevantes. Mantener el mismo patrón: resumen → catálogo/filtros → datos por tema. |

#### 3.5.2 Detalle visual propuesto (Anuario)

- **Sidebar**: Año; opcional: Sector (para filtrar catálogo y/o resaltar solo un sector en balances/listados).
- **Cuerpo**:
  - Bloque de métricas en columnas (3–4 métricas).
  - Expander “Catálogo de cuadros” con tabla completa y filtro por sector.
  - Subheader “Balances condensados” + texto corto explicando los cuatro cuadros (24, 40, 47, 54) + tabs por sector, cada tab con una tabla (concepto, monto, tipo).
  - Subheader “Listados de empresas autorizadas” + tabs por sector (39, 46, 53), cada tab con tabla (numero_orden, nombre_empresa).
- **Formato**: números con separador de miles; tablas en `st.dataframe(..., use_container_width=True, hide_index=True)`; sin símbolos Unicode que fallen en consola (ya aplicado en scripts).

#### 3.5.3 Lógica de sectores (catálogo como referencia)

- Cuadros ya tienen `sector` en `anuario.cuadros`. Para balances/listados se puede:
  - O bien **unir** con el catálogo (join por `cuadro_id`) y filtrar/agrupar por `sector`.
  - O bien **mapear en el front**: 24→Seguro directo, 40→Reaseguro, 47→Financiadoras de primas, 54→Medicina prepagada (y 39, 46, 53 para listados). Así no se depende de que el catálogo esté cargado para mostrar etiquetas.

Recomendación: usar el catálogo cuando esté disponible; si no, fallback al mapeo fijo por `cuadro_id` para las tablas ya cargadas.

---

## 4. Flujo de datos (data_loader y páginas)

- **Datos operativos**: `get_primas_df()`, `load_entities_from_supabase()`, `load_series_from_supabase()` (sin cambios de contrato).
- **Anuario**: 
  - `load_anuario_cuadros()` → catálogo.
  - `load_anuario_balances_condensados(anio)` → balances; en la página, agrupar por `cuadro_id` y mostrar por sector.
  - `load_anuario_listados_empresas(anio)` → listados; en la página, agrupar por `cuadro_id` y mostrar por sector.
- Caché: mantener `@st.cache_data(ttl=3600)` para todas las cargas.
- Sin datos de anuario: mensaje claro (“No hay datos del anuario…”) y pasos para ejecutar DDL y ETL (sin bloquear el resto del dashboard).

---

## 5. Resumen de decisiones para aprobar

| # | Decisión | Opción propuesta |
|---|----------|------------------|
| 1 | Navegación Anuario | Una sola página “Anuario Seguro en Cifras” con secciones (catálogo, balances, listados) y tabs por sector. |
| 2 | Sectores en balances/listados | Tabs etiquetados por sector (Seguro directo, Reaseguro, Financiadoras de primas, Medicina prepagada) usando `cuadro_id` y, si existe, nombre del sector desde el catálogo. |
| 3 | Catálogo de cuadros | En expander con tabla completa y filtro opcional por sector. |
| 4 | Año | Selector único en sidebar; aplica a balances y listados. |
| 5 | Inicio | Incluir resumen breve del anuario (métricas) y enlace a la página Anuario cuando haya datos. |
| 6 | Estilo | Métricas arriba; tablas con formato numérico; sin símbolos problemáticos en consola; mensajes claros cuando falten datos. |

---

## 6. Próximos pasos tras aprobación

1. Ajustar **Inicio** (`app.py`) con resumen anuario y enlaces.
2. Revisar **Resumen**, **Primas**, **Por Empresa** (mensajes y formato).
3. Rediseñar **4_Anuario_Seguro_En_Cifras.py** según secciones 3.5.1 y 3.5.2 (métricas, catálogo con filtro, balances por sector en tabs, listados por sector en tabs).
4. Probar en local (`streamlit run app.py`) con y sin datos de anuario y con y sin primas.
5. Documentar en el repo la estructura del dashboard (este documento o un README de la app).

Si apruebas este esquema, el siguiente paso es implementar los cambios en el código y ejecutar el dashboard en local para una revisión minuciosa antes de publicar.
