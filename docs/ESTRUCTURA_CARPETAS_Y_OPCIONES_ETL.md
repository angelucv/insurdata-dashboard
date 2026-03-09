# Estructura de carpetas y opciones de ETL

Este documento: (1) verifica la estructura actual de carpetas, (2) describe el contenido base en `data/raw/`, y (3) propone **tres opciones** de lógica para rehacer el vaciado desde los archivos base hasta Supabase.

---

## 1. Estructura actual de carpetas (configuración)

Definida en `config/settings.py` y `config/audit_paths.py`:

```
data/
├── raw/                    # ÚNICA fuente de verdad — archivos base (no se borra en reset)
│   ├── pdf/                # PDFs: anuarios, boletines, Seguro en Cifras
│   ├── xlsx/               # Excel: resumen por empresa, cuadro resultados, primas, margen solvencia, etc.
│   ├── .gitkeep
│   └── test_camelot_tabla.pdf
│
├── processed/              # Salida lista para consumo (Parquet); fallback del dashboard
├── staged/                 # Una salida por archivo fuente y año (CSV/Parquet normalizado)
│   └── {YYYY}/             # ej. 2023/
├── clean/                  # Compilado por año, esquema unificado, validado
│   └── {YYYY}/
└── audit/                  # Trazabilidad sin tocar la BD
    ├── mirror/             # Espejo de tablas (entities, primas_mensuales, exchange_rates, etc.)
    │   ├── entities/
    │   ├── primas_mensuales/
    │   ├── exchange_rates/
    │   ├── margen_solvencia/
    │   └── series_historicas/
    ├── by_source/          # Una salida por archivo procesado (CSV + pdf_text/)
    └── manifest/           # Índice de descargas y extracciones (index.json, descargas.csv)
```

**Estado esperado tras reset:** solo `data/raw/` tiene archivos; `processed`, `staged`, `clean` y `audit` están vacíos (las carpetas existen, sin contenido).

---

## 2. Verificación: contenido base en `data/raw/`

Tras el reset, en **raw** se conserva:

| Ubicación | Contenido típico |
|-----------|-------------------|
| **raw/pdf/** | Anuarios "Seguro en Cifras" (1967–2024), boletines mensuales "Boletín en Cifras", GOE, algún XLSX de anuario |
| **raw/xlsx/** | Cuadro de resultados, Resumen por empresa, Índices por empresa, Saldo de operaciones, Primas netas cobradas por empresa, Margen de solvencia, Cuadros descargables (Seguro en cifras), series históricas |

Tipos de archivos que el ETL actual reconoce por nombre:

- **Excel:** `resumen-por-empresa-*.xlsx`, `primas-netas-cobradas-por-empresa-*.xlsx`, `cuadro-de-resultados-*.xlsx`, `cuadros descargables_Seguro en cifras *.xlsx`, `Margen de Solvencia *.xlsx`, etc.
- **PDF:** `seguros-en-cifra-*.pdf`, `Seguro-en-Cifras-*.pdf`, boletines, etc.

Para listar en tu máquina:

```bash
python scripts/verificar_estructura_carpetas.py
```

(o revisar manualmente `data/raw/pdf/` y `data/raw/xlsx/`).

---

## 3. Tres opciones de lógica para el vaciado (ETL desde archivos base)

Todas parten de **solo** `data/raw/` como fuente; difieren en cuántas capas intermedias usar y si priorizas velocidad, validación año a año o trazabilidad máxima.

---

### Opción A — Directo: Raw → Supabase (mínimo)

**Flujo:** `data/raw/` → ETL en memoria → **Supabase**. Opcionalmente se escribe un Parquet en `data/processed/` como respaldo.

```
raw/  ──►  [ETL: loaders Excel/PDF → entities + primas_mensuales]  ──►  Supabase
                (opcional: processed/primas_mensuales.parquet)
```

| Ventajas | Desventajas |
|----------|-------------|
| Un solo paso; más rápido de ejecutar | Poca trazabilidad: no queda por archivo qué se cargó |
| Menos carpetas que mantener | Difícil depurar por año o por archivo sin reprocesar todo |
| Ya implementado en `run_etl_to_supabase.py` | Validación solo a posteriori en Supabase |

**Cuándo usarla:** Quieres cargar todo de una vez y no te importa no tener capas intermedias.  
**Script:** `python scripts/run_etl_to_supabase.py` (con o sin `--year`, `--debug`).

---

### Opción B — Staged + Clean por año (validación explícita)

**Flujo:** `data/raw/` → **staged** (una salida por archivo fuente, por año) → validación → **clean** (un dataset por año) → Supabase.

```
raw/  ──►  staged/{YYYY}/     (un CSV/Parquet por archivo, esquema unificado)
                │
                ▼  validación (filas, totales, duplicados)
                │
                ▼
           clean/{YYYY}/      (primas_YYYY.parquet, entities_YYYY.parquet)
                │
                ▼
           Supabase
```

| Ventajas | Desventajas |
|----------|-------------|
| Validas por año y por archivo antes de tocar la BD | Más pasos y más código/orquestación |
| Puedes reprocesar solo un año | Requiere rellenar staged y clean en el código actual |
| Fácil comparar “qué salió de este Excel” vs totales | staged y clean ocupan más disco |

**Cuándo usarla:** Quieres control año a año y poder revisar en disco antes de cargar.  
**Pasos:** (1) Implementar/ajustar “raw → staged” por tipo de archivo y año; (2) scripts de validación sobre staged; (3) “staged → clean” por año; (4) carga desde clean a Supabase (reutilizando entity resolution y upsert).

---

### Opción C — Audit-first (trazabilidad y reproceso sin releer PDF/Excel)

**Flujo:** `data/raw/` → **audit** (by_source + mirror + manifest) → desde mirror o by_source → **clean** (opcional) → Supabase.

```
raw/  ──►  audit/by_source/   (un CSV por archivo + pdf_text cuando aplique)
                │
                ▼
           audit/mirror/      (entities.csv, primas_mensuales.csv, etc.)
                │
                ▼  (opcional) clean/{YYYY}/
                │
                ▼
           Supabase
```

| Ventajas | Desventajas |
|----------|-------------|
| Trazabilidad completa: qué archivo generó qué | Más disco y más pasos |
| Puedes reprocesar desde audit sin volver a leer PDF/Excel | La capa audit ya existe pero no está unificada con el flujo a Supabase |
| Útil para auditoría y depuración | Requiere definir bien “mirror → clean” o “mirror → Supabase” |

**Cuándo usarla:** Necesitas trazabilidad y poder rehacer el vaciado desde una capa intermedia sin tocar raw.  
**Pasos:** (1) Ejecutar `audit_local_pipeline.py` (raw → audit); (2) definir si la carga va desde mirror o desde clean; (3) script que lea mirror (o clean) y cargue a Supabase.

---

## 4. Resumen y recomendación

| Criterio | Opción A | Opción B | Opción C |
|----------|----------|----------|----------|
| Complejidad | Baja | Media | Media-Alta |
| Trazabilidad | Baja | Por año/archivo | Alta (por archivo + mirror) |
| Validación antes de BD | No | Sí (staged/clean) | Sí (audit) |
| Estado en el código | Lista | Parcial (staged/clean por definir) | Parcial (audit existe, falta unificar carga) |

- **Para empezar rápido:** usar **Opción A** con `run_etl_to_supabase.py` (y opcionalmente `--year 2023 --debug`).
- **Para control por año y validación en disco:** avanzar hacia **Opción B** (staged → clean → Supabase).
- **Para auditoría y reproceso sin releer raw:** usar **Opción C** (audit primero, luego mirror/clean → Supabase).

El script `scripts/reset_etl_mantener_raw.py` deja siempre solo `data/raw/` con datos; processed, staged, clean y audit se vacían. Cualquiera de las tres opciones puede ejecutarse tras ese reset.
