# SUDEASEG Dashboard — Inteligencia de Datos del Sector Asegurador Venezolano

Panel de control (dashboard) de inteligencia de negocios basado en datos históricos de la **Superintendencia de la Actividad Aseguradora (SUDEASEG)** de Venezuela. Incluye extracción híbrida (web + PDF + Excel), normalización monetaria con tasas BCV, ETL con pandas, persistencia en **Supabase (PostgreSQL)** y visualización con **Streamlit**.

## Requisitos

- **Python 3.10+**
- **Ghostscript** (para Camelot): [Descarga](https://www.ghostscript.com/download.html)
- Cuenta en [Supabase](https://supabase.com) (opcional; se puede usar solo datos locales)

## Instalación

```bash
cd sudeaseg-dashboard
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
cp .env.example .env
# Editar .env con SUPABASE_URL y SUPABASE_KEY si usas Supabase
```

## Estructura del proyecto

Para verificar carpetas: `python scripts/verificar_estructura_carpetas.py`.  
**Proceso con auditorías y réplica local:** `docs/PROPUESTA_ETL_AUDITORIA_Y_REPLICA_LOCAL.md`.  
**Anuario 2023 (Seguro en Cifras):** `python scripts/pipeline_anuario_2023.py` → ver `docs/ANUARIO_2023_PIPELINE.md`.

```
sudeaseg-dashboard/
├── app.py                 # Entrada del dashboard (streamlit run app.py)
├── pages/                  # Páginas multipage de Streamlit
│   ├── 1_Resumen.py
│   ├── 2_Primas_Siniestros.py
│   └── 3_Por_Empresa.py
├── config/
│   └── settings.py        # URLs, rutas, variables de entorno
├── src/
│   ├── extraction/        # Scraping SUDEASEG, PDF (Camelot), Excel, BCV
│   ├── etl/               # Transformadores pandas, entity resolver, pipeline
│   ├── db/                # Esquema SQL y cliente Supabase
│   └── app/               # Componentes del dashboard (auth, data_loader)
├── scripts/
│   ├── run_extraction.py   # Descarga archivos del portal SUDEASEG
│   ├── run_etl.py          # ETL y carga a Supabase
│   ├── run_etl_to_supabase.py  # Solo ETL (sin descargas)
│   ├── reset_etl_mantener_raw.py  # Borra processed/staged/clean/audit; deja solo raw
│   ├── truncate_supabase.py       # Vacía tablas para empezar de cero
│   └── verificar_carga.py         # Verifica consistencia Excel vs Supabase
├── data/
│   ├── raw/               # PDF y XLSX descargados
│   └── processed/         # Parquet listos para BD
└── requirements.txt
```

## Uso

### 1. Extracción

Descarga automática de enlaces a PDF y XLSX desde la sección de estadísticas de SUDEASEG (ajustar `SUDEASEG_BASE_URL` y `SUDEASEG_ESTADISTICAS_PATH` en `config/settings.py` según el portal oficial):

```bash
python scripts/run_extraction.py
```

Los archivos se guardan en `data/raw/` por extensión (`pdf/`, `xlsx/`).

### 2. ETL

Procesa archivos en `data/raw/`, aplana cabeceras MultiIndex, imputa nulos, normaliza entidades y opcionalmente convierte VES → USD con tasas BCV. Salida en `data/processed/` y, si está configurado, carga en Supabase:

```bash
python scripts/run_etl.py
```

### 3. Vaciar y cargar desde cero
Si la base tiene datos erróneos:
1. En **Supabase → SQL Editor** ejecuta el contenido de `src/db/truncate_all.sql` (vacía todas las tablas).
2. Opcional: ejecuta `src/db/policy_delete_anon.sql` si quieres que `truncate_supabase.py` pueda borrar por API.
3. Carga de nuevo: `python scripts/run_etl_to_supabase.py`.
4. Verificación: `python scripts/verificar_carga.py` (compara filas esperadas vs Supabase).

### 4. Reiniciar ETL desde cero (solo datos crudos)
Para borrar **todos** los datos procesados y volver a empezar, manteniendo solo los archivos crudos en `data/raw/`:

```bash
python scripts/reset_etl_mantener_raw.py
```

Esto elimina el contenido de `data/processed/`, `data/staged/`, `data/clean/` y `data/audit/`. **No modifica** `data/raw/`. Después:
- Si también quieres vaciar Supabase: en el **SQL Editor** del proyecto ejecuta `src/db/truncate_all.sql` (cuando el proyecto esté activo).
- Vuelve a ejecutar el ETL: `python scripts/run_etl_to_supabase.py`.

### 5. Base de datos (Supabase)

1. Crear proyecto en [Supabase](https://supabase.com/dashboard).
2. En SQL Editor, ejecutar el contenido de `src/db/schema.sql`.
3. En `.env` definir `SUPABASE_URL` y `SUPABASE_KEY`.

### 6. Dashboard

```bash
streamlit run app.py
```

Se abre en el navegador. Si en `.env` hay `SUPABASE_URL` y `SUPABASE_KEY`, se puede activar autenticación (Supabase Auth) desde `src/app/components/auth.py`.

## Consideraciones

- **SUDEASEG**: Si el portal cambia estructura o URLs, hay que actualizar el scraper y, si aplica, los extractores de tablas PDF (Camelot/pdfplumber).
- **Tasas BCV**: El módulo `bcv_client` usa APIs públicas o scraping; conviene cachear tasas en la tabla `exchange_rates` para no depender de disponibilidad en tiempo real.
- **Hosting**: El documento recomienda **Streamlit Community Cloud** (repositorio público) o **Render** para código privado; **Oracle Cloud Always Free** para mayor control y disponibilidad.

## Licencia

Uso según normativa aplicable a datos públicos de SUDEASEG y condiciones de las herramientas de terceros utilizadas.
