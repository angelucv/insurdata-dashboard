# Verificación de resultados — Anuario 2023

## Archivos generados

| Ubicación | Archivo | Tamaño (bytes) | Descripción |
|-----------|---------|----------------|-------------|
| **audit/by_source/** | `seguros-en-cifra-2023_tables.csv` | ~10 KB | Tablas extraídas del PDF (índice de cuadros, estructura). Usado como respaldo si se reprocesa desde PDF. |
| **staged/2023/** | `anuario_2023_entidades.csv` | ~37 KB | 288 filas: entidades detectadas (empresas + títulos de sección). |
| **staged/2023/** | `anuario_2023_metricas.csv` | ~701 KB | 7.431 filas: métricas por entidad (value, unit, metric_name). |
| **staged/2023/** | `reporte_anuario_2023.txt` | ~0,6 KB | Resumen del pipeline (fuentes, vaciado, conteos). |

**Fuente usada en el vaciado:** `seguros-en-cifra-2023.xlsx` (Excel tipo Adobe Table 1).

---

## Verificación de resultados

### Entidades (`anuario_2023_entidades.csv`)

| Concepto | Valor |
|----------|--------|
| Total filas | 288 |
| **Parecen empresa** (Seguros, C.A., S.A., Reaseguros, etc.) | **164** |
| Títulos / secciones / notas (BALANCE, ESTADO DE GANANCIAS, párrafos de texto) | **124** |

- Las empresas reales aparecen a partir de filas como "Adriática de Seguros, C.A.", "Altamira C.A., Seguros", "Banesco Seguros C.A.", etc.
- Mezcladas con ellas hay encabezados de cuadro ("BALANCE CONDENSADO", "ESTADO DE GANANCIAS Y PÉRDIDAS..."), notas al pie y párrafos largos que el loader interpretó como “entidad”.

**Recomendación:** filtrar para clean/replica dejando solo las ~164 que parecen empresa (por palabras clave o lista conocida de aseguradoras).

### Métricas (`anuario_2023_metricas.csv`)

| Concepto | Valor |
|----------|--------|
| Total filas | 7.431 |
| `metric_name` único | **"otro"** (el mapeo de cabeceras no identificó primas/siniestros/reservas, etc.) |
| `value`: mínimo | -158,00 |
| `value`: máximo | 113.947.880,56 |
| `value`: media | 23.397,30 |
| Filas con value > 1.000 (posibles montos en miles Bs) | **213** |

- Hay valores que parecen montos reales (miles Bs) y otros que parecen índices de fila/página (102, 103, 113, etc.).
- Las filas con `entity_name` = empresas (p. ej. Adriática, Altamira) y `value` grande son las que tienen sentido para indicadores; el resto conviene revisar o excluir.

**Recomendación:** en clean, conservar solo filas donde `entity_name` sea una entidad válida (tras filtrar entidades) y, si se puede, etiquetar `metric_name` (primas, siniestros, reservas, etc.) a partir de la estructura del Excel o del PDF.

### By_source (`seguros-en-cifra-2023_tables.csv`)

- Contiene el índice de cuadros del PDF (columnas 0–3: número de cuadro, “EMPRESAS DE SEGUROS”, nombre del cuadro, página).
- Sirve como trazabilidad de la extracción del PDF; el vaciado actual se hizo desde el XLSX.

---

## Conclusión

- **Archivos generados:** 4 (1 en by_source, 3 en staged/2023).
- **Datos útiles:** ~164 entidades tipo empresa y una parte de las 7.431 métricas (sobre todo las con value > 1.000 y entidad = empresa).
- **Para clean/replica:** filtrar entidades (solo empresas), depurar métricas (excluir “valor” = índice de fila) y, si es posible, mejorar el mapeo de cabeceras para obtener `metric_name` distinto de "otro".
