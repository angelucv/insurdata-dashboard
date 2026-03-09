# Análisis de archivos crudos y propuesta de proceso/estructura

Verificación de la coherencia entre lo que hay en `data/raw/`, lo que el ETL actual usa y una propuesta concreta de proceso y estructura de carpetas.

---

## 1. Inventario de archivos crudos (verificado)

### 1.1 Por ubicación y tipo

| Ubicación | Cantidad | Contenido |
|-----------|----------|-----------|
| **raw/pdf/** | 119 | Anuarios, boletines mensuales, GOE, 1 anuario 1986; algunos XLSX dentro de pdf/ (anuarios 2014–2023) |
| **raw/xlsx/** | 72 | Resumen, cuadro resultados, primas, margen solvencia, índices, saldo operaciones, cuadros descargables, series históricas |
| **raw/** (raíz) | 2 | .gitkeep, test_camelot_tabla.pdf |

### 1.2 Excel (xlsx) por tipo y años detectables

El ETL extrae el año del **nombre del archivo** con el patrón `20XX`. Archivos sin año en el nombre (ej. `1_Cuadro_de_Resultados_Dic.xlsx`) quedan con año `None` y se **excluyen** si se filtra por año.

| Tipo de archivo | Patrón en nombre | Años presentes (en nombre) | Loader ETL actual |
|-----------------|------------------|----------------------------|-------------------|
| **Resumen por empresa** | resumen-por-empresa / resumen-de-empresa | 2015–2020, 2021 (resumen-de-empresa), 2022, 2023; Dic resumen-por-empresa-2024 | `resumen_por_empresa` ✓ |
| **Primas netas por empresa** | primas-netas-cobradas-por-empresa | 2015–2023; Dic primas-netas-...-2024 | `primas_netas_por_empresa` ✓ |
| **Cuadro de resultados** | cuadro-de-resultados / cuadros-de-resultados | 2015, 2017–2023; Dic cuadro-de-resultados-2024 | `cuadro_resultados` ✓ |
| **Cuadros descargables (Seguro en cifras)** | cuadros descargables / Seguro en cifras | Solo 2024 | `seguro_en_cifras_anual` ✓ |
| **Margen de solvencia** | Margen de Solvencia | 2015–2024 (IV Trim), 2025 (III Trim) | `excel_generico` ⚠️ (no hay loader específico → tabla `margen_solvencia`) |
| **Índices por empresa** | indices-por-empresa / indice-por-empresa | 2015–2023; Dic indice-por-empresa-2024 | `excel_generico` ⚠️ (no va a primas_mensuales) |
| **Saldo de operaciones** | saldo-de-operaciones-por-empresa | 2015–2023; Dic saldo-de-operaciones-...-2024 | `excel_generico` ⚠️ |
| **Series históricas** | series-historicas | 2014-2018 (un archivo) | `excel_generico` ⚠️ |
| **Sin año en nombre** | 1_Cuadro_..., 2_Resumen_..., 3_Indice_..., 4_Saldo_..., 5_Primas_... (Dic/Ene) | — | Se omiten si se usa `--year` o rango de años |

### 1.3 PDF

| Tipo | Ejemplos | Año en nombre | Loader ETL |
|------|----------|----------------|-------------|
| Anuarios "Seguro en Cifras" | Seguro-en-Cifras-1970, seguros-en-cifra-1999, seguro-en-cifras-2023 | 1967–2024 (19XX/20XX) | `load_pdf_tables_to_supabase` (genérico) |
| Boletines mensuales | Boletín en Cifras Ene 2022, … Dic 2024; Boletín Cifras Nro 40–51 | 2021–2026 | Idem |
| Otros | GOE 6.770, boletin.24.1.1964 | No o distinto | Idem |

Nota: `_year_from_path` solo busca `20\d{2}`; archivos con solo `19XX` (anuarios antiguos) tienen año `None` y se excluyen si se filtra por año.

---

## 2. Coherencia con las tres propuestas (opciones A/B/C)

### 2.1 Opción A (directo raw → Supabase)

- **Coherente** con el inventario: el ETL actual recorre `data/raw` (incl. subcarpetas) y aplica loaders por nombre.
- **Limitaciones:**
  - Archivos sin año en el nombre se procesan solo si **no** se usa `--year` ni rango; si se usa, se omiten.
  - **Margen de solvencia**, **índices**, **saldo de operaciones** y **series históricas** caen en `excel_generico`: se intenta mapear a primas_mensuales; no hay carga específica a `margen_solvencia` ni a tablas de índices/series.
  - PDF: muchos diseños distintos; el loader genérico puede dar resultados desiguales.

### 2.2 Opción B (staged + clean por año)

- **Coherente** si se define un flujo por tipo y año: los Excel con año en el nombre (2015–2024) son adecuados para staged por año y luego clean.
- **Recomendación:** priorizar en staged/clean los tipos que ya tienen loader dedicado (resumen, primas netas, cuadro resultados, seguro en cifras) y tratar margen/índices/saldo/series en una segunda fase con loaders específicos.

### 2.3 Opción C (audit-first)

- **Coherente** con el volumen actual: by_source puede tener un CSV (o equivalente) por cada archivo raw; mirror puede consolidar por tabla.
- Los Excel dentro de `raw/pdf/` (anuarios en xlsx) se descubren con `rglob("*.xlsx")`, así que entran en el mismo flujo.

---

## 3. Incoherencias y riesgos detectados

| Tema | Detalle | Impacto |
|------|---------|---------|
| **Año en nombre** | Archivos `1_Cuadro_...`, `2_Resumen_...`, etc. no tienen 20XX | Omitidos al filtrar por año; año indefinido en carga directa |
| **Margen de solvencia** | Loader genérico; tabla `margen_solvencia` existe en esquema | No se rellenan margen_solvencia desde Excel específicos |
| **Índices / Saldo / Series** | Sin loader dedicado | No se cargan a tablas específicas; solo posible mapeo genérico a primas si columnas coinciden |
| **Resumen 2021** | Nombre `resumen-de-empresa-2021` (no "resumen-por-empresa") | El loader usa "resumen" + "empresa" → sí lo toma ✓ |
| **Anuarios 19XX** | Año en nombre es 1967, 1986, etc. | Con filtro por año 20XX se excluyen; sin filtro sí se procesan (PDF) |
| **Excel en raw/pdf/** | Varios .xlsx dentro de pdf/ | Se incluyen por rglob; conviene no duplicarlos en raw/xlsx |

---

## 4. Propuesta recomendada: proceso y estructura de carpetas

Sugerencia que mantiene la estructura actual, ordena el uso de raw y añade una capa de control sin complicar demasiado.

### 4.1 Estructura de carpetas (mantener y usar así)

```
data/
├── raw/                          # ÚNICA fuente de verdad (no tocar en reset)
│   ├── pdf/                      # Solo PDF (anuarios, boletines); opcional: mover .xlsx de anuarios a xlsx/
│   ├── xlsx/                     # Solo Excel (todos los tipos)
│   └── .gitkeep
│
├── staged/                       # Salida por archivo fuente, por año (para validar)
│   └── {YYYY}/
│       ├── resumen_por_empresa_YYYY.csv
│       ├── primas_netas_por_empresa_YYYY.csv
│       ├── cuadro_resultados_YYYY.csv
│       └── ...
│
├── clean/                        # Un dataset por año, listo para carga
│   └── {YYYY}/
│       ├── primas_YYYY.parquet   # primas_mensuales + entidades implícitas
│       └── manifest_YYYY.json    # Fuentes usadas, checksums (opcional)
│
├── processed/                    # Salida global (opcional): union de clean o salida directa ETL
│   └── primas_mensuales.parquet  # Fallback del dashboard
│
└── audit/                        # Solo si se usa Opción C
    ├── by_source/
    ├── mirror/
    └── manifest/
```

Recomendación operativa:

- **raw:** dejar todo como está; opcionalmente mover los `.xlsx` que están hoy en `raw/pdf/` a `raw/xlsx/` (mismo nombre) para tener “todo Excel en xlsx, todo PDF en pdf” y evitar confusiones.
- **staged:** usar solo para los tipos con loader claro (resumen, primas netas, cuadro resultados, seguro en cifras) y, en una segunda fase, margen de solvencia cuando exista loader.
- **clean:** compilar por año desde staged; un solo artefacto principal por año (p. ej. `primas_YYYY.parquet`) para cargar a Supabase.
- **processed:** opcional; puede ser la unión de clean o la salida del ETL directo (Opción A).

### 4.2 Proceso sugerido (por fases)

**Fase 1 — Arranque rápido (Opción A mejorada)**  
1. Mantener `data/raw` tal cual (pdf/ + xlsx/).  
2. Ejecutar ETL directo a Supabase para los tipos que ya funcionan:
   - `python scripts/run_etl_to_supabase.py --year 2023 --debug`
   - Revisar en Supabase que primas_mensuales y entities se llenen bien.  
3. Opcional: extender `_year_from_path` para aceptar `19XX` si se quieren incluir anuarios antiguos al filtrar por año.  
4. Opcional: normalizar nombres de archivos sin año (ej. `1_Cuadro_de_Resultados_Dic.xlsx` → `cuadro-de-resultados-2024-Dic.xlsx` o inferir año por contenido) para que entren en filtros por año.

**Fase 2 — Staged + clean (Opción B parcial)**  
1. Implementar “raw → staged” por tipo y año solo para:
   - resumen_por_empresa  
   - primas_netas_por_empresa  
   - cuadro_resultados  
   - seguro_en_cifras (cuadros descargables)  
2. Validar en staged (conteos, totales, duplicados) antes de generar clean.  
3. Generar `clean/{YYYY}/primas_YYYY.parquet` desde staged.  
4. Cargar a Supabase desde clean (reutilizando entity resolution y upsert actuales).

**Fase 3 — Loaders y tablas adicionales**  
1. Loader específico para **Margen de solvencia** → tabla `margen_solvencia`.  
2. Decidir si índices, saldo de operaciones y series históricas van a tablas propias o se dejan fuera del ETL inicial; si se incorporan, definir esquema y loader por tipo.  
3. Si se usa **audit** (Opción C): ejecutar `audit_local_pipeline.py` y luego alimentar mirror o clean desde by_source para trazabilidad.

### 4.3 Orden de ejecución recomendado (resumen)

1. **Verificar raw:** `python scripts/verificar_estructura_carpetas.py`  
2. **Probar ETL un año:** `python scripts/run_etl_to_supabase.py --year 2023 --debug`  
3. **Revisar Supabase:** `python scripts/consulta_supabase.py`  
4. (Opcional) **Normalizar raw:** mover xlsx desde raw/pdf a raw/xlsx; renombrar archivos sin año si se desea filtrar por año.  
5. (Fase 2) **Implementar staged → clean** para los 4 tipos principales y cargar desde clean.  
6. (Fase 3) **Loader margen_solvencia** y, si aplica, índices/series y/o audit.

---

## 5. Conclusión

- Los **archivos crudos** son coherentes con las tres opciones (A/B/C): hay suficiente volumen y variedad para directo, staged+clean o audit-first.  
- Las **incoherencias** importantes son: (1) archivos sin año en el nombre que se excluyen con filtro de año, (2) falta de loader para margen de solvencia y para índices/saldo/series si se quieren en BD.  
- **Propuesta:** estructura de carpetas actual (raw → staged → clean → processed; audit opcional), con **proceso en 3 fases**: Fase 1 ETL directo por año, Fase 2 staged + clean para los 4 tipos principales, Fase 3 loaders y tablas adicionales (margen, etc.) y opcionalmente audit para trazabilidad.
