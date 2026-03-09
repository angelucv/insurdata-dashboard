# Propuesta: ETL con capas intermedias, auditorías y réplica local antes de la nube

Ante la complejidad de los PDF (extensos) y de los Excel (estructuras complejas), esta propuesta define **capas intermedias**, **puntos de auditoría** y una **réplica local de la base de datos** para validar que todo esté limpio antes de cargar a Supabase.

---

## 1. Principios

- **No cargar a la nube hasta que la réplica local esté auditada y aprobada.**
- **Cada capa tiene un formato y propósito claro** para poder auditar en disco.
- **Trazabilidad:** en cada paso se sabe qué archivo fuente generó qué datos.
- **Réplica local = mismo esquema que Supabase** (entities, primas_mensuales, exchange_rates, margen_solvencia, series_historicas), en CSV o Parquet, para revisión y comparación.

---

## 2. Estructura de carpetas propuesta

```
data/
│
├── raw/                          # Fuente de verdad (no modificar en ETL)
│   ├── pdf/
│   └── xlsx/
│
├── audit/                        # Trazabilidad y salidas crudas de extracción
│   ├── by_source/                # Una salida por archivo procesado
│   │   ├── {nombre_archivo}_extract.csv   # Excel: tablas extraídas
│   │   ├── {nombre_archivo}_tables.csv    # PDF: tablas Camelot/pdfplumber
│   │   └── pdf_text/                       # Texto completo de PDFs (OCR/nativo)
│   └── manifest/                 # Índice: archivo fuente → qué se generó
│       └── index.json
│
├── staged/                       # Normalizado por archivo y año (esquema unificado)
│   └── {YYYY}/
│       ├── resumen_por_empresa_YYYY.csv
│       ├── primas_netas_por_empresa_YYYY.csv
│       ├── cuadro_resultados_YYYY.csv
│       ├── seguro_en_cifras_YYYY.csv
│       ├── margen_solvencia_YYYY.csv
│       └── reporte_staged_YYYY.txt         # Conteos y totales para auditoría
│
├── clean/                        # Compilado por año, validado (listo para réplica)
│   └── {YYYY}/
│       ├── primas_YYYY.parquet             # Datos para primas_mensuales + entities
│       ├── margen_solvencia_YYYY.parquet
│       ├── exchange_rates_YYYY.parquet     # Si aplica
│       ├── validacion_YYYY.json             # Resultado de reglas de validación
│       └── manifest_YYYY.json               # Fuentes usadas, checksums
│
├── replica_db/                   # RÉPLICA LOCAL DE LA BASE (mismo esquema que Supabase)
│   ├── entities.parquet
│   ├── primas_mensuales.parquet
│   ├── exchange_rates.parquet
│   ├── margen_solvencia.parquet
│   ├── series_historicas.parquet
│   ├── manifest_replica.json     # Fecha de generación, fuentes, conteos
│   └── auditoria_replica.txt     # Resumen de validaciones pre-carga
│
└── processed/                    # Opcional: copia para fallback del dashboard
    └── primas_mensuales.parquet
```

**Réplica local (`replica_db/`):** es la “copia” de las tablas que luego se subirán a Supabase. Se construye desde `clean/` y se audita aquí; solo cuando esté validada se ejecuta la carga a la nube.

---

## 3. Flujo del proceso (paso a paso)

```
  raw/  ──►  audit/by_source/     ──►  staged/{YYYY}/   ──►  clean/{YYYY}/   ──►  replica_db/   ──►  Supabase
              │                            │                      │                    │
         [Auditoría 1]               [Auditoría 2]           [Auditoría 3]        [Auditoría 4]
         ¿Se extrajo algo            ¿Conteos y totales       ¿Clean consistente?   ¿Réplica lista
         de cada archivo?            por archivo correctos?   ¿Sin duplicados?      para subir?
```

### Fase 1 — Extracción a by_source (auditoría 1)

| Entrada | Salida | Objetivo auditoría |
|---------|--------|---------------------|
| `raw/pdf/*`, `raw/xlsx/*` | `audit/by_source/{archivo}_extract.csv` o `_tables.csv`; `audit/by_source/pdf_text/*.txt` | Ver que cada archivo generó al menos una salida; revisar muestras de Excel/PDF complejos |

- **Excel:** por archivo, una o varias hojas → un CSV normalizado por hoja o uno por archivo (según complejidad).
- **PDF:** por archivo, tablas extraídas (Camelot/pdfplumber) → CSV; texto completo → `pdf_text/` para revisión manual si hace falta.
- **Manifest:** registrar en `audit/manifest/index.json` qué archivo generó qué fichero en by_source.

**Criterio de paso:** listado de archivos raw vs listado de salidas en by_source; revisión de una muestra (p. ej. un Resumen por empresa, un anuario PDF).

---

### Fase 2 — Normalización a staged (auditoría 2)

| Entrada | Salida | Objetivo auditoría |
|---------|--------|---------------------|
| `audit/by_source/*.csv` (por tipo y año) | `staged/{YYYY}/{tipo}_{YYYY}.csv` | Mismo esquema de columnas en todos los staged; conteos por mes/entidad; totales por archivo |

- Por **tipo** (resumen_por_empresa, primas_netas, cuadro_resultados, etc.) y **año**, generar un CSV en staged con columnas unificadas (entity_name, periodo, primas_netas_ves, …).
- Generar `reporte_staged_YYYY.txt`: número de filas por archivo fuente, totales por mes, número de entidades.

**Criterio de paso:** totales por mes coherentes entre fuentes del mismo año; sin filas duplicadas (entity + periodo) dentro de cada tipo; revisión de empresas conocidas.

---

### Fase 3 — Compilación a clean (auditoría 3)

| Entrada | Salida | Objetivo auditoría |
|---------|--------|---------------------|
| `staged/{YYYY}/*.csv` | `clean/{YYYY}/*.parquet` + `validacion_YYYY.json` | Un dataset por año; reglas de validación (rangos, nulos, duplicados) documentadas |

- Unir los staged del año en un esquema único; resolver entidades (normalizar nombres); deduplicar (entity, period).
- Aplicar reglas de validación (ej. primas >= 0, periodo en rango, entidad no vacía) y guardar resultado en `validacion_YYYY.json`.
- Opcional: exportar por tabla lógica (primas+entities, margen_solvencia, exchange_rates) en Parquet.

**Criterio de paso:** validacion_YYYY.json sin errores críticos; manifest_YYYY.json con fuentes y checksums; revisión de totales anuales vs staged.

---

### Fase 4 — Construcción de la réplica local (auditoría 4)

| Entrada | Salida | Objetivo auditoría |
|---------|--------|---------------------|
| `clean/{YYYY}/*.parquet` (uno o varios años) | `replica_db/*.parquet` + `manifest_replica.json` + `auditoria_replica.txt` | Réplica con el mismo esquema que Supabase; listada para revisión humana |

- Construir/actualizar las “tablas” en `replica_db/`: entities, primas_mensuales, exchange_rates, margen_solvencia, series_historicas (mismo esquema que en `src/db/schema.sql`).
- Generar `manifest_replica.json`: fecha, años incluidos, conteo por tabla, fuentes (archivos clean usados).
- Generar `auditoria_replica.txt`: resumen de filas por tabla, totales clave, advertencias (duplicados, nulos, rangos).

**Criterio de paso:** revisión de conteos y totales en auditoria_replica.txt; comprobación de que no hay duplicados (entity_id + periodo en primas_mensuales); decisión explícita “réplica aprobada para carga”.

---

### Fase 5 — Carga a Supabase (solo tras aprobar réplica)

| Entrada | Acción |
|---------|--------|
| `replica_db/*.parquet` | Lectura de la réplica local e inserción/upsert en Supabase (entities, primas_mensuales, etc.) |

- Ejecutar solo cuando la réplica local esté validada.
- Opción: script que lea desde `replica_db/` y llame a la API de Supabase (o que genere SQL de INSERT para ejecución manual).
- Tras la carga: ejecutar `scripts/consulta_supabase.py` y comparar conteos con `replica_db` (y con auditoria_replica.txt).

---

## 4. Resumen de auditorías

| Fase | Dónde se audita | Qué se revisa |
|------|------------------|---------------|
| 1    | audit/by_source + manifest | Que cada raw tenga salida; muestras de extracción |
| 2    | staged/{YYYY} + reporte_staged | Conteos, totales por archivo, esquema unificado |
| 3    | clean/{YYYY} + validacion_YYYY.json | Reglas de validación, duplicados, consistencia |
| 4    | replica_db/ + auditoria_replica.txt | Conteos por tabla, totales, listos para subir |
| 5    | Supabase (tras carga) | Conteos vs replica_db; consultas de muestra |

---

## 5. Orden de implementación sugerido

1. **Definir y crear carpetas** (ya existe raw, audit, staged, clean; añadir y usar `data/replica_db/`).
2. **Fase 1:** Implementar o ajustar extracción raw → by_source por tipo (Excel por hoja/archivo, PDF por tablas + texto); manifest index.
3. **Fase 2:** Implementar by_source → staged por tipo y año; reporte_staged por año.
4. **Fase 3:** Implementar staged → clean por año; validación y manifest en clean.
5. **Fase 4:** Implementar clean → replica_db (construcción de tablas locales); manifest_replica y auditoria_replica.
6. **Fase 5:** Script de carga replica_db → Supabase; ejecutar solo cuando la réplica esté aprobada.

**Implementado:** pipeline del **anuario 2023** (Seguro en Cifras): `python scripts/pipeline_anuario_2023.py`. Genera by_source (PDF) y staged/2023 (entidades + métricas). Ver `docs/ANUARIO_2023_PIPELINE.md`.

---

## 6. Configuración en el proyecto

- **Réplica local:** ruta en `config/settings.py`: `DATA_REPLICA = BASE_DIR / "data" / "replica_db"`.
- **Auditoría (by_source, manifest):** ya existen `DATA_AUDIT_BY_SOURCE`, `DATA_AUDIT_MANIFEST`; el espejo antiguo está en `DATA_AUDIT_MIRROR`; la réplica “oficial” pre-nube es `DATA_REPLICA`.

Con esta estructura y este proceso se mantiene trazabilidad, se audita en cada capa y se garantiza una réplica local limpia antes de cargar en la nube.
