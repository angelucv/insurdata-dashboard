# Seguro en Cifras – Estructura en disco y esquema coherente

## Objetivo

Estructura **solo en disco** para el vaciado de los anuarios "Seguro en Cifras" / "Seguros en Cifras", con definición de entidades, variables y esquema listo para una futura base de datos.

## Rango de anuarios

| Origen | Años | Formato | Observación |
|--------|------|---------|-------------|
| data/raw/pdf | 1967-1969 | PDF | Seguros-en-Cifras-YYYY |
| data/raw/pdf | 1970-1998 | PDF | Seguro-en-Cifras-YYYY (1986: 1.Seguro-en-Cifras-1986) |
| data/raw/pdf | 1993-1994 | PDF | Un solo archivo Seguro-en-Cifras-1993-1994 |
| data/raw/pdf | 1999-2023 | PDF | seguros-en-cifra-YYYY |
| data/raw/pdf | 2018, 2020 | PDF | seguro-en-cifras-YYYY |
| data/raw/pdf | 2024 | PDF | Seguro en Cifras 2024 |
| data/raw/xlsx | 2024 | Excel | cuadros descargables_Seguro en cifras 2024.xlsx |

**Total:** 57 años con al menos una fuente (1967–2024).

## Estructura en disco

```
data/audit/seguro_en_cifras/
├── README.md
├── indice/
│   ├── anuario_fuentes.csv    # Una fila por archivo fuente (anio, nombre_archivo, tipo, ruta)
│   └── revision_estructura.csv # Por año: tiene_extraccion_tablas, tiene_texto, total_filas_tablas
├── variables/
│   └── canonico.csv          # metric_name, descripcion, unit_default, cuadros_tipicos
├── entidades/                 # (opcional) catálogo consolidado de entidades
├── vaciado/
│   ├── anuario_entidades.csv  # anio, source_file, entity_name, entity_normalized_name
│   └── anuario_metricas.csv  # anio, source_file, cuadro_or_seccion, entity_name, metric_name, value, unit, ramo_opcional
└── raw/                       # (opcional) copias o enlaces a extracciones por archivo
```

## Esquema coherente para base de datos

### Tabla `anuario_fuentes` (índice)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| anio | int | Año del anuario |
| anio_fin | text | Segundo año si es rango (ej. 1994 en 1993-1994) |
| nombre_archivo | text | Nombre del archivo |
| tipo | text | pdf \| xlsx |
| ruta_relativa | text | Ruta respecto a data/raw |
| tiene_entidades | bool | Si se extrajeron entidades |
| tiene_primas | bool | Si hay datos de primas |
| tiene_siniestros | bool | Si hay datos de siniestros |
| observaciones | text | Notas |

### Tabla `anuario_entidades`

Una fila por (anio, entidad) por fuente.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| anio | int | Año |
| source_file | text | Archivo del que se extrajo |
| entity_name | text | Nombre tal cual en la fuente |
| entity_normalized_name | text | Clave estable (minúsculas, sin tildes, normalizado) para cruce entre años |

### Tabla `anuario_metricas`

Una fila por (anio, fuente, cuadro, entidad, métrica).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| anio | int | Año |
| source_file | text | Archivo de origen |
| cuadro_or_seccion | text | Ej. "Cuadro 4", "Cuadro 5A" |
| entity_name | text | Nombre de la entidad en la fuente |
| metric_name | text | Variable canónica (ver variables/canonico.csv) |
| value | float | Valor numérico |
| unit | text | miles_Bs, %, etc. |
| ramo_opcional | text | Rama si aplica (ej. Automóvil Casco, Vida) |

### Variables canónicas (metric_name)

Definidas en `variables/canonico.csv`:

- **primas_netas_cobradas** – Primas netas cobradas (total o por ramo)
- **primas_netas_por_ramo** – Desglose por ramo/empresa
- **siniestros_pagados** – Prestaciones y siniestros pagados
- **reservas_tecnicas** – Reservas técnicas por retención propia
- **reservas_primas** – Reservas de primas
- **reservas_siniestros_pendientes** – Reservas para siniestros pendientes
- **gastos_administracion** – Gastos de administración vs primas
- **gastos_produccion** – Gastos de producción vs primas
- **capital_garantia** – Capital y garantía por empresa
- **resultados_economicos** – Resultados económicos / ganancias netas
- **inversiones_reservas** – Inversiones aptas para reservas técnicas
- **comisiones_gastos_adquisicion** – Comisiones y gastos de adquisición
- **empresas_autorizadas** – Número de empresas autorizadas

## Entidades

Las **entidades** son las empresas de seguros (y, si aplica, reaseguros u otros sujetos) que aparecen en los cuadros. Se identifican por:

- **entity_name:** texto tal como aparece en la publicación.
- **entity_normalized_name:** versión normalizada (minúsculas, sin tildes, puntuación reducida) para unificar variaciones entre años (fusiones, cambios de razón social, errores tipográficos).

El vaciado actual (Excel 2024) produce **134 entidades** únicas por año en `anuario_entidades.csv`. En futuras cargas se puede mantener un catálogo maestro en `entidades/` con `entity_normalized_name` y un nombre canónico o UUID para la base de datos.

## Disponibilidad por año

- **Extracción en by_source:** Los PDFs procesados por el pipeline de auditoría generan en `data/audit/by_source` archivos `*_tables.csv` (tablas extraídas) y en `pdf_text/` el texto (nativo u OCR). La revisión (`scripts/anuarios_revision_estructura.py`) genera `indice/revision_estructura.csv` con, por año, si hay tablas y/o texto y cantidad de filas.
- **Vaciado estructurado:** Por ahora solo el Excel 2024 se vacía a `vaciado/anuario_entidades.csv` y `vaciado/anuario_metricas.csv`. Los anuarios en PDF (1967–2023) quedan como fuentes indexadas y extracciones crudas en by_source; el vaciado a este esquema se puede extender con parsers específicos por periodo o con OCR + reglas por cuadro.

## Índice de cuadros y alineación con anuarios

Los anuarios están estructurados por **cuadros** (tablas). La extracción se alinea con:

- **variables/indice_cuadros.csv**: `cuadro_id`, `nombre_cuadro`, `metricas_esperadas`, `descripcion_corta`. Para cada cuadro (Cuadro 4, 5A, 5B, 7, 8A–8C, 12–19, 23A–23F, 30, 31B, 34, 35, Resumen) se definen las métricas canónicas que se esperan. El ETL normaliza el título del cuadro en PDF (ej. "Cuadro No. 5-A  EMPRESAS...") a `Cuadro 5A` para homogeneizar.
- **variables/canonico.csv**: 20+ `metric_name` con `cuadros_tipicos` donde suelen aparecer. La matriz de vaciado incluye columnas para todos los canónicos (las faltantes quedan en NaN) para verificar consistencia.

Objetivo en la **ventana 2014–2024**: al menos **20 campos** con serie histórica consistente por compañía (base madre).

## Verificación de consistencia (ventana 2014–2024)

1. **Tabla por compañía y año**: `indice/verificacion_tabla_compania_anio_campos.csv` — una fila por (`nombre_normalizado_madre`, `anio`) con indicador 0/1 por cada campo objetivo y `n_campos_llenos`, `ok_20_campos`, `campos_faltantes`.
2. **Resumen**: `indice/verificacion_resumen_consistencia_ventana.csv` — por compañía, número de años y de filas con ≥20 campos.
3. **Inconsistencias**: `indice/verificacion_inconsistencias_ventana.csv` — duplicados (mismo entity, año, métrica con valores distintos).

Si la data no es consistente (pocos campos llenos o duplicados), se repite: **normalización → vaciado → base madre → verificación** hasta lograr al menos 20 campos con serie histórica consistente por compañía.

## Scripts

| Script | Función |
|-------|--------|
| `scripts/anuarios_indice_y_vaciado.py` | Construye `indice/anuario_fuentes.csv` y vacía el Excel 2024 a vaciado/ |
| `scripts/anuarios_revision_estructura.py` | Revisa by_source y escribe `indice/revision_estructura.csv` (rangos, estructura, variables disponibles) |
| `scripts/anuarios_vaciado_secuencial.py` | Vaciado año a año; deduplica métricas (anio, entity_name, metric_name) con `keep="first"` |
| `scripts/anuarios_construir_entidades_y_matriz.py` | Catálogo, variantes y matriz (incluye columnas canónicas faltantes como NaN) |
| `scripts/anuarios_base_madre_2014_2024.py` | Base madre ventana 2014–2024 y matriz filtrada con `nombre_normalizado_madre` |
| `scripts/anuarios_verificar_consistencia_ventana.py` | Verificación por compañía/año de los 20 campos; reportes de consistencia e inconsistencias |

## Próximos pasos (cuando se suba a nube)

1. Crear tablas en la base de datos según este esquema.
2. Cargar `anuario_fuentes.csv`, `anuario_entidades.csv` y `anuario_metricas.csv` desde disco.
3. Extender el vaciado a más años (PDF/OCR o Excels adicionales) y volver a cargar o hacer upsert por (anio, source_file, entity, metric).
