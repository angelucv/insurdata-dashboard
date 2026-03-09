# Extracción del PDF anuario: tabla a tabla

El anuario "Seguro en Cifras" está estructurado por **cuadros numerados** (Nº 4, 5-A, 6, etc.), cada uno con título y página(s). Es **coherente y recomendable** extraer la información del PDF siguiendo ese esquema: **una extracción por cuadro**, con identificación clara de número, título y página.

## Ventajas de extraer tabla a tabla

| Aspecto | Extracción global (actual) | Extracción tabla a tabla |
|---------|----------------------------|---------------------------|
| **Trazabilidad** | Todas las tablas en un CSV; no se sabe qué filas corresponden a qué cuadro | Un archivo (o bloque) por cuadro; se sabe exactamente el origen |
| **Semántica** | Hay que inferir la métrica (primas, siniestros, etc.) después | Cada cuadro tiene título en el índice → se puede mapear a `metric_name` (primas_netas_cobradas, siniestros_pagados, etc.) |
| **Validación** | Difícil contrastar “cuadro 4” vs documento | Se puede validar cuadro por cuadro contra el PDF |
| **Páginas** | Camelot extrae todo el PDF de golpe; mezcla de tablas | Se extrae solo la página (o rango) del cuadro → menos ruido |
| **Reproceso** | Si falla una tabla, se reprocesa todo | Se puede reprocesar solo el cuadro que falle |

## Estructura del índice (ya presente en el PDF)

El índice del anuario tiene esta forma (ejemplo del archivo ya extraído):

| Columna 0 (Nº) | Columna 1 (Sección) | Columna 2 (Título del cuadro) | Columna 3 (Página) |
|----------------|---------------------|--------------------------------|--------------------|
| 4 | EMPRESAS DE SEGUROS | PRIMAS NETAS COBRADAS POR RAMO/EMPRESA. SEGURO DIRECTO | 19 |
| 5-A | EMPRESAS DE SEGUROS | PRIMAS NETAS COBRADAS POR RAMO/EMPRESA. SEGUROS DE PERSONAS... | 20-21 |
| 6 | EMPRESAS DE SEGUROS | PRESTACIONES Y SINIESTROS PAGADOS POR RAMO. SEGURO DIRECTO | 27 |
| ... | ... | ... | ... |

Con esto se puede:
1. **Parsear el índice** (desde las primeras páginas del PDF o desde un CSV de índice).
2. **Para cada fila con número y página:** extraer solo esa página (o rango, ej. "20-21").
3. **Guardar una salida por cuadro**, por ejemplo: `by_source/seguros-en-cifra-2023_cuadro_4_p19.csv`, con metadato: `cuadro_id=4`, `titulo=...`, `pagina=19`, `metric_semantic=primas_netas_cobradas`.

## Esquema propuesto de salida

```
data/audit/by_source/
├── seguros-en-cifra-2023_indice.csv          # Índice parseado (Nº, sección, título, página)
├── seguros-en-cifra-2023_cuadro_4_p19.csv    # Contenido del Cuadro 4 (primas netas por ramo/empresa)
├── seguros-en-cifra-2023_cuadro_5A_p20-21.csv
├── seguros-en-cifra-2023_cuadro_6_p27.csv
└── ...
```

Cada CSV de cuadro puede incluir (en comentario o en un manifest) el `cuadro_id`, `titulo`, `pagina` y `metric_semantic` para que el siguiente paso (staged) sepa qué métrica asignar sin tener que adivinar.

## Flujo recomendado

1. **Obtener el índice**  
   - Opción A: extraer solo las primeras páginas del PDF (donde está el índice) y parsear la tabla de contenidos.  
   - Opción B: usar el CSV global ya generado y tomar las filas que corresponden al índice (las que tienen número de cuadro y página en columnas 0 y 3).

2. **Por cada cuadro en el índice:**  
   - Resolver la página o rango (ej. "19" → página 19; "20-21" → páginas 20 a 21).  
   - Llamar al extractor (Camelot o pdfplumber) con `pages="19"` o `pages="20-21"`.  
   - Guardar el resultado en `by_source/{archivo}_cuadro_{id}_p{paginas}.csv`.  
   - Registrar en un manifest: `cuadro_id`, `titulo`, `pagina`, `archivo_csv`, `metric_semantic` (opcional).

3. **Staged / clean**  
   - Leer cada CSV de cuadro; ya se sabe la métrica por el `cuadro_id` o `metric_semantic`.  
   - Unificar columnas (empresa, ramo, valor, etc.) y escribir en staged/clean con `metric_name` correcto.

Así la extracción del PDF queda **alineada con la estructura del documento** (tabla a tabla) y es coherente con un esquema paso a paso.
