# Estructura de la base de datos del anuario "Seguro en Cifras"

Documento de referencia: cómo queda organizada la base de datos (local SQLite y schema PostgreSQL para Supabase) **sin ejecutar** ningún script. Si ya corriste `load_anuario_to_local_db.py --year 2023`, lo que tienes coincide con esta estructura.

---

## 1. Ubicación y carpetas

```
data/
├── staged/2023/verificadas/     ← 100 CSV (fuente de verdad; no se mueven)
│
└── db/
    ├── local/
    │   ├── anuario.db           ← SQLite: 100 tablas, una por cuadro
    │   └── manifest_carga.json  ← Fecha de carga, archivos, filas por tabla
    │
    └── schema/
        └── 001_schema_anuario.sql  ← DDL PostgreSQL (schema anuario) para Supabase
```

- **SQLite** (`data/db/local/anuario.db`): misma estructura que se puede replicar en Supabase.
- **PostgreSQL** (`data/db/schema/`): solo incluye de ejemplo 2 tablas; el resto sigue el mismo patrón.

---

## 2. Reglas de la estructura

- **Una tabla por archivo CSV:** nombre de tabla = nombre del archivo sin `.csv` (ej. `cuadro_03_primas_por_ramo`).
- **Columna `anio`:** en todas las tablas, primera columna, `INTEGER NOT NULL` (ej. 2023). Permite tener varios años en la misma tabla.
- **Demás columnas:** una por columna del CSV, normalizadas para SQL:
  - Espacios → `_`
  - `%` → `pct`
  - Caracteres no alfanuméricos (excepto `_`) → `_`
  - Nombres duplicados reciben sufijo `_2`, `_3`, etc.
- **Tipos en SQLite:** todas las columnas de datos como `TEXT` (los números se guardan como texto y se pueden castear en consultas).
- **Índice:** en cada tabla, índice sobre `anio` para filtrar por año.

---

## 3. Listado de las 100 tablas (SQLite / futuro PostgreSQL)

Cada fila = una tabla. Orden = orden del índice del anuario (cuadros 3 a 58).

| # | Tabla | Filas (2023) |
|---|-------|--------------|
| 1 | cuadro_03_primas_por_ramo | 37 |
| 2 | cuadro_04_primas_por_ramo_empresa | 51 |
| 3 | cuadro_05A_pag20_5_ramos | 51 |
| 4 | cuadro_05A_pag21_4_ramos_total | 51 |
| 5 | cuadro_05B_pag22_5_ramos | 51 |
| 6 | cuadro_05B_pag23_6_ramos | 51 |
| 7 | cuadro_05B_pag24_5_ramos_total | 51 |
| 8 | cuadro_05C_pag25_5_ramos | 51 |
| 9 | cuadro_05C_pag26_3_ramos_total | 51 |
| 10 | cuadro_06_siniestros_pagados_por_ramo | 38 |
| 11 | cuadro_07_siniestros_por_ramo_empresa | 52 |
| 12 | cuadro_08A_pag29_5_ramos | 50 |
| 13 | cuadro_08A_pag30_5_ramos_total | 50 |
| 14 | cuadro_08B_pag31_5_ramos | 51 |
| 15 | cuadro_08B_pag32_6_ramos | 51 |
| 16 | cuadro_08B_pag33_5_ramos_total | 51 |
| 17 | cuadro_08C_pag34_5_ramos | 51 |
| 18 | cuadro_08C_pag35_3_ramos_total | 51 |
| 19 | cuadro_09_reservas_tecnicas | 28 |
| 20 | cuadro_10_reservas_prima_por_ramo | 37 |
| 21 | cuadro_11_reservas_prima_por_empresa | 52 |
| 22 | cuadro_12_reservas_prima_personas_por_empresa | 52 |
| 23 | cuadro_13_reservas_prima_patrimoniales_por_empresa | 52 |
| 24 | cuadro_14_reservas_prima_obligacionales_por_empresa | 52 |
| 25 | cuadro_15_reservas_prestaciones_siniestros_por_ramo | 37 |
| 26 | cuadro_16_reservas_prestaciones_siniestros_por_empresa | 52 |
| 27 | cuadro_17_reservas_prestaciones_siniestros_personas_por_empresa | 52 |
| 28 | cuadro_18_reservas_prestaciones_siniestros_patrimoniales_por_empresa | 52 |
| 29 | cuadro_19_reservas_prestaciones_siniestros_obligacionales_por_empresa | 52 |
| 30 | cuadro_20A_pag47_5_ramos | 51 |
| 31 | cuadro_20A_pag48_4_ramos_total | 51 |
| 32 | cuadro_20B_pag49_6_ramos | 51 |
| 33 | cuadro_20B_pag50_6_ramos | 51 |
| 34 | cuadro_20B_pag51_4_ramos_total | 51 |
| 35 | cuadro_20C_pag52_5_ramos | 51 |
| 36 | cuadro_20C_pag53_3_ramos_total | 51 |
| 37 | cuadro_20D_pag54_5_ramos | 51 |
| 38 | cuadro_20D_pag55_4_ramos_total | 51 |
| 39 | cuadro_20E_pag56_6_ramos | 51 |
| 40 | cuadro_20E_pag57_6_ramos | 51 |
| 41 | cuadro_20E_pag58_4_ramos_total | 51 |
| 42 | cuadro_20F_pag59_5_ramos | 51 |
| 43 | cuadro_20F_pag60_3_ramos_total | 51 |
| 44 | cuadro_21_inversiones_reservas_tecnicas | 18 |
| 45 | cuadro_22_gastos_admin_vs_primas_por_empresa | 47 |
| 46 | cuadro_23_gastos_produccion_vs_primas_por_ramo | 38 |
| 47 | cuadro_23A_pag64_comisiones_5_ramos | 50 |
| 48 | cuadro_23A_pag65_comisiones_4_ramos_total | 50 |
| 49 | cuadro_23B_pag66_comisiones_6_ramos | 50 |
| 50 | cuadro_23B_pag67_comisiones_6_ramos | 50 |
| 51 | cuadro_23B_pag68_comisiones_4_ramos_total | 50 |
| 52 | cuadro_23C_pag69_comisiones_5_ramos | 50 |
| 53 | cuadro_23C_pag70_comisiones_3_ramos_total | 50 |
| 54 | cuadro_23D_pag71_gastos_adm_5_ramos | 51 |
| 55 | cuadro_23D_pag72_gastos_adm_4_ramos_total | 51 |
| 56 | cuadro_23E_pag73_gastos_adm_6_ramos | 51 |
| 57 | cuadro_23E_pag74_gastos_adm_6_ramos | 51 |
| 58 | cuadro_23E_pag75_gastos_adm_4_ramos_total | 51 |
| 59 | cuadro_23F_pag76_gastos_adm_5_ramos | 51 |
| 60 | cuadro_23F_pag77_gastos_adm_3_ramos_total | 51 |
| 61 | cuadro_24_balance_condensado | 35 |
| 62 | cuadro_25A_estado_ganancias_perdidas_ingresos | 39 |
| 63 | cuadro_25B_estado_ganancias_perdidas_egresos | 52 |
| 64 | cuadro_26_gestion_general | 41 |
| 65 | cuadro_27_rentabilidad_inversiones_por_empresa | 51 |
| 66 | cuadro_28_resultados_ejercicio_2019_2023_por_empresa | 54 |
| 67 | cuadro_29_indicadores_financieros_2023_por_empresa | 47 |
| 68 | cuadro_30_suficiencia_patrimonio_solvencia_2022_2023 | 51 |
| 69 | cuadro_31A_primas_netas_cobradas_2023_vs_2022 | 52 |
| 70 | cuadro_31B_primas_prestaciones_siniestros_1990_2023 | 34 |
| 71 | cuadro_32_reservas_prima_siniestros_hospitalizacion_individual | 52 |
| 72 | cuadro_33_reservas_prima_siniestros_hospitalizacion_colectivo | 52 |
| 73 | cuadro_34_primas_brutas_personas_generales_por_empresa | 52 |
| 74 | cuadro_35_devolucion_primas_personas_generales_por_empresa | 52 |
| 75 | cuadro_36_reservas_prestaciones_siniestros_pendientes_ocurridos_no_notificados | 52 |
| 76 | cuadro_37_cantidad_polizas_siniestros_por_ramo | 41 |
| 77 | cuadro_38_cantidad_polizas_siniestros_por_empresa | 52 |
| 78 | cuadro_39_empresas_reaseguro_autorizadas | 5 |
| 79 | cuadro_40_balance_condensado_reaseguros | 33 |
| 80 | cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros | 36 |
| 81 | cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros | 37 |
| 82 | cuadro_42_balance_condensado_por_empresa_reaseguros | 29 |
| 83 | cuadro_43A_estado_ganancias_perdidas_ingresos_por_empresa_reaseguros | 36 |
| 84 | cuadro_43B_estado_ganancias_perdidas_egresos_por_empresa_reaseguros | 35 |
| 85 | cuadro_44_indicadores_financieros_2023_reaseguros | 5 |
| 86 | cuadro_45_suficiencia_patrimonio_solvencia_reaseguros_2022_2023 | 4 |
| 87 | cuadro_46_empresas_financiadoras_primas_autorizadas | 17 |
| 88 | cuadro_47_balance_condensado_financiadoras_primas | 34 |
| 89 | cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas | 21 |
| 90 | cuadro_49_ingresos_por_empresa_financiadoras_primas | 18 |
| 91 | cuadro_50_circulante_activo_por_empresa_financiadoras_primas | 18 |
| 92 | cuadro_51_gastos_operativos_administrativos_financieros_por_empresa_financiadoras_primas | 18 |
| 93 | cuadro_52_indicadores_financieros_2023_financiadoras_primas | 17 |
| 94 | cuadro_53_empresas_medicina_prepagada_autorizadas | 10 |
| 95 | cuadro_54_balance_condensado_medicina_prepagada | 35 |
| 96 | cuadro_55A_estado_ganancias_perdidas_ingresos_medicina_prepagada | 19 |
| 97 | cuadro_55B_estado_ganancias_perdidas_egresos_medicina_prepagada | 44 |
| 98 | cuadro_56_ingresos_netos_por_empresa_medicina_prepagada | 11 |
| 99 | cuadro_57_reservas_tecnicas_por_empresa_medicina_prepagada | 11 |
| 100 | cuadro_58_indicadores_financieros_2023_medicina_prepagada | 6 |

**Total filas (año 2023):** 4.240 en las 100 tablas.

---

## 4. Ejemplos de columnas por tabla

Las columnas son **anio** más las cabeceras del CSV normalizadas (espacios → `_`, `%` → `pct`). Algunos ejemplos:

**cuadro_03_primas_por_ramo** (Primas por ramo)  
- `anio`, `RAMO_DE_SEGUROS`, `SEGURO_DIRECTO`, `REASEGURO_ACEPTADO`, `TOTAL`, `pct`

**cuadro_24_balance_condensado** (Balance condensado)  
- `anio`, `CONCEPTO`, `MONTO`, `TIPO`

**cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas**  
- `anio`, `CONCEPTO`, `MONTO`, `TIPO`

**cuadro_54_balance_condensado_medicina_prepagada**  
- `anio`, `CONCEPTO`, `MONTO`, `TIPO`

**cuadro_57_reservas_tecnicas_por_empresa_medicina_prepagada**  
- `anio`, `NOMBRE_EMPRESA`, `RESERVAS_CUOTAS_EN_CURSO`, `RESERVAS_SERVICIOS_REEMBOLSOS_PENDIENTES`, `RESERVAS_SERVICIOS_NO_NOTIFICADOS`, `RESERVAS_RIESGOS_CATASTROFICOS`, `RESERVAS_REINTEGRO_EXPERIENCIA_FAVORABLE`, `CUOTAS_COBRADAS_ANTICIPADO`, `VALES_COBRADOS_ANTICIPADO`, `DEPOSITOS_CONTRATOS_EN_PROCESO`, `TOTAL_RESERVAS`

El resto de tablas siguen el mismo criterio: una columna por campo del CSV, con nombres válidos en SQL.

---

## 5. Schema PostgreSQL (Supabase)

En **`data/db/schema/001_schema_anuario.sql`** está:

- `CREATE SCHEMA anuario;`
- Dos tablas de ejemplo:
  - `anuario.cuadro_03_primas_por_ramo` (anio + ramo_de_seguros, seguro_directo, reaseguro_aceptado, total, pct)
  - `anuario.cuadro_54_balance_condensado_medicina_prepagada` (anio + concepto, monto, tipo)
- Índices sobre `anio` en esas tablas.

Para tener las 100 tablas en Supabase se puede:  
- repetir el mismo patrón (anio + columnas TEXT según cada CSV), o  
- extender el script de carga para que genere el DDL completo a partir de los CSV.

---

## 6. Cómo ver la estructura sin ejecutar carga

- **Listado de tablas y filas:**  
  `data/db/local/manifest_carga.json` (generado al correr `load_anuario_to_local_db.py`).

- **Esquema de una tabla en SQLite** (si ya existe `anuario.db`):  
  ```bash
  sqlite3 data/db/local/anuario.db ".schema cuadro_03_primas_por_ramo"
  ```

- **Script auxiliar** (solo lectura):  
  `python scripts/mostrar_estructura_anuario_db.py`  
  imprime todas las tablas y sus columnas leyendo `anuario.db`.

Resumen: **100 tablas**, una por cuadro del anuario, cada una con **anio** + columnas del CSV normalizadas; en local en **SQLite** y en Supabase bajo el **schema anuario** con el mismo diseño.
