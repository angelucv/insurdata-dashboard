# ¿100 tablas crudas o reorganizar? Tres opciones de esquema para el anuario

Los 100 CSV se pueden volcar tal cual (100 tablas) o reorganizarse para que la base sea más fácil de consultar y mantener. Abajo van **tres opciones** y una **sugerencia**.

---

## Opción 1: Mantener 100 tablas (1 tabla = 1 CSV)

**Qué es:** Lo que tienes ahora. Cada archivo CSV → una tabla con el mismo nombre (`cuadro_03_primas_por_ramo`, etc.) y columna `anio`.

| Ventajas | Desventajas |
|----------|-------------|
| ETL trivial: leer CSV e insertar. | 100 tablas que mantener (DDL, migraciones). |
| Fidelidad total al PDF: cada cuadro se consulta igual que en el anuario. | Estructuras repetidas (varios “balance condensado”, varios “por empresa”). |
| Auditoría simple: comparar filas con el documento. | Cruces entre cuadros requieren JOINs entre muchas tablas. |
| Añadir otro año = mismo proceso, mismo esquema. | Poco “tema”: no hay una sola tabla “todos los balances” o “todos los indicadores”. |

**Cuándo tiene sentido:** Si el uso principal es “consultar un cuadro concreto” o “reproducir el anuario en pantalla” y quieres cero lógica de reorganización.

---

## Opción 2: Reorganizar por tipo de contenido (tablas temáticas)

**Qué es:** Agrupar los 100 cuadros en **menos tablas** según el **tipo de dato** (primas, siniestros, reservas, balances, indicadores, listados, etc.). Cada tabla tiene una columna `cuadro_id` (o `origen`) para saber de qué cuadro viene cada fila.

Ejemplo de agrupación posible:

| Tabla temática | Cuadros que agrupa (ej.) | Estructura típica |
|----------------|---------------------------|-------------------|
| `primas_por_ramo` | 3, 4, 5A/B/C (por página si hace falta) | anio, cuadro_id, ramo, seguro_directo, reaseguro, total, pct |
| `siniestros_por_ramo` | 6, 7, 8A/B/C | anio, cuadro_id, ramo/empresa, columnas numéricas |
| `reservas_tecnicas` | 9 | anio, concepto, monto, tipo |
| `reservas_prima_por_ramo_empresa` | 10, 11, 12–14, 15–19, 20A–F | anio, cuadro_id, ramo/empresa, columnas según subtipo |
| `balances_condensados` | 24, 40, 47, 54 | anio, cuadro_id, concepto, monto, tipo |
| `estados_ingresos_egresos` | 25A/B, 26, 41A/B, 48, 55A/B | anio, cuadro_id, concepto, monto, tipo |
| `indicadores_por_empresa` | 29, 44, 52, 58 | anio, cuadro_id, nombre_empresa, col1…colN |
| `listados_empresas` | 39, 46, 53 | anio, cuadro_id, numero_registro, nombre_empresa, … |
| `otros_cuadros` | 21, 22, 23, 30, 31A/B, 32–38, 42, 43A/B, 45, 49–51, 56, 57 | anio, cuadro_id, columnas específicas o JSONB |

Resultado: del orden de **10–20 tablas** en lugar de 100. Cuadros con estructura muy distinta pueden seguir en tablas propias (ej. `cantidad_polizas_siniestros` para 37–38).

| Ventajas | Desventajas |
|----------|-------------|
| Menos tablas, esquema más legible. | Hay que definir y mantener el mapeo CSV → tabla temática. |
| Consultas por tema: “todos los balances”, “todos los indicadores por empresa”. | Algunos cuadros no encajan en un tipo común (hay que decidir si tabla específica o “otros”). |
| Más fácil añadir años: mismos esquemas, solo cambia `anio`. | ETL más complejo que “un CSV → una tabla”. |
| Cruces más simples dentro de cada tema. | Perder el 1:1 exacto cuadro ↔ tabla (se recupera con `cuadro_id`). |

**Cuándo tiene sentido:** Cuando quieres usar la BD para análisis, reportes y dashboards por tema (primas, siniestros, reservas, balances, indicadores) y aceptas un ETL que clasifique cada CSV en una de estas tablas.

---

## Opción 3: Modelo genérico (pocas tablas + catálogos)

**Qué es:** Una o muy pocas tablas “de filas” y catálogos. Por ejemplo:

- **`anuario.cuadros`** (catálogo): id, codigo, nombre, descripcion.
- **`anuario.filas_cuadro`**: anio, cuadro_id, fila_orden, datos (JSONB o clave-valor).
- Opcional: **`anuario.empresas`** si normalizas nombres de empresa en muchos cuadros.

Cada fila de cada CSV se guarda como una fila en `filas_cuadro`, con `cuadro_id` y los valores en `datos` (por ejemplo un JSON con las columnas del CSV).

| Ventajas | Desventajas |
|----------|-------------|
| Muy pocas tablas; esquema estable aunque cambien los cuadros. | Consultas por concepto (ej. “dame el total de primas”) requieren filtrar/agregar sobre JSON. |
| Añadir un cuadro nuevo = insertar en catálogo + cargar filas. | Menos aprovechamiento de tipos y columnas nativas de SQL. |
| Máxima flexibilidad ante cambios en el PDF. | Más difícil hacer JOINs “clásicos” y reportes por columnas fijas. |

**Cuándo tiene sentido:** Si priorizas flexibilidad y almacenamiento unificado sobre consultas SQL simples por columnas.

---

## Sugerencia

- **Si el objetivo es solo reflejar el anuario y consultar cuadro por cuadro** → **Opción 1 (100 tablas)** es razonable: simple, auditable, sin rediseño.
- **Si quieres usar la BD para análisis, comparar años y construir reportes por tema** → **Opción 2 (tablas temáticas)** suele ser más eficiente: menos tablas, consultas más claras, mismo dato con mejor organización.
- **Opción 3** tiene sentido sobre todo si esperas muchos cambios en la estructura del anuario o quieres un único “contenedor” de filas.

Recomendación práctica: **avanzar con Opción 2 de forma gradual**:

1. Mantener los **100 CSV en `verificadas/`** como fuente de verdad (igual que ahora).
2. Definir **5–10 tablas temáticas** que cubran la mayoría de los cuadros (primas, siniestros, reservas, balances, estados de resultados, indicadores, listados).
3. Escribir un ETL que lea cada CSV y lo inserte en la tabla temática que corresponda (con `cuadro_id` para trazabilidad).
4. Los cuadros que no encajen bien pueden quedarse temporalmente en una tabla “cruda” por cuadro (híbrido entre Opción 1 y 2) hasta que decidas si merecen tabla temática propia.

Así reduces la complejidad del esquema (menos tablas, más eficiente para consultas por tema) sin perder trazabilidad al cuadro ni la fuente CSV.
