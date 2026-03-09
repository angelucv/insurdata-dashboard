# Auditoría local y estructura espejo

Flujo para **revisar todos los Excel localmente**, **descargar anuarios** desde SUDEASEG (incl. desde 1967), **tratar PDFs escaneados con OCR** y **crear una estructura en disco tipo espejo** de la base de datos antes de cargar nada a Supabase.

## 1. Estructura en disco (espejo de la base de datos)

```
data/
  raw/                    # Descargas (Excel, PDF, anuarios)
    xlsx/
    pdf/
    anuario/
      pdf/
      xlsx/
  audit/
    mirror/               # Tablas en CSV (mismo esquema lógico que la DB)
      entities/entities.csv
      primas_mensuales/primas_mensuales.csv
      exchange_rates/
      margen_solvencia/
      series_historicas/
    by_source/            # Una extracción por archivo origen (trazabilidad)
    manifest/
      index.json           # Índice de la última ejecución del pipeline
      descargas.csv        # Enlaces de anuarios descargados
```

- **mirror**: datos compilados listos para revisar y, luego, cargar a la DB.
- **by_source**: extracción cruda por archivo (qué salió de cada Excel/PDF).
- **manifest**: qué se procesó, cuántas filas y posibles errores.

## 2. Revisión inicial de todos los Excel (solo local)

```bash
python scripts/revision_excel_local.py
```

- Recorre `data/raw` (incl. subcarpetas) y lista cada `.xlsx`/`.xls`.
- Por archivo: hojas, filas × columnas y muestra de la primera fila.
- No usa base de datos.

## 3. Descargar anuarios (desde 1967)

```bash
python scripts/audit_descargar_anuarios.py
```

- Entra en la sección **Cifras anuales** de SUDEASEG.
- Detecta enlaces a PDF/Excel y años en URL o texto (1967–2024).
- Descarga todo en `data/raw/anuario/pdf` y `data/raw/anuario/xlsx`.
- Escribe `data/audit/manifest/descargas.csv` con cada enlace y si se descargó.

Configuración: `config/settings.py` → `SUDEASEG_ANUARIOS_PATH`, `ANUARIO_YEAR_MIN` (por defecto 1967).

## 4. PDFs escaneados (OCR)

Para anuarios o boletines que solo están como imagen:

- **Detección**: si un PDF tiene muy poco texto extraíble (< 200 caracteres), se considera escaneado.
- **OCR**: se usa **Tesseract** (PyMuPDF para renderizar páginas + `pytesseract`).
  - Instalar Tesseract en el sistema y, en Windows, añadirlo al PATH.
  - Idioma español: instalar datos `spa` de Tesseract.
- **Uso**: el pipeline de auditoría y el extractor de PDF (`PDFTableExtractor`) usan OCR cuando detectan PDF escaneado (Camelot/pdfplumber no devuelven tablas).

Dependencias: `pytesseract`, `Pillow` (en `requirements.txt`).

## 5. Pipeline de auditoría local (arqueo)

```bash
python scripts/audit_local_pipeline.py
```

- Lee **todo** lo que haya en `data/raw` (Excel y PDF, incluido `anuario/`).
- **Excel**: identifica tipo (resumen por empresa, primas netas, cuadro resultados) y extrae a filas normalizadas (entidad, periodo, primas, siniestros, gastos).
- **PDF**: extrae tablas (Camelot → pdfplumber → OCR si está escaneado) y guarda en `by_source`.
- Escribe:
  - `mirror/entities/entities.csv` y `mirror/primas_mensuales/primas_mensuales.csv`.
  - Un CSV por archivo en `by_source`.
  - `manifest/index.json` (resumen y errores).

No toca Supabase.

## 6. Verificación de campos compilados

```bash
python scripts/audit_verificar_campos.py
```

- Lee `manifest/index.json` y los CSV del **mirror**.
- Para `primas_mensuales`: cuenta no nulos en `primas_netas_ves`, `siniestros_pagados_ves`, `gastos_operativos_ves`, `entity_normalized_name`, `periodo`.
- Para `entities`: comprueba `normalized_name` y `canonical_name`.
- Lista archivos en `by_source` y número de columnas.
- Sirve para validar que los campos compilados tengan valores antes de cargar a la base.

## 7. Extracción completa (crudo + estructura coherente)

Un solo comando hace verificación de PDF escaneados, extracción cruda, mapeo al espejo y verificación de campos:

```bash
python scripts/ejecutar_extraccion_completa.py
```

- **Fase cruda**: Todo Excel → `by_source/*_extract.csv` (hojas con columnas originales). Todo PDF → texto (nativo o OCR) en `by_source/pdf_text/*.txt` y tablas en `by_source/*_tables.csv`.
- **Fase mapeada**: Variables normalizadas (entidad, periodo, primas, siniestros, gastos) → `mirror/entities/entities.csv` y `mirror/primas_mensuales/primas_mensuales.csv` (estructura lista para carga en nube).

Para solo pipeline (sin verificación previa):

```bash
python scripts/audit_local_pipeline.py
python scripts/audit_verificar_campos.py
```

## 8. Orden recomendado

1. `verificar_pdf_escaneados.py` – Comprobar que OCR extrae de PDFs escaneados.
2. `revision_excel_local.py` – Revisión inicial de Excel (opcional).
3. `audit_local_pipeline.py` o `ejecutar_extraccion_completa.py` – Crudo + espejo.
4. `audit_verificar_campos.py` – Comprobar campos compilados.
5. Cuando el arqueo sea correcto: `run_etl_to_supabase.py` para cargar a la base.

## Archivos tocados / nuevos

- **Config**: `config/settings.py` (rutas `DATA_AUDIT`, `SUDEASEG_ANUARIOS_PATH`, `ANUARIO_YEAR_MIN`), `config/audit_paths.py`.
- **Scraper**: `src/extraction/scraper.py` (`crawl_anuarios`, `list_all_for_audit`, `download_anuarios`).
- **OCR**: `src/extraction/pdf_ocr.py`; integración en `src/extraction/pdf_extractor.py`.
- **Auditoría local**: `src/etl/audit_local.py` (extracción a mirror sin DB).
- **Scripts**: `scripts/revision_excel_local.py`, `scripts/audit_descargar_anuarios.py`, `scripts/audit_local_pipeline.py`, `scripts/audit_verificar_campos.py`.
- **Docs**: `data/audit/README.md`, `docs/AUDITORIA_LOCAL.md`.
