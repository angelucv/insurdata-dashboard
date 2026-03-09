# Propuesta de reorganización (Opción 2): tablas temáticas del anuario

Antes de ejecutar nada: este documento define cómo se reagrupan los **100 CSV** en **tablas temáticas**, manteniendo siempre los CSV como fuente de verdad y permitiendo cargar **año a año** en la misma base.

---

## 1. Principios

- **Los 100 CSV en `data/staged/{año}/verificadas/` no se tocan:** siguen siendo la fuente de verdad. La reorganización es solo en la base de datos (SQLite local y/o Supabase).
- **Carga año a año:** cada tabla temática tiene columna **`anio`**. Se carga 2023 primero; luego 2024, 2025, etc., en las mismas tablas sin cambiar esquema.
- **Trazabilidad:** en cada tabla temática hay **`cuadro_id`** (ej. `"3"`, `"5-A"`, `"24"`). Si un cuadro tiene varios archivos (ej. 5A = 2 CSV), se usa **`origen_archivo`** (nombre del CSV) para distinguir.
- **Schema:** schema PostgreSQL **`anuario`** (o el que se use). Todas las tablas temáticas viven ahí.

---

## 2. Resumen: de 100 CSV a N tablas temáticas

Se proponen **23 tablas temáticas**. Cada una agrupa uno o varios cuadros (y sus archivos) que comparten el mismo “tipo” de dato.

| # | Tabla temática | Cuadros (IDs) | Archivos (aprox.) | Descripción breve |
|---|----------------|---------------|-------------------|-------------------|
| 1 | `primas_por_ramo` | 3, 5-A, 5-B, 5-C | 8 | Primas por ramo (agregado y desglose personas/patrimoniales/obligacionales). |
| 2 | `primas_por_ramo_empresa` | 4 | 1 | Primas por empresa y ramo. |
| 3 | `siniestros_por_ramo` | 6, 7, 8-A, 8-B, 8-C | 9 | Siniestros por ramo y por empresa. |
| 4 | `reservas_tecnicas_agregado` | 9 | 1 | Reservas técnicas (concepto, monto, tipo). |
| 5 | `reservas_prima_por_ramo` | 10 | 1 | Reservas de prima por ramo. |
| 6 | `reservas_prima_por_empresa` | 11, 12, 13, 14 | 4 | Reservas de prima por empresa (personas, patrimoniales, obligacionales). |
| 7 | `reservas_prestaciones_por_ramo` | 15 | 1 | Reservas prestaciones/siniestros por ramo. |
| 8 | `reservas_prestaciones_por_empresa` | 16, 17, 18, 19 | 4 | Reservas prestaciones por empresa. |
| 9 | `reservas_detalle_por_ramo_empresa` | 20-A … 20-F | 14 | Reservas prima y prestaciones por ramo/empresa (varias páginas por tipo). |
| 10 | `inversiones_reservas_tecnicas` | 21 | 1 | Inversiones aptas para reservas técnicas. |
| 11 | `gastos_vs_primas` | 22, 23, 23-A … 23-F | 14 | Gastos administración/producción y comisiones por ramo/empresa. |
| 12 | `balances_condensados` | 24, 40, 47, 54 | 4 | Balance condensado (seguro directo, reaseguros, financiadoras, medicina prepagada). |
| 13 | `estados_ingresos_egresos` | 25-A, 25-B, 41-A, 41-B, 48, 55-A, 55-B | 7 | Estado de ganancias y pérdidas (ingresos/egresos) por sector. |
| 14 | `gestion_general` | 26 | 1 | Gestión general (concepto, monto). |
| 15 | `datos_por_empresa` | 27, 28, 34, 35, 36, 49, 50, 51, 56, 57 | 11 | Rentabilidad, resultados, primas brutas, ingresos/circulante/gastos, medicina prepagada. |
| 16 | `indicadores_financieros_empresa` | 29, 44, 52, 58 | 4 | Indicadores financieros por empresa (seguro directo, reaseguros, financiadoras, medicina prepagada). |
| 17 | `suficiencia_patrimonio` | 30, 45 | 2 | Suficiencia patrimonio vs margen solvencia (cortes 30/06). |
| 18 | `series_historicas_primas` | 31-A, 31-B | 2 | Primas netas 2023 vs 2022; series largas primas/siniestros. |
| 19 | `reservas_hospitalizacion` | 32, 33 | 2 | Reservas prima/siniestros hospitalización individual y colectivo. |
| 20 | `cantidad_polizas_siniestros` | 37, 38 | 2 | Cantidad de pólizas y siniestros por ramo y por empresa. |
| 21 | `listados_empresas` | 39, 46, 53 | 3 | Listados de empresas (reaseguro, financiadoras, medicina prepagada). |
| 22 | `balance_por_empresa_reaseguros` | 42 | 1 | Balance condensado por empresa (columnas = empresas). Requiere pivot. |
| 23 | `ingresos_egresos_por_empresa_reaseguros` | 43-A, 43-B | 2 | Ingresos y egresos por empresa (reaseguros). |

Total: **23 tablas temáticas** que consumen los **100 CSV**. Algunas tablas tienen estructuras fijas (concepto, monto, tipo); otras tienen “empresa + columnas variables” y pueden usar columnas fijas donde coincidan o un campo **`datos` JSONB** para lo que cambie por cuadro.

---

## 3. Mapeo completo: 100 CSV → tabla temática

Cada fila es un archivo CSV. **cuadro_id** identifica el cuadro del anuario; **origen_archivo** es el nombre del CSV (para cuadros con varios archivos).

| # | origen_archivo (CSV) | cuadro_id | Tabla temática |
|---|----------------------|-----------|-----------------|
| 1 | cuadro_03_primas_por_ramo.csv | 3 | primas_por_ramo |
| 2 | cuadro_04_primas_por_ramo_empresa.csv | 4 | primas_por_ramo_empresa |
| 3 | cuadro_05A_pag20_5_ramos.csv | 5-A | primas_por_ramo |
| 4 | cuadro_05A_pag21_4_ramos_total.csv | 5-A | primas_por_ramo |
| 5 | cuadro_05B_pag22_5_ramos.csv | 5-B | primas_por_ramo |
| 6 | cuadro_05B_pag23_6_ramos.csv | 5-B | primas_por_ramo |
| 7 | cuadro_05B_pag24_5_ramos_total.csv | 5-B | primas_por_ramo |
| 8 | cuadro_05C_pag25_5_ramos.csv | 5-C | primas_por_ramo |
| 9 | cuadro_05C_pag26_3_ramos_total.csv | 5-C | primas_por_ramo |
| 10 | cuadro_06_siniestros_pagados_por_ramo.csv | 6 | siniestros_por_ramo |
| 11 | cuadro_07_siniestros_por_ramo_empresa.csv | 7 | siniestros_por_ramo |
| 12 | cuadro_08A_pag29_5_ramos.csv | 8-A | siniestros_por_ramo |
| 13 | cuadro_08A_pag30_5_ramos_total.csv | 8-A | siniestros_por_ramo |
| 14 | cuadro_08B_pag31_5_ramos.csv | 8-B | siniestros_por_ramo |
| 15 | cuadro_08B_pag32_6_ramos.csv | 8-B | siniestros_por_ramo |
| 16 | cuadro_08B_pag33_5_ramos_total.csv | 8-B | siniestros_por_ramo |
| 17 | cuadro_08C_pag34_5_ramos.csv | 8-C | siniestros_por_ramo |
| 18 | cuadro_08C_pag35_3_ramos_total.csv | 8-C | siniestros_por_ramo |
| 19 | cuadro_09_reservas_tecnicas.csv | 9 | reservas_tecnicas_agregado |
| 20 | cuadro_10_reservas_prima_por_ramo.csv | 10 | reservas_prima_por_ramo |
| 21 | cuadro_11_reservas_prima_por_empresa.csv | 11 | reservas_prima_por_empresa |
| 22 | cuadro_12_reservas_prima_personas_por_empresa.csv | 12 | reservas_prima_por_empresa |
| 23 | cuadro_13_reservas_prima_patrimoniales_por_empresa.csv | 13 | reservas_prima_por_empresa |
| 24 | cuadro_14_reservas_prima_obligacionales_por_empresa.csv | 14 | reservas_prima_por_empresa |
| 25 | cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv | 15 | reservas_prestaciones_por_ramo |
| 26 | cuadro_16_reservas_prestaciones_siniestros_por_empresa.csv | 16 | reservas_prestaciones_por_empresa |
| 27 | cuadro_17_reservas_prestaciones_siniestros_personas_por_empresa.csv | 17 | reservas_prestaciones_por_empresa |
| 28 | cuadro_18_reservas_prestaciones_siniestros_patrimoniales_por_empresa.csv | 18 | reservas_prestaciones_por_empresa |
| 29 | cuadro_19_reservas_prestaciones_siniestros_obligacionales_por_empresa.csv | 19 | reservas_prestaciones_por_empresa |
| 30 | cuadro_20A_pag47_5_ramos.csv | 20-A | reservas_detalle_por_ramo_empresa |
| 31 | cuadro_20A_pag48_4_ramos_total.csv | 20-A | reservas_detalle_por_ramo_empresa |
| 32 | cuadro_20B_pag49_6_ramos.csv | 20-B | reservas_detalle_por_ramo_empresa |
| 33 | cuadro_20B_pag50_6_ramos.csv | 20-B | reservas_detalle_por_ramo_empresa |
| 34 | cuadro_20B_pag51_4_ramos_total.csv | 20-B | reservas_detalle_por_ramo_empresa |
| 35 | cuadro_20C_pag52_5_ramos.csv | 20-C | reservas_detalle_por_ramo_empresa |
| 36 | cuadro_20C_pag53_3_ramos_total.csv | 20-C | reservas_detalle_por_ramo_empresa |
| 37 | cuadro_20D_pag54_5_ramos.csv | 20-D | reservas_detalle_por_ramo_empresa |
| 38 | cuadro_20D_pag55_4_ramos_total.csv | 20-D | reservas_detalle_por_ramo_empresa |
| 39 | cuadro_20E_pag56_6_ramos.csv | 20-E | reservas_detalle_por_ramo_empresa |
| 40 | cuadro_20E_pag57_6_ramos.csv | 20-E | reservas_detalle_por_ramo_empresa |
| 41 | cuadro_20E_pag58_4_ramos_total.csv | 20-E | reservas_detalle_por_ramo_empresa |
| 42 | cuadro_20F_pag59_5_ramos.csv | 20-F | reservas_detalle_por_ramo_empresa |
| 43 | cuadro_20F_pag60_3_ramos_total.csv | 20-F | reservas_detalle_por_ramo_empresa |
| 44 | cuadro_21_inversiones_reservas_tecnicas.csv | 21 | inversiones_reservas_tecnicas |
| 45 | cuadro_22_gastos_admin_vs_primas_por_empresa.csv | 22 | gastos_vs_primas |
| 46 | cuadro_23_gastos_produccion_vs_primas_por_ramo.csv | 23 | gastos_vs_primas |
| 47 | cuadro_23A_pag64_comisiones_5_ramos.csv | 23-A | gastos_vs_primas |
| 48 | cuadro_23A_pag65_comisiones_4_ramos_total.csv | 23-A | gastos_vs_primas |
| 49 | cuadro_23B_pag66_comisiones_6_ramos.csv | 23-B | gastos_vs_primas |
| 50 | cuadro_23B_pag67_comisiones_6_ramos.csv | 23-B | gastos_vs_primas |
| 51 | cuadro_23B_pag68_comisiones_4_ramos_total.csv | 23-B | gastos_vs_primas |
| 52 | cuadro_23C_pag69_comisiones_5_ramos.csv | 23-C | gastos_vs_primas |
| 53 | cuadro_23C_pag70_comisiones_3_ramos_total.csv | 23-C | gastos_vs_primas |
| 54 | cuadro_23D_pag71_gastos_adm_5_ramos.csv | 23-D | gastos_vs_primas |
| 55 | cuadro_23D_pag72_gastos_adm_4_ramos_total.csv | 23-D | gastos_vs_primas |
| 56 | cuadro_23E_pag73_gastos_adm_6_ramos.csv | 23-E | gastos_vs_primas |
| 57 | cuadro_23E_pag74_gastos_adm_6_ramos.csv | 23-E | gastos_vs_primas |
| 58 | cuadro_23E_pag75_gastos_adm_4_ramos_total.csv | 23-E | gastos_vs_primas |
| 59 | cuadro_23F_pag76_gastos_adm_5_ramos.csv | 23-F | gastos_vs_primas |
| 60 | cuadro_23F_pag77_gastos_adm_3_ramos_total.csv | 23-F | gastos_vs_primas |
| 61 | cuadro_24_balance_condensado.csv | 24 | balances_condensados |
| 62 | cuadro_25A_estado_ganancias_perdidas_ingresos.csv | 25-A | estados_ingresos_egresos |
| 63 | cuadro_25B_estado_ganancias_perdidas_egresos.csv | 25-B | estados_ingresos_egresos |
| 64 | cuadro_26_gestion_general.csv | 26 | gestion_general |
| 65 | cuadro_27_rentabilidad_inversiones_por_empresa.csv | 27 | datos_por_empresa |
| 66 | cuadro_28_resultados_ejercicio_2019_2023_por_empresa.csv | 28 | datos_por_empresa |
| 67 | cuadro_29_indicadores_financieros_2023_por_empresa.csv | 29 | indicadores_financieros_empresa |
| 68 | cuadro_30_suficiencia_patrimonio_solvencia_2022_2023.csv | 30 | suficiencia_patrimonio |
| 69 | cuadro_31A_primas_netas_cobradas_2023_vs_2022.csv | 31-A | series_historicas_primas |
| 70 | cuadro_31B_primas_prestaciones_siniestros_1990_2023.csv | 31-B | series_historicas_primas |
| 71 | cuadro_32_reservas_prima_siniestros_hospitalizacion_individual.csv | 32 | reservas_hospitalizacion |
| 72 | cuadro_33_reservas_prima_siniestros_hospitalizacion_colectivo.csv | 33 | reservas_hospitalizacion |
| 73 | cuadro_34_primas_brutas_personas_generales_por_empresa.csv | 34 | datos_por_empresa |
| 74 | cuadro_35_devolucion_primas_personas_generales_por_empresa.csv | 35 | datos_por_empresa |
| 75 | cuadro_36_reservas_prestaciones_siniestros_pendientes_ocurridos_no_notificados.csv | 36 | datos_por_empresa |
| 76 | cuadro_37_cantidad_polizas_siniestros_por_ramo.csv | 37 | cantidad_polizas_siniestros |
| 77 | cuadro_38_cantidad_polizas_siniestros_por_empresa.csv | 38 | cantidad_polizas_siniestros |
| 78 | cuadro_39_empresas_reaseguro_autorizadas.csv | 39 | listados_empresas |
| 79 | cuadro_40_balance_condensado_reaseguros.csv | 40 | balances_condensados |
| 80 | cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros.csv | 41-A | estados_ingresos_egresos |
| 81 | cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros.csv | 41-B | estados_ingresos_egresos |
| 82 | cuadro_42_balance_condensado_por_empresa_reaseguros.csv | 42 | balance_por_empresa_reaseguros |
| 83 | cuadro_43A_estado_ganancias_perdidas_ingresos_por_empresa_reaseguros.csv | 43-A | ingresos_egresos_por_empresa_reaseguros |
| 84 | cuadro_43B_estado_ganancias_perdidas_egresos_por_empresa_reaseguros.csv | 43-B | ingresos_egresos_por_empresa_reaseguros |
| 85 | cuadro_44_indicadores_financieros_2023_reaseguros.csv | 44 | indicadores_financieros_empresa |
| 86 | cuadro_45_suficiencia_patrimonio_solvencia_reaseguros_2022_2023.csv | 45 | suficiencia_patrimonio |
| 87 | cuadro_46_empresas_financiadoras_primas_autorizadas.csv | 46 | listados_empresas |
| 88 | cuadro_47_balance_condensado_financiadoras_primas.csv | 47 | balances_condensados |
| 89 | cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas.csv | 48 | estados_ingresos_egresos |
| 90 | cuadro_49_ingresos_por_empresa_financiadoras_primas.csv | 49 | datos_por_empresa |
| 91 | cuadro_50_circulante_activo_por_empresa_financiadoras_primas.csv | 50 | datos_por_empresa |
| 92 | cuadro_51_gastos_operativos_administrativos_financieros_por_empresa_financiadoras_primas.csv | 51 | datos_por_empresa |
| 93 | cuadro_52_indicadores_financieros_2023_financiadoras_primas.csv | 52 | indicadores_financieros_empresa |
| 94 | cuadro_53_empresas_medicina_prepagada_autorizadas.csv | 53 | listados_empresas |
| 95 | cuadro_54_balance_condensado_medicina_prepagada.csv | 54 | balances_condensados |
| 96 | cuadro_55A_estado_ganancias_perdidas_ingresos_medicina_prepagada.csv | 55-A | estados_ingresos_egresos |
| 97 | cuadro_55B_estado_ganancias_perdidas_egresos_medicina_prepagada.csv | 55-B | estados_ingresos_egresos |
| 98 | cuadro_56_ingresos_netos_por_empresa_medicina_prepagada.csv | 56 | datos_por_empresa |
| 99 | cuadro_57_reservas_tecnicas_por_empresa_medicina_prepagada.csv | 57 | datos_por_empresa |
| 100 | cuadro_58_indicadores_financieros_2023_medicina_prepagada.csv | 58 | indicadores_financieros_empresa |

---

## 4. Esquema sugerido por tabla temática

Todas incluyen **`anio`** (y donde aplica **`cuadro_id`**, **`origen_archivo`**). Para columnas que cambian mucho entre cuadros se puede usar **`datos JSONB`** (PostgreSQL) o una tabla “cruda” por cuadro hasta unificar.

### 4.1 Estructura fija (concepto / monto / tipo)

- **reservas_tecnicas_agregado**: `anio`, `cuadro_id`, `concepto`, `monto`, `tipo` (nullable si el CSV no tiene tipo).
- **balances_condensados**: `anio`, `cuadro_id`, `concepto`, `monto`, `tipo` (nullable para C24 que solo tiene concepto y monto).
- **estados_ingresos_egresos**: `anio`, `cuadro_id`, `concepto`, `monto`, `tipo`.
- **gestion_general**: `anio`, `cuadro_id`, `concepto`, `monto`.
- **inversiones_reservas_tecnicas**: `anio`, `cuadro_id`, `concepto`, `monto` (y opcional `tipo` si el CSV lo trae).

### 4.2 Por ramo (primas / siniestros / reservas / gastos)

- **primas_por_ramo**: `anio`, `cuadro_id`, `origen_archivo`, `concepto_ramo`, `seguro_directo`, `reaseguro_aceptado`, `total`, `pct` (y columnas extra en `datos` JSONB si algún archivo trae más).
- **siniestros_por_ramo**: igual idea; puede unificarse con primas en una tabla “por_ramo” con `tipo_serie` (primas/siniestros) si se prefiere.
- **reservas_prima_por_ramo**, **reservas_prestaciones_por_ramo**: `anio`, `cuadro_id`, `concepto_ramo`, columnas numéricas o `datos` JSONB.
- **reservas_detalle_por_ramo_empresa**: `anio`, `cuadro_id`, `origen_archivo`, `fila_orden`, `datos` JSONB (o columnas fijas si se homogeniza).
- **gastos_vs_primas**: `anio`, `cuadro_id`, `origen_archivo`, `concepto_ramo_o_empresa`, `datos` JSONB (o columnas según subtipo).
- **cantidad_polizas_siniestros**: `anio`, `cuadro_id`, `concepto_ramo_o_empresa`, `polizas`, `siniestros` (y columnas extra si hay).

### 4.3 Por empresa

- **primas_por_ramo_empresa**: `anio`, `cuadro_id`, `nombre_empresa`, `datos` JSONB (columnas por ramo/porcentajes).
- **reservas_prima_por_empresa**, **reservas_prestaciones_por_empresa**: `anio`, `cuadro_id`, `nombre_empresa`, columnas numéricas o `datos` JSONB.
- **datos_por_empresa**: `anio`, `cuadro_id`, `nombre_empresa`, `datos` JSONB. Aquí caen 27, 28, 34, 35, 36, 49, 50, 51, 56, 57 (columnas distintas por cuadro).
- **indicadores_financieros_empresa**: `anio`, `cuadro_id`, `nombre_empresa`, `col1` … `col6` (o nombres semánticos cuando estén fijos) para no usar JSONB si las columnas son estables.
- **suficiencia_patrimonio**: `anio`, `cuadro_id`, `nombre_empresa`, columnas por corte (margen, patrimonio_no_comprometido, pct_suficiencia).
- **ingresos_egresos_por_empresa_reaseguros**: `anio`, `cuadro_id`, `nombre_empresa`, columnas de montos o `datos` JSONB.

### 4.4 Listados y tablas especiales

- **listados_empresas**: `anio`, `cuadro_id`, `numero_orden`, `nombre_empresa` (y columnas extra si algún listado trae más).
- **balance_por_empresa_reaseguros**: normalizado a filas: `anio`, `cuadro_id`, `concepto`, `nombre_empresa`, `monto` (pivot al cargar desde el CSV que tiene empresas en columnas).
- **series_historicas_primas**: 31-A = por empresa (nombre_empresa, año_2023, año_2022); 31-B = por año (año, primas, prestaciones_siniestros). Pueden ser dos tablas o una con `tipo_serie` y `datos` JSONB.

---

## 5. Carga año a año y ETL

- **Origen:** siempre `data/staged/{año}/verificadas/`. Un año = una carpeta con hasta 100 CSV (según lo que publique el anuario ese año).
- **Proceso:** para cada año (ej. 2023, luego 2024):
  1. Leer cada CSV de esa carpeta.
  2. Según el mapeo (sección 3), insertar en la tabla temática que corresponda.
  3. Rellenar `anio`, `cuadro_id`, `origen_archivo` (si aplica).
  4. Para cuadro 42: transformar columnas (empresas) a filas (concepto, empresa, monto) antes de insertar.
- **Idempotencia:** para ese `anio`, antes de cargar se puede hacer `DELETE FROM … WHERE anio = ?` en cada tabla temática, o usar upsert si se define clave única (anio, cuadro_id, origen_archivo, fila_orden o equivalente).

---

## 6. Resumen ejecutivo

- **100 CSV** se mantienen como fuente de verdad en `staged/{año}/verificadas/`.
- Se cargan en **23 tablas temáticas** bajo el schema **anuario**, con **anio** y **cuadro_id** (y **origen_archivo** cuando un cuadro tiene varios archivos).
- Se puede **ir compilando año a año** en la misma base; no hace falta cambiar esquema al sumar 2024, 2025, etc.
- Donde las columnas son muy distintas entre cuadros se usa **`datos` JSONB** o columnas genéricas; donde son estables (balances, estados de resultado, listados) se usan columnas fijas.

Si esta propuesta te cierra, el siguiente paso sería: (1) definir el DDL exacto de las 23 tablas (y si usamos JSONB en alguna), y (2) implementar el ETL que lea los CSV y llene estas tablas sin tocar los archivos originales.
