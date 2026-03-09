# Pipeline Anuario 2023 (Seguro en Cifras)

Primer flujo implementado siguiendo la propuesta de **capas intermedias y auditoría** antes de cargar a la nube.

## Archivos involucrados

| Origen | Ubicación |
|--------|-----------|
| **Crudo** | `data/raw/pdf/seguros-en-cifra-2023.pdf`, `data/raw/pdf/seguros-en-cifra-2023.xlsx` |
| **By source** | `data/audit/by_source/seguros-en-cifra-2023_tables.csv` (extracción del PDF) |
| **Staged** | `data/staged/2023/anuario_2023_entidades.csv`, `anuario_2023_metricas.csv`, `reporte_anuario_2023.txt` |

## Cómo ejecutar

Desde la raíz del proyecto (con el venv activado):

```bash
python scripts/pipeline_anuario_2023.py
```

El script:

1. Lista fuentes de anuario 2023 (PDF y XLSX en `data/raw`).
2. Si existe el PDF y aún no está en by_source, extrae las tablas del PDF a `audit/by_source/seguros-en-cifra-2023_tables.csv`.
3. Ejecuta el vaciado para 2023: **prefiere el XLSX** si está disponible (estructura tipo “Adobe Table 1”); si no, usa el CSV del PDF.
4. Escribe en `staged/2023/`:
   - `anuario_2023_entidades.csv`: entidades detectadas (anio, source_file, entity_name, entity_normalized_name).
   - `anuario_2023_metricas.csv`: métricas (anio, entity_name, metric_name, value, unit, etc.).
   - `reporte_anuario_2023.txt`: resumen para auditoría (fuentes, conteos, métricas distintas).

## Auditoría recomendada

Antes de pasar a **clean** o **replica_db**:

1. **Revisar el reporte**  
   `data/staged/2023/reporte_anuario_2023.txt`: número de entidades, de filas de métricas y de métricas distintas.

2. **Revisar entidades**  
   Abrir `anuario_2023_entidades.csv` y comprobar que las filas correspondan a **aseguradoras/entidades** y no a títulos de sección (p. ej. “BALANCE CONDENSADO”, “ESTADO DE GANANCIAS…”). El loader actual puede incluir bloques que son encabezados de cuadro; en ese caso conviene filtrar o ajustar el loader.

3. **Revisar métricas**  
   Abrir `anuario_2023_metricas.csv`: comprobar que `metric_name` y `value` tengan sentido (primas, siniestros, etc.). Si muchas filas tienen `metric_name = "otro"` o valores que parecen índices de fila, el mapeo de cabeceras puede necesitar ajuste.

4. **Comparar con el PDF**  
   Si se usó el XLSX para el vaciado, opcionalmente contrastar totales o empresas con el anuario en PDF para validar cobertura.

## Siguientes pasos (clean y réplica)

Cuando el contenido de **staged/2023** esté validado:

- Definir reglas para filtrar entidades (solo aseguradoras, excluir títulos de cuadro).
- Generar **clean/2023/** a partir de `staged/2023` (por ejemplo un único dataset por año con entidades y métricas listas para BD).
- Incorporar ese clean en la **réplica local** (`data/replica_db/`) y, tras una nueva auditoría, cargar a Supabase.

## Nota sobre el XLSX 2023

El archivo `seguros-en-cifra-2023.xlsx` tiene estructura tipo “Adobe Table 1” (una hoja con bloques). El módulo `vaciar_excel_adobe_anuario` detecta bloques por la celda “Empresa” y extrae filas. Según el diseño real del archivo, pueden colarse:

- Secciones o títulos de cuadro como si fueran “entidades”.
- Valores que no son métricas (p. ej. números de fila).

Revisar siempre `staged/2023` antes de dar por bueno el paso a clean y réplica.
