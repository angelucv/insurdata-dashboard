# Ruta de compilación por año y estructura integral del aplicativo

Este documento describe: (1) la recomendación de por dónde empezar (Excel vs PDF), (2) una ruta escalable para compilar la información año a la vez y validar consistencia, y (3) cómo todo se relaciona con Supabase y el resto del aplicativo.

---

## 1. Recomendación: empezar por Excel (un archivo tipo, un año)

### Por qué Excel primero y no el PDF del anuario

| Criterio | Excel (ej. resumen-por-empresa-YYYY.xlsx) | PDF anuario (Seguro en Cifras) |
|----------|--------------------------------------------|--------------------------------|
| **Estructura** | Filas/columnas definidas; hojas por mes (Enero, Febrero…). Aunque haya celdas combinadas o cabeceras en varias filas, el patrón se puede normalizar con código. | Varias “tablas” por página, diseños distintos según año; Camelot devuelve fragmentos y a veces falla en PDFs basados en imagen. |
| **Consistencia** | Un mismo archivo = un año; puedes validar totales por mes y por archivo antes de mezclar con otros. | Un PDF = un año pero la extracción es inestable; hace falta más lógica ad hoc para unificar tablas. |
| **Trazabilidad** | Fácil: “estos registros vienen de resumen-por-empresa-2023.xlsx, hoja Diciembre”. | Más difícil: un CSV `_tables.csv` puede mezclar muchas tablas del PDF. |
| **Escalabilidad** | Mismo loader (resumen_por_empresa, primas_netas_por_empresa, etc.) para todos los años; solo cambia el año en el nombre del archivo. | Cada anuario puede cambiar estructura; más trabajo por año. |

**Recomendación:** empezar por **un tipo de Excel en concreto** (por ejemplo **Resumen por empresa**) y **un solo año** (ej. 2023). Llevar ese archivo a una **capa de datos limpios** con esquema fijo (entidad, periodo, primas_netas_ves, siniestros_pagados_ves, gastos_operativos_ves, etc.), validar ahí, y solo después integrar más fuentes (otros Excel, luego PDF si hace falta).

El PDF del anuario conviene usarlo como **complemento o contraste** una vez que tengas ya compilado y validado el año con Excel (p. ej. comparar totales anuales).

---

## 2. Capas de datos y ruta escalable año a año

### 2.1 Capas (de crudo a consumo)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. RAW (fuentes crudas)                                                     │
│     data/raw/xlsx/, data/raw/pdf/                                             │
│     Archivos tal cual se descargan: Excel por año, PDFs Boletín/Anuario.     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. STAGED (por fuente, normalizado)                                         │
│     data/staged/YYYY/  o  data/audit/by_source/                               │
│     Un archivo (o conjunto) por archivo fuente, mismo esquema de columnas:   │
│     source_file, sheet, entity_name, periodo, primas_netas_ves, ...          │
│     Objetivo: poder revisar “qué salió de este Excel” sin tocar la BD.        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. CLEAN (compilado por año, listo para analizar/cargar)                    │
│     data/clean/YYYY/                                                         │
│     Un dataset por año (o por tipo: primas_2023.parquet, etc.) con esquema   │
│     unificado, entidades normalizadas, periodos YYYY-MM-01. Validado.        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. SUPABASE (persistencia para el aplicativo)                               │
│     entities, primas_mensuales, exchange_rates, margen_solvencia,             │
│     series_historicas                                                        │
│     Se alimenta desde la capa CLEAN (o desde ETL que lee RAW y escribe       │
│     también en CLEAN/STAGED).                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. DASHBOARD (Streamlit)                                                    │
│     Lee de Supabase (o fallback a data/processed / data/clean)               │
│     Muestra KPIs, gráficos, tablas por periodo y por empresa.                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Ruta paso a paso (escalar por año)

Ciclo **por año** (ej. 2023) y **por tipo de fuente**:

1. **Elegir un solo archivo Excel** para ese año  
   Ejemplo: `resumen-por-empresa-2023.xlsx`.

2. **Extraer a STAGED**  
   - Leer todas las hojas (Enero … Diciembre).  
   - Resolver cabeceras (filas 8–9 típicas, posibles multiíndice).  
   - Mapear columnas a un esquema fijo: `entity_name`, `periodo` (YYYY-MM-01), `primas_netas_ves`, `siniestros_pagados_ves`, `gastos_operativos_ves`, `source_file`, `sheet`.  
   - Guardar en algo como:  
     `data/staged/2023/resumen_por_empresa_2023.csv` (o por hoja si prefieres revisar mes a mes).

3. **Validar en STAGED**  
   - Conteo de filas por mes.  
   - Totales por mes (suma de primas, siniestros, gastos).  
   - Detección de filas duplicadas (misma entidad + periodo).  
   - Revisión manual de una muestra (empresas conocidas, un mes).  
   - **Semántica de los campos:** en cada pestaña del Resumen por empresa la información es **acumulada (YTD)** para primas (1), siniestros pagados (2), comisiones (6), gastos de adquisición (7) y gastos de administración (8): en principio no disminuyen mes a mes; las bajas pueden deberse a empresas que no envían en un mes o a **ajustes a la baja**. Solo las **reservas** (3), (4) y siniestros totales (5) = (2)+(3) se **constituyen y liberan mes a mes**, por tanto pueden subir o bajar y no se validan como series crecientes.

4. **Pasar a CLEAN**  
   - Normalizar nombres de entidad (misma función que usas para Supabase).  
   - Unificar `periodo` a fecha (primer día del mes).  
   - Generar `data/clean/2023/primas_2023.parquet` (o solo `resumen_por_empresa_2023.parquet` si aún no mezclas fuentes).  
   - Opcional: checks de integridad (rangos, nulos, duplicados).

5. **Cargar a Supabase**  
   - Resolver `entity_name` → `entities.id` (get_or_create).  
   - Insertar/upsert en `primas_mensuales` desde el dataset de CLEAN para ese año.  
   - No hace falta cargar todos los años a la vez: puedes cargar solo 2023, validar en el dashboard, y luego seguir con 2024, 2022, etc.

6. **Repetir para otro tipo de Excel** (mismo año)  
   - Ej.: `primas-netas-cobradas-por-empresa-2023.xlsx` → staged → validar → incorporar a clean 2023 (o tabla separada) → cargar a Supabase.  
   - Aquí puedes decidir reglas de prioridad si una misma (entidad, periodo) viene de dos fuentes (ej. quedarse con resumen_por_empresa porque trae más columnas).

7. **Al terminar el año**  
   - Script de verificación que compare:  
     - Conteo y totales en CLEAN 2023 vs STAGED 2023.  
     - Conteo/totales en Supabase para periodo 2023-01-01 a 2023-12-01.

8. **Siguiente año**  
   - Misma secuencia para 2024, 2022, etc., reutilizando los mismos loaders y la misma estructura de carpetas.

**PDF anuario:** cuando quieras integrarlo, puede ser un segundo flujo:  
- Extraer anuario (ej. Seguro en Cifras 2023) a STAGED (ej. `data/staged/2023/seguro_en_cifras_2023_*.csv`).  
- Validar totales anuales frente a lo que ya tienes en CLEAN/Supabase para ese año.  
- Si cuadra, incorporar a CLEAN o a una tabla específica (p. ej. series_historicas o una tabla “anuario”) y luego exponerla en el dashboard.

---

## 3. Estructura de carpetas propuesta

```
data/
├── raw/                      # Fuentes crudas (sin modificar)
│   ├── xlsx/                 # Excel por año y tipo
│   └── pdf/                  # Boletines y anuarios
│
├── staged/                   # Una salida por archivo fuente (normalizada)
│   └── 2023/
│       ├── resumen_por_empresa_2023.csv
│       ├── primas_netas_por_empresa_2023.csv
│       ├── cuadro_resultados_2023.csv
│       └── ...
│
├── clean/                    # Compilado por año, esquema unificado
│   └── 2023/
│       ├── primas_2023.parquet      # Todas las primas/métricas del año
│       ├── entities_2023.parquet    # Catálogo de entidades usado ese año
│       └── manifest_2023.json       # Metadato: fuentes, fechas, checksums
│
├── processed/                # Salida actual del ETL (compatible con el app)
│   └── primas_mensuales.parquet     # Fallback cuando no hay Supabase
│
└── audit/                    # Auditoría y trazabilidad (ya existente)
    ├── by_source/            # CSVs por archivo procesado
    ├── mirror/               # Espejo de tablas (entities, primas_mensuales)
    └── manifest/
```

- **raw:** lo que ya tienes.  
- **staged:** salida de “un Excel → un CSV/Parquet normalizado” por año.  
- **clean:** lo que consideras “dato listo” por año para cargar a Supabase y para el dashboard.  
- **processed** y **audit** pueden seguir siendo usados por el ETL actual y por los scripts de verificación.

---

## 4. Cómo se relaciona con Supabase y el resto del aplicativo

### 4.1 Flujo de datos hacia Supabase

```
Excel/PDF (raw)
    → ETL (src/etl/sudeaseg_to_supabase.py, audit_local.py)
    → [opcional] staged/ + clean/
    → Supabase: entities, primas_mensuales, exchange_rates, margen_solvencia, series_historicas
```

- **entities:** una fila por aseguradora; `normalized_name` (clave estable), `canonical_name` (nombre legible).  
- **primas_mensuales:** una fila por (entidad, mes): primas, siniestros, gastos (VES y opcionalmente USD).  
- **exchange_rates:** tasas BCV para convertir VES → USD.  
- **margen_solvencia:** trimestral por entidad.  
- **series_historicas:** agregados por periodo (totales sector, etc.) para KPIs.

El ETL actual ya hace “raw → Supabase” (y opcionalmente espejo en audit). La ruta nueva añade **staged** y **clean** en el medio para que puedas revisar año a año antes de tocar Supabase.

### 4.2 Cómo el dashboard usa estos datos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  app.py  y  pages/*.py                                                       │
│  Usan: get_primas_df(), load_entities_from_supabase(), load_series_...()     │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │  src/app/components/data_loader.py
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1) Intenta Supabase (primas_mensuales, entities, series_historicas)        │
│  2) Si no hay URL/KEY o falla → fallback a data/processed/*.parquet          │
└─────────────────────────────────────────────────────────────────────────────┘
```

- Todo lo que cargues en **primas_mensuales** y **entities** en Supabase se refleja en el dashboard (Resumen, Primas/Siniestros, Por empresa).  
- Si quieres que el dashboard pueda usar solo un año (ej. 2023) para depurar, puedes:  
  - cargar en Supabase solo ese año, o  
  - añadir en `data_loader` un filtro por año cuando lee de `data/processed` o `data/clean` (p. ej. leer `data/clean/2023/primas_2023.parquet`).

### 4.3 Esquema de Supabase (resumen)

| Tabla | Uso |
|-------|-----|
| **entities** | Catálogo de aseguradoras; `primas_mensuales.entity_id` apunta aquí. |
| **primas_mensuales** | Métricas por entidad y mes (primas, siniestros, gastos VES/USD). |
| **exchange_rates** | Tasas BCV para convertir montos a USD. |
| **margen_solvencia** | Margen de solvencia por entidad y trimestre. |
| **series_historicas** | Agregados por periodo (para KPIs del resumen). |

La compilación por año que hagas en **clean** debe producir exactamente el tipo de filas que el ETL inserta en **primas_mensuales** y **entities** (mismas columnas y convenciones de periodo y entidad).

---

## 5. Vista integral del aplicativo

```
sudeaseg-dashboard/
│
├── config/                   # Configuración central
│   ├── settings.py           # Rutas (DATA_RAW, DATA_PROCESSED, SUPABASE_*), ETL_TARGET_YEAR, etc.
│   ├── audit_paths.py         # Rutas de data/audit (mirror, by_source, manifest)
│   └── sudeaseg_columns.py   # Mapeo de columnas Excel → esquema
│
├── data/                     # Datos (raw → staged → clean → processed / audit)
│   ├── raw/                  # Fuentes crudas (xlsx/, pdf/)
│   ├── staged/               # [NUEVO] Por año, por archivo fuente, normalizado
│   ├── clean/                 # [NUEVO] Por año, compilado y validado
│   ├── processed/            # Parquet para el dashboard (fallback)
│   └── audit/                # by_source, mirror, manifest (trazabilidad)
│
├── src/
│   ├── extraction/           # Lectura de fuentes crudas
│   │   ├── excel_loader.py   # Carga Excel SUDEASEG
│   │   ├── pdf_extractor.py  # Camelot / pdfplumber / OCR
│   │   ├── pdf_ocr.py        # OCR para PDFs escaneados
│   │   ├── scraper.py        # Descarga desde portal SUDEASEG
│   │   └── bcv_client.py     # Tasas de cambio
│   │
│   ├── etl/                  # Transformación y carga
│   │   ├── sudeaseg_to_supabase.py  # Excel/PDF → Supabase (entities + primas_mensuales)
│   │   ├── transformers.py   # Flatten headers, impute, normalize entity
│   │   ├── entity_resolver.py
│   │   ├── audit_local.py    # Raw → audit/mirror y by_source (sin Supabase)
│   │   └── pipeline.py
│   │
│   ├── db/                   # Base de datos
│   │   ├── client.py         # get_supabase_client(), load_df_into_table
│   │   ├── schema.sql        # DDL entities, primas_mensuales, exchange_rates, etc.
│   │   └── truncate_all.sql
│   │
│   ├── app/                  # Dashboard Streamlit
│   │   └── components/
│   │       ├── data_loader.py # get_primas_df(), load_entities_from_supabase(), fallback local
│   │       └── auth.py       # Login Supabase Auth (opcional)
│   │
│   └── verification/         # Verificación de datos convertidos
│       └── pdf_2023.py       # Verificación PDF 2023
│
├── scripts/                  # Puntos de entrada
│   ├── run_extraction.py     # Descarga raw
│   ├── run_etl_to_supabase.py # ETL raw → Supabase (con --year, --debug, --dry-run)
│   ├── run_etl_2023.py       # ETL solo 2023, debug
│   ├── audit_local_pipeline.py # Raw → audit (mirror + by_source)
│   ├── verificar_carga.py    # Excel vs Supabase
│   ├── verificar_consistencia_datos_convertidos.py
│   └── verificar_pdf_2023.py
│
├── app.py                    # Entrada del dashboard (streamlit run app.py)
├── pages/                    # Páginas del dashboard
│   ├── 1_Resumen.py
│   ├── 2_Primas_Siniestros.py
│   └── 3_Por_Empresa.py
│
└── docs/
    └── RUTA_COMPILACION_Y_ESTRUCTURA.md   # Este documento
```

---

## 6. Orden sugerido de implementación (práctico)

1. **Crear `data/staged/` y `data/clean/`** (y subcarpetas por año si quieres).
2. **Implementar un loader “Excel → staged”** para un solo tipo (ej. Resumen por empresa):  
   - Entrada: `data/raw/xlsx/resumen-por-empresa-2023.xlsx`.  
   - Salida: `data/staged/2023/resumen_por_empresa_2023.csv` con columnas fijas.
3. **Script de validación** sobre ese CSV (filas, totales, duplicados).
4. **Paso staged → clean** para 2023 (un Parquet o CSV por año).
5. **Carga clean 2023 → Supabase** (reutilizando entity resolution y upsert del ETL actual).
6. **Comprobar en el dashboard** que 2023 se ve bien.
7. Repetir para otro tipo de Excel (ej. primas-netas) y/o para 2024, 2022, etc.
8. Opcional: integrar PDF anuario a staged/clean y a una tabla específica o a series_historicas.

Con esto tienes una ruta escalable por año y por fuente, datos limpios revisables antes de tocar Supabase, y una visión clara de cómo encaja todo el aplicativo (raw → staged → clean → Supabase → dashboard).
