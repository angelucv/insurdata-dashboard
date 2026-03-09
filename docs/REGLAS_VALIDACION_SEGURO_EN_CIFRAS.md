# Reglas de validación – Seguro en Cifras (Anuario)

Este documento consolida los criterios de **validación interna**, **validación entre tablas** y **escritura/lectura** de los datos extraídos del anuario "Seguro en Cifras". Sirve como guía para replicar el proceso tabla a tabla y **generalizar a otros años**.

**Año de referencia:** Las **páginas** y **ejemplos numéricos** (totales, fechas de corte) indicados en las tablas corresponden al anuario **2023**. Para otro año, las páginas deben tomarse del **índice del PDF** (págs. 4-6) y la misma lógica de validación y cruces aplica; los scripts aceptan el parámetro `--year`.

---

## 0. Verificación del índice y notas del anuario

- **Índice (páginas 4 a 6):** El PDF del anuario incluye un índice que lista cada cuadro y su página. Para comprobar que se han cubierto todas las tablas extraíbles y ubicar **por cada página qué cuadro corresponde**, ejecutar al inicio (o tras la extracción):
  ```bash
  python scripts/verificar_indice_anuario.py --year 2023
  ```
  Sustituir `2023` por el año deseado si se trabaja con otro anuario. El script comprueba que existan los CSV esperados para los cuadros 3 a 58 y muestra la **ubicación página → cuadro**. Los cuadros 1 y 2 (Empresas autorizadas, Capital y garantía) no se extraen en este proyecto.

- **Notas al final (páginas 137 a 139):** Las notas aclaran definiciones y fórmulas usadas en el anuario (primas netas cobradas, retención propia, fórmula de Hardy en Cuadro 27, e indicadores (1)-(6) de los Cuadros 29, 44, 52 y 58). Para el detalle de cada fórmula y su relación con los CSV y columnas extraídos, ver **`docs/NOTAS_ANUARIO_PAGS_137_139.md`**.

- **Consistencia reglas vs archivos generados:** Para comprobar que los 100 CSV esperados existen, que no hay archivos en disco sin cuadro en el índice y que los scripts de verificación referenciados existen: `python scripts/verificar_consistencia_reglas_archivos.py --year 2023`.

---

## 1. Objetivo y alcance

- **Alcance:** Este documento y las reglas que describe aplican **únicamente a los anuarios** "Seguro en Cifras" (PDF → CSV). Otras fuentes de información (por ejemplo Excel) tendrán sus propias reglas y documentación. Ver `docs/FUENTES_DE_DATOS.md`.
- **Fuente:** PDF del anuario (ej. Seguro en Cifras 2023).
- **Producto:** Tablas en CSV en `data/staged/{año}/verificadas/`, con criterios verificables.
- **Uso:** Auditar que lo extraído coincida con totales del documento y que las tablas enlazadas sean coherentes entre sí.

---

## 2. Convenciones de escritura y lectura

### 2.1 Formato CSV unificado

| Criterio | Regla |
|----------|--------|
| **Separador** | Punto y coma (`;`) en todo el archivo. |
| **Encoding** | UTF-8 con BOM (`utf-8-sig`) para compatibilidad con Excel. |
| **Primera línea** | Siempre nombres de campos (cabecera explícita). |
| **Campos de texto** | Entre comillas dobles cuando contengan coma o para homogeneizar (ej. `csv.QUOTE_NONNUMERIC`). |
| **Números** | Sin comillas; separador decimal según fuente (punto o coma); en script se normaliza a número. |

**Motivo del punto y coma:** Evitar conflicto con comas en nombres (ej. "Seguros, C.A.") y con coma como separador decimal en muchos contextos.

### 2.2 Lectura

- Leer con `sep=';'`, `encoding='utf-8-sig'`.
- Validar que todas las filas tengan el mismo número de columnas que la cabecera.
- Script de comprobación: `scripts/verificar_csv_verificadas.py`.

---

## 3. Reglas por cuadro (validación interna)

Cada cuadro tiene reglas propias que deben cumplirse con los datos extraídos (y, si aplica, con el documento).  
**Nota:** La columna «Página(s)» corresponde al anuario 2023; para otros años, consultar el índice del PDF (págs. 4-6).

| Cuadro | Página(s) | Descripción | Validación interna |
|--------|-----------|-------------|--------------------|
| **3** | 18 | Primas netas por ramo | Estructura: RAMO; SEGURO DIRECTO; REASEGURO ACEPTADO; TOTAL; %. Suma de ramos coherente con TOTAL documento. |
| **4** | 19 | Primas por ramo/empresa | Una fila por empresa. Suma de la columna TOTAL por fila = TOTAL del cuadro (valor del documento; ej. anuario 2023: 24.976.109). Mismo número de columnas en todas las filas. |
| **5-A** | 20, 21 | Primas Personas por empresa (9 ramos) | Pág 20: 5 ramos; pág 21: 4 ramos + TOTAL. Por empresa, suma de las 9 columnas = columna TOTAL. |
| **5-B** | 22, 23, 24 | Primas Patrimoniales por empresa (16 ramos) | 5 + 6 + 5 ramos (+ TOTAL). Suma por columna coherente por bloque. |
| **5-C** | 25, 26 | Primas Obligacionales por empresa (8 ramos) | 5 + 3 ramos (+ TOTAL). Suma por columna coherente por bloque. |
| **6** | 27 | Siniestros pagados por ramo | Misma estructura que Cuadro 3 (5 columnas). Tres subtotales (Personas, Patrimoniales, Obligacionales) suman al TOTAL. |
| **7** | 28 | Siniestros por ramo/empresa | Estructura tipo Cuadro 4. Suma por columna = total por ramo (cruzar con Cuadro 6). |
| **8-A** | 29, 30 | Siniestros Personas por empresa | 5 + 5 ramos (+ TOTAL). Suma por columna coherente. |
| **8-B** | 31, 32, 33 | Siniestros Patrimoniales por empresa | 16 ramos en 3 páginas. Suma por columna coherente. |
| **8-C** | 34, 35 | Siniestros Obligacionales por empresa | 8 ramos en 2 páginas. Suma por columna coherente. |
| **9** | 36 | Reservas técnicas por retención propia | CONCEPTO; MONTO; TIPO (SECCION/SUBDIVISION). Secciones en MAYÚSCULAS; **suma(subdivisiones) = total de la sección**. Suma de secciones = TOTAL. |
| **10** | 37 | Reservas de prima por ramo | RAMO; RETENCION_PROPIA; A_CARGO_REASEGURADORES; TOTAL. **Por línea: Retención + Reaseguro = Total**. Por sección (Personas, Patrimoniales, Responsabilidad), suma de subdivisiones = total de la sección. |
| **11** | 38 | Reservas de prima por empresa | EMPRESA; RETENCION_PROPIA; A_CARGO_REASEGURADORES; TOTAL. **Por línea: Retención + Reaseguro = Total**. Suma de todas las empresas = fila TOTAL (y debe coincidir con Cuadro 10). |
| **12** | 39 | Reservas de prima SEGUROS DE PERSONAS por empresa | Misma estructura que 11. Suma de todas las empresas = fila "SEGURO DE PERSONAS" del Cuadro 10 (Retención propia, A cargo reaseguradores, Total). |
| **13** | 40 | Reservas de prima SEGUROS PATRIMONIALES por empresa | Misma estructura que 11. Suma empresas = fila "SEGUROS PATRIMONIALES" del Cuadro 10. |
| **14** | 41 | Reservas de prima SEGUROS OBLIGACIONALES/RESPONSABILIDAD por empresa | Misma estructura que 11. Suma empresas = fila "SEGUROS DE RESPONSABILIDAD" del Cuadro 10. |
| **15** | 42 | Reservas para prestaciones y siniestros pendientes por ramo | RAMO; RETENCION_PROPIA; A_CARGO_REASEGURADORES; TOTAL. Total Retención = C9 "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES". Subtotal Personas = Vida + Individual de Personas + Colectivos de Personas + Funerarios (C9). Cruces por ramo/agrupación con C9. |
| **16** | 43 | Reservas prestaciones/siniestros pendientes por empresa | EMPRESA; RETENCION_PROPIA; A_CARGO_REASEGURADORES; TOTAL. Misma estructura que 11/15. **Suma de todas las empresas = fila TOTAL del Cuadro 15.** |
| **17** | 44 | Reservas prestaciones/siniestros pendientes SEGUROS DE PERSONAS por empresa | Misma estructura que 16. **Suma empresas = fila "SEGURO DE PERSONAS" del Cuadro 15.** |
| **18** | 45 | Reservas prestaciones/siniestros pendientes SEGUROS PATRIMONIALES por empresa | Misma estructura. **Suma empresas = fila "SEGUROS PATRIMONIALES" del Cuadro 15.** |
| **19** | 46 | Reservas prestaciones/siniestros pendientes SEGUROS OBLIGACIONALES/RESPONSABILIDAD por empresa | Misma estructura. **Suma empresas = fila "SEGUROS DE RESPONSABILIDAD" del Cuadro 15.** |
| **20-A** | 47, 48 | Reservas de prima por ramo/empresa SEGUROS DE PERSONAS (Retención propia) | Pág 47: 5 ramos (Accidentes Pers. Individual, Vida Individual, Desgravamen Hipotecario, Rentas Vitalicias, Vida Colectivo). Pág 48: 4 ramos + TOTAL (Accidentes Pers. Colectivo, Hospitalización Ind./Col., Seguros Funerarios, TOTAL). **Suma por columnas de los 9 ramos = Cuadro 12 col. Retención propia (o fila TOTAL C12).** |
| **20-B** | 49, 50, 51 | Reservas de prima por ramo/empresa SEGUROS PATRIMONIALES (Retención propia) | Pág 49: 6 ramos (Incendio, Terremoto, Robo, Transporte, Ramos Técnicos, Petroleros). Pág 50: 6 ramos (Combinados, Lucro cesante, Automóvil casco, Aeronaves, Naves, Agrícola). Pág 51: 4 ramos + TOTAL (Pecuario, Bancarios, Joyería, Diversos, TOTAL). **Suma por columnas de los 16 ramos = Cuadro 13 col. Retención propia (o fila TOTAL C13).** |
| **20-C** | 52, 53 | Reservas de prima por ramo/empresa SEGUROS OBLIGACIONALES Y/O DE RESPONSABILIDAD (Retención propia) | Pág 52: 5 ramos (R.C. Automóvil, R.C. Patronal, R.C. General, R.C. Profesional, Fianzas). Pág 53: 3 ramos + TOTAL (Fidelidad de Empleados, R.C. de Productos, Seguros de Crédito, TOTAL). **Suma por columnas de los 8 ramos = Cuadro 14 col. Retención propia (o fila TOTAL C14).** |
| **20-D** | 54, 55 | Reservas para prestaciones y siniestros pendientes por ramo/empresa SEGUROS DE PERSONAS | Pág 54: 5 ramos; pág 55: 4 ramos + TOTAL (misma estructura que 20-A). **Suma por columnas de los 9 ramos = Cuadro 17 (y fila SEGURO DE PERSONAS del Cuadro 15).** |
| **20-E** | 56, 57, 58 | Reservas prestaciones/siniestros pendientes por ramo/empresa SEGUROS PATRIMONIALES | Pág 56: 6 ramos; 57: 6 ramos; 58: 4 + TOTAL (misma estructura que 20-B). **Suma por columnas de los 16 ramos = Cuadro 18 (y fila SEGUROS PATRIMONIALES del Cuadro 15).** |
| **20-F** | 59, 60 | Reservas prestaciones/siniestros pendientes por ramo/empresa SEGUROS OBLIGACIONALES/RESPONSABILIDAD | Pág 59: 5 ramos; 60: 3 + TOTAL (misma estructura que 20-C). **Suma por columnas de los 8 ramos = Cuadro 19 (y fila SEGUROS DE RESPONSABILIDAD del Cuadro 15).** |
| **21** | 61 | Inversiones aptas para la representación de reservas técnicas | CONCEPTO; MONTO; PORCENTAJE; TIPO (SECCION/SUBDIVISION). Secciones: TOTAL, DISPONIBLE, VALORES PÚBLICOS, PREDIOS URBANOS EDIFICADOS, OTROS BIENES AUTORIZADOS. **Suma(subdivisiones) = total de la sección.** Suma de secciones (excl. fila TOTAL) = TOTAL. |
| **22** | 62 | Gastos de administración vs primas netas cobradas por empresa | NOMBRE_EMPRESA; PRIMAS_NETAS; GASTOS_ADMINISTRACION; PORCENTAJE. **Primas Netas (por empresa) = columna TOTAL del Cuadro 4 (misma empresa).** |
| **23** | 63 | Gastos de producción vs primas netas cobradas por ramo | RAMO_DE_SEGUROS; PRIMAS_NETAS; COMISIONES_GASTOS_ADQUISICION; PORC_COMISIONES; GASTOS_ADMINISTRACION; PORC_GASTOS_ADM. **PRIMAS_NETAS (por ramo) = columna SEGURO DIRECTO del Cuadro 3 (mismo ramo).** |
| **23-A** | 64, 65 | Comisiones y gastos de adquisición por ramo/empresa SEGURO DE PERSONAS | 5 ramos (pág 64) + 4 ramos + TOTAL (pág 65). **Suma total (col. TOTAL pág 65 o suma de ramos) = Cuadro 23 fila "SEGURO DE PERSONAS" col. COMISIONES_GASTOS_ADQUISICION.** |
| **23-B** | 66, 67, 68 | Comisiones y gastos de adquisición por ramo/empresa SEGUROS PATRIMONIALES | 5 + 6 + 5 ramos + TOTAL (3 págs). **Suma total = Cuadro 23 fila "SEGUROS PATRIMONIALES" col. COMISIONES_GASTOS_ADQUISICION.** |
| **23-C** | 69, 70 | Comisiones y gastos de adquisición por ramo/empresa SEGUROS OBLIGACIONALES | 5 ramos (pág 69) + 3 ramos + TOTAL (pág 70). **Suma total = Cuadro 23 fila "SEGUROS OBLIGACIONALES..." col. COMISIONES_GASTOS_ADQUISICION.** |
| **23-D** | 71, 72 | Gastos de administración por ramo/empresa SEGURO DE PERSONAS | 5 + 4 ramos + TOTAL (misma estructura que 23-A). **Suma total = Cuadro 23 fila "SEGURO DE PERSONAS" col. GASTOS_ADMINISTRACION.** |
| **23-E** | 73, 74, 75 | Gastos de administración por ramo/empresa SEGUROS PATRIMONIALES | Misma estructura que 23-B. **Suma total = Cuadro 23 fila "SEGUROS PATRIMONIALES" col. GASTOS_ADMINISTRACION.** |
| **23-F** | 76, 77 | Gastos de administración por ramo/empresa SEGUROS OBLIGACIONALES | Misma estructura que 23-C. **Suma total = Cuadro 23 fila "SEGUROS OBLIGACIONALES..." col. GASTOS_ADMINISTRACION.** |
| **24** | 78 | Balance condensado | CONCEPTO; MONTO. Secciones: ACTIVO (con total), pérdidas, TOTAL GENERAL, cuentas de orden; PASIVO (con total); CAPITAL (con total), superávit no realizado, TOTAL PASIVO+CAPITAL+SUPERÁVIT, utilidad, TOTAL GENERAL. **Validación interna:** los dos "TOTAL GENERAL" deben ser iguales (cuadre del balance). |
| **25-A** | 79 | Estado de Ganancias y Pérdidas - Ingresos | CONCEPTO; MONTO; TIPO (SECCION/LINEA/TOTAL_GLOBAL/RESULTADO). Secciones: Operaciones Seguros de Personas, Seguros Generales, Solidarios, Reaseguro Aceptado, Gestión General. **Validación interna:** suma(LINEA) por bloque = SECCION; suma(SECCION) = TOTAL INGRESOS; TOTAL INGRESOS + RESULTADO = TOTAL GENERAL. **Cruce:** Primas Aceptadas Seguros de Personas/Generales = Cuadro 3 REASEGURO ACEPTADO (Personas/Patrimoniales). Primas del Ejercicio vs C3 (pueden diferir por criterio contable). |
| **25-B** | 80, 81 | Estado de Ganancias y Pérdidas - Egresos | CONCEPTO; MONTO; TIPO. Secciones: Operaciones Seguros de Personas, Seguros Generales, Solidarios, Reaseguro Aceptado, Gestión General. **Validación interna:** suma(LINEA) por bloque = SECCION; suma(SECCION) = TOTAL EGRESOS; TOTAL EGRESOS + RESULTADO (utilidad) = TOTAL GENERAL. **Cruces:** Prestaciones+Siniestros Personas = C6 TOTAL Personas; Siniestros Generales = C6 Patr.+Oblig.; Comisiones y Gastos Adm (Personas/Generales) = C23 por segmento. |
| **26** | 82 | Gestión general | CONCEPTO; MONTO. Desglose ingresos (A–E) y totales. **Cruces:** PRODUCTO BRUTO TOTAL (A+B+C+D+E) = 25-A "GESTIÓN GENERAL DE LA EMPRESA"; TOTAL EGRESOS POR LA GESTIÓN GENERAL = 25-B "GESTIÓN GENERAL DE LA EMPRESA"; PRODUCTO NETO = PRODUCTO BRUTO − TOTAL EGRESOS. |
| **27** | 83 | Rentabilidad de las inversiones por empresa | NOMBRE_EMPRESA; MONTO_FONDO_2022; MONTO_FONDO_2023; PRODUCTO_INVERSIONES; RENTABILIDAD_PORC. **Cruce:** Suma de la columna Producto de Inversiones (I) por empresas = Cuadro 26 "A.PRODUCTO DE INVERSIONES". Fila TOTAL (si existe) debe coincidir con el mismo valor. |
| **28** | 84 | Resultados del ejercicio económico 2019-2023 por empresa | NOMBRE_EMPRESA; AÑO_2019; AÑO_2020; AÑO_2021; AÑO_2022; AÑO_2023. Incluye filas TOTAL BENEFICIO y TOTAL PÉRDIDA. **Cruce (año 2023):** TOTAL BENEFICIO (C28) = Cuadro 24 UTILIDAD DEL EJERCICIO; TOTAL PÉRDIDA (C28, valor absoluto) = Cuadro 24 PÉRDIDA DEL EJERCICIO. |
| **29** | 85 | Indicadores financieros (año del anuario) por empresa | 5 columnas: (1) % Siniestralidad Pagada, (2) % Gastos de Administración, (3) % Comisión y Gastos de Adquisición, (4) Índice de Cobertura de Reservas, (5) Índice Utilidad/Pérdida vs Patrimonio. **Cruces:** (1)=C7 TOTAL/C4 TOTAL×100; (2)=C22 PORCENTAJE; (3)=suma comisiones 23-A+23-B+23-C / C4 TOTAL×100; (4) referencia C11/C4×100; (5) agregado C28/C24. Fórmulas en Notas Finales (págs. 137-139). |
| **30** | 86 | Suficiencia/insuficiencia patrimonio propio no comprometido vs margen de solvencia | 3 columnas al 31/12/2022: Patrimonio propio no comprometido, Margen de solvencia, % suficiencia/insuficiencia. 3 columnas al 31/12/2023: misma estructura. Una fila por empresa. Nota (2): no remitieron formulario MS-02. |
| **31-A** | 87 | Primas netas cobradas por empresa 2023 vs 2022 | NOMBRE_EMPRESA; PRIMAS_2022; PRIMAS_2023; CRECIMIENTO_PORC. **Cruce:** PRIMAS_2023 (C31-A) = columna TOTAL del Cuadro 4 (misma empresa). |
| **31-B** | 88 | Primas netas cobradas - Prestaciones y siniestros pagados (1990-2023) | Serie anual, año base 2007. Valores antiguos cercanos a cero por indexación; se corregirá con más anuarios. **Cruce solo última línea (2023):** PRIMAS_NETAS_COBRADAS (2023) = C31-A Total o C4; PRESTACIONES_SINIESTROS_PAGADOS (2023) = C6 TOTAL. |
| **32** | 89 | Reservas de prima y reservas siniestros pendientes por empresa – Hospitalización, Cirugía y Maternidad Individual | 3 cols Reservas de Prima (Retención propia, A cargo reaseguradores, Total) + 3 cols Reservas Siniestros Pendientes (ídem). (*) No incluye reservas siniestros ocurridos y no notificados. **Cruce:** Fila TOTAL = C10 y C15 ramo "Hospitalización Individual"; por empresa Retención prima = 20-A col. Hospitalización Individual, Retención siniestros = 20-D col. Hospitalización Individual. |
| **33** | 90 | Reservas de prima y reservas siniestros pendientes por empresa – Hospitalización, Cirugía y Maternidad COLECTIVO | Misma estructura que C32 para el ramo COLECTIVO. **Cruce:** Fila TOTAL = C10 y C15 ramo "Hospitalización Colectivo"; por empresa = 20-A y 20-D col. Hospitalización Colectivo. |
| **34** | 91 | Primas brutas por ramo/empresa al 31/12/2023 | **Primeras 3 columnas:** SEGUROS DE PERSONAS (Seguro Directo, Reaseguro Aceptado, Total). **Siguientes 3 columnas:** SEGUROS GENERALES (Seguro Directo, Reaseguro Aceptado, Total). Una fila por empresa + TOTAL. **Consistencia interna:** suma de empresas = fila TOTAL por cada columna. **Referencia:** Cuadro 3 (Personas = fila SEGURO DE PERSONAS; Generales = TOTAL − Personas − Solidarios; pueden diferir por criterio brutas/netas). |
| **35** | 92 | Devolución de primas por ramo/empresa al 31/12/2023 | Misma estructura que Cuadro 34: **Primeras 3 columnas:** SEGUROS DE PERSONAS (Seguro Directo, Reaseguro Aceptado, Total). **Siguientes 3 columnas:** SEGUROS GENERALES (ídem). Una fila por empresa + TOTAL. **Consistencia interna:** suma empresas = fila TOTAL. |
| **36** | 93 | Reservas prestaciones y siniestros pendientes + ocurridos y no notificados por empresa (retención propia) | Total (A+B), Prestaciones y Siniestros Pendientes (A), Siniestros Ocurridos y No Notificado (B), % (B/A). **Consistencia:** TOTAL = A + B. **Cruce:** columna (A) = Cuadro 16 RETENCION_PROPIA (reservas prestaciones/siniestros por empresa). |
| **37** | 94 | Cantidad de pólizas y cantidad de siniestros por ramo | Una fila por ramo (y secciones). **Columnas:** RAMO_DE_SEGUROS, POLIZAS (cantidad), SINIESTROS (cantidad). Son cantidades, no montos en bolívares. |
| **38** | 95 | Cantidad de pólizas y siniestros por empresa | Misma información que C37 pero por empresa. **Totales por columna (fila TOTAL) = fila TOTAL del Cuadro 37.** Consistencia interna: suma empresas = TOTAL. |
| **39** | 101 | Empresas de reaseguro autorizadas | Lista de empresas de reaseguro (Al 30/06/2023). Columnas: NUMERO_ORDEN, NOMBRE_EMPRESA. Inicio de la serie de tablas de EMPRESAS DE REASEGURO. |
| **40** | 102 | Balance condensado empresas de reaseguro | CONCEPTO; MONTO; TIPO (SECCION/LINEA/TOTAL_ACTIVO/TOTAL_PASIVO/TOTAL_CAPITAL/TOTAL_GLOBAL). **Validación interna:** suma líneas ACTIVOS = TOTAL ACTIVO; suma PASIVOS = TOTAL PASIVO; suma CAPITAL Y OTROS = TOTAL CAPITAL; TOTAL ACTIVO = TOTAL GENERAL; TOTAL PASIVO + TOTAL CAPITAL + UTILIDAD = TOTAL GENERAL. |
| **41-A** | 103 | Estado de Ganancias y Pérdidas - Ingresos (reaseguros) | CONCEPTO; MONTO; TIPO. Secciones: OPERACIONES TÉCNICAS (con sublíneas DEL PAÍS, NEGOCIOS NACIONALES/EXTRANJEROS), GESTIÓN GENERAL. **Validación interna:** suma líneas "padre" (excl. sublíneas) = OPERACIONES TÉCNICAS; suma líneas gestión = GESTIÓN GENERAL; OPER.+ GEST.= TOTAL INGRESOS; TOTAL INGRESOS + PÉRDIDA = TOTAL GENERAL. **Cruce con C40 y 41-B:** UTILIDAD C40 = Total Ingresos (41-A) − Total Egresos (41-B). |
| **41-B** | 104 | Estado de Ganancias y Pérdidas - Egresos (reaseguros) | CONCEPTO; MONTO; TIPO. Secciones: OPERACIONES TÉCNICAS (con sublíneas AL PAÍS, DEL PAÍS, NACIONALES, EXTRANJERAS, etc.), GESTIÓN GENERAL. **Validación interna:** suma líneas padre = OPERACIONES TÉCNICAS; suma gestión = GESTIÓN GENERAL; TOTAL EGRESOS = OPER.+ GEST.; TOTAL GENERAL = TOTAL EGRESOS + UTILIDAD. **Cruce con C40 y 41-A:** UTILIDAD C40 = Ingresos (41-A) − Egresos (41-B); UTILIDAD en 41-B = UTILIDAD C40. |
| **42** | 105 | Balance condensado por empresa (reaseguros) | CONCEPTO; RIV; KAIROS; PROVINCIAL; DELTA. Empresas de reaseguro en columnas. **Validación interna:** cada fila tiene 4 valores (una por empresa). **Cruce con Cuadro 40:** Para cada concepto, suma RIV + KAIROS + PROVINCIAL + DELTA = MONTO del mismo concepto en Cuadro 40 (Balance condensado reaseguros). |
| **43-A** | 106 | Estado de Ganancias y Pérdidas. Ingresos por empresas (reaseguros) | CONCEPTO; RIV_MONTO; RIV_PCT; KAIROS_MONTO; KAIROS_PCT; PROVINCIAL_MONTO; PROVINCIAL_PCT; DELTA_MONTO; DELTA_PCT. Dos columnas por empresa (monto y %). **Cruce con Cuadro 41-A:** Para cada concepto, suma RIV_MONTO + KAIROS_MONTO + PROVINCIAL_MONTO + DELTA_MONTO = MONTO del mismo concepto en Cuadro 41-A (ingresos agregados). |
| **43-B** | 107 | Estado de Ganancias y Pérdidas. Egresos por empresas (reaseguros) | Misma estructura que 43-A (monto y % por empresa). **Cruce con Cuadro 41-B:** Para cada concepto, suma de los 4 montos = MONTO del mismo concepto en Cuadro 41-B (egresos agregados). |
| **44** | 108 | Indicadores financieros 2023 reaseguros | 6 columnas: (1)% Siniestralidad Pagada, (2)% Gastos Administración, (3)% Comisión, (4) Cobertura de Reservas, (5) Índice Endeudamiento, (6) Utilidad o Pérdida vs Patrimonio. Una fila por empresa + Valor del Mercado Reasegurador. **Cruce:** Los valores deben coincidir con ratios calculados desde tablas anteriores (43-A, 43-B, 42); definiciones en Notas Finales. |
| **45** | 108 | Suficiencia/insuficiencia patrimonio vs margen de solvencia (reaseguros) | Corte 30/6/2022 y 30/6/2023 (reaseguros a mitad de año). 3 columnas por corte: MARGEN DE SOLVENCIA, PATRIMONIO PROPIO NO COMPROMETIDO, % DE SUFICIENCIA O INSUFICIENCIA DEL PATRIMONIO PROPIO. |
| **46** | 112 | Empresas financiadoras de primas autorizadas | Otro sujeto regulado. Lista al 31/12/2023. Columnas: NUMERO_ORDEN, NOMBRE_EMPRESA. Inicio de la serie de tablas de financiadoras de primas. |
| **47** | 113 | Balance condensado empresas financiadoras de primas | CONCEPTO; MONTO; TIPO. Al 31/12/2023. Secciones: ACTIVOS (con total), PASIVOS, CAPITAL, RESULTADO DEL EJERCICIO, TOTAL GENERAL. Validación interna: totales por sección coherentes. |
| **48** | 114 | Estado de Ganancias y Pérdidas. Ingresos y Egresos (financiadoras de primas) | CONCEPTO; MONTO; TIPO. Bloque INGRESOS: Operaciones de Financiamiento, Por Financiamiento, Ajuste de Valores, Otros Ingresos, TOTAL INGRESOS, Resultado (Pérdida), TOTAL GENERAL. Bloque EGRESOS: Gastos operacionales, administración, financieros, ajustes, otros, TOTAL EGRESOS, Resultado (Utilidad), TOTAL GENERAL. Los dos TOTAL GENERAL deben coincidir. |
| **49** | 115 | Ingresos por empresa (financiadoras de primas) | NOMBRE_EMPRESA; OPERACIONES_POR_FINANCIAMIENTO; POR_FINANCIAMIENTO; AJUSTE_DE_VALORES; TOTAL. Detalle por empresa de los tres conceptos de ingreso (Operaciones por Financiamiento, Por Financiamiento, Ajuste de Valores). **Cruce con Cuadro 48:** Fila TOTAL de C49: las tres columnas = mismos conceptos en C48; TOTAL C49 = suma de las tres (no incluye OTROS INGRESOS de C48). |
| **50** | 116 | Circulante (Activo) por empresa (financiadoras de primas) | NOMBRE_EMPRESA; DISPONIBLE; INVERSIONES; EXIGIBLE_CORTO_PLAZO; GASTOS_PAGADOS_ANTICIPADO; TOTAL. **Cruce con Cuadro 47:** Fila TOTAL (o suma columna TOTAL) = concepto CIRCULANTE bajo sección ACTIVOS en C47. |
| **51** | 117 | Gastos operativos, administrativos y financieros por empresa (financiadoras de primas) | NOMBRE_EMPRESA; GASTOS_OPERATIVOS; GASTOS_ADMINISTRATIVOS; GASTOS_FINANCIEROS. **Cruce con Cuadro 48:** Fila TOTAL (o suma por columna) = GASTOS OPERACIONALES, GASTOS DE ADMINISTRACIÓN y GASTOS FINANCIEROS de C48 (egresos). |
| **52** | 118 | Indicadores financieros 2023 (financiadoras de primas) | NOMBRE_EMPRESA; SOLVENCIA; ENDEUDAMIENTO; RENTABILIDAD_FINANCIERA; RENTABILIDAD_INGRESOS; APALANCAMIENTO. Cinco columnas por empresa; (1)-(5) según Notas Finales. |
| **53** | 121 | Empresas de medicina prepagada autorizadas | NUMERO_REGISTRO; NUMERO_ORDEN; NOMBRE_EMPRESA. Al 31/12/2023. Nuevo sujeto regulado: medicina prepagada. |
| **54** | 122 | Balance condensado empresas de medicina prepagada | CONCEPTO; MONTO; TIPO. Secciones: ACTIVO (y TOTAL ACTIVO), Pérdidas/Saldo, TOTAL GENERAL, PASIVO (y TOTAL PASIVO), PATRIMONIO (y TOTAL PATRIMONIO), SUPERÁVIT NO REALIZADO, UTILIDAD, TOTAL GENERAL. **Validación interna:** suma líneas ACTIVO = TOTAL ACTIVO; TOTAL ACTIVO + pérdidas = TOTAL GENERAL; suma PASIVO = TOTAL PASIVO; suma PATRIMONIO = TOTAL PATRIMONIO; los dos TOTAL GENERAL iguales; ecuación contable pasivo+patrimonio+superávit+utilidad = TOTAL GENERAL. |
| **55-A** | 123 | Estado de Ganancias y Pérdidas - Ingresos (medicina prepagada) | CONCEPTO; MONTO; TIPO. Secciones: Operaciones de medicina prepagada, Ingresos por servicios médicos, Gestión financiera. **Validación interna:** suma LINEA por sección = monto sección; suma secciones = TOTAL INGRESOS; TOTAL INGRESOS + PÉRDIDA = TOTAL GENERAL. **Cruce con 55-B:** TOTAL GENERAL (55-A) = TOTAL GENERAL (55-B); TOTAL INGRESOS − TOTAL EGRESOS = UTILIDAD − PÉRDIDA. |
| **55-B** | 124 | Estado de Ganancias y Pérdidas - Egresos (medicina prepagada) | CONCEPTO; MONTO; TIPO. Secciones (solo líneas en mayúsculas): Operaciones directa/indirecta, Anulaciones, Cuotas cedidas/pagadas, Comisiones y gastos, Reservas técnicas, Gastos de administración, Gestión financiera. **Validación interna:** suma LINEA por sección = monto sección; suma secciones = TOTAL EGRESOS; TOTAL EGRESOS + UTILIDAD = TOTAL GENERAL. |
| **56** | 125 | Ingresos netos por empresa (medicina prepagada) | NOMBRE_EMPRESA; INGRESOS_POR_CONTRATOS. Una fila por empresa + TOTAL (valor del documento; ej. 2023: 72.141). Referencia: puede relacionarse con Cuadro 55-A "Ingresos por Contratos" (diferencia por netos vs concepto agregado). |
| **57** | 126 | Reservas técnicas por empresa (medicina prepagada) | Dos tablas en un solo CSV. (1) Columnas: Reservas para Cuotas en Curso; Reservas para Servicios Prestados y Reembolsos Pendientes de Pago; Reservas para Servicios Prestados y Reembolsos No Notificados; Reservas para Riesgos Catastróficos. (2) Columnas: Reservas para Reintegro por Experiencia Favorable; Cuotas Cobradas por anticipado; Vales Cobrados por Anticipado; Depósitos para Contratos en Proceso; TOTAL. Una fila por empresa + fila TOTAL. **Cruce con Cuadro 54:** La columna TOTAL de la segunda tabla (fila TOTAL) = concepto RESERVAS TÉCNICAS del Cuadro 54 (pasivo). |
| **58** | 127 | Indicadores financieros 2023 (medicina prepagada) | Dos tablas en un solo CSV. (1) Comisiones y Gastos de Adquisición %; Gastos de Administración %; Utilidad o Pérdida %. (2) Índice de Cobertura de Reservas Técnicas; Índice de Solvencia. Una fila por empresa (6 empresas con datos). (1)-(5) según Notas Finales. |

---

## 4. Reglas entre cuadros (cruce)

Las siguientes relaciones deben cumplirse entre tablas del mismo año.

| Origen | Referencia | Regla de cruce |
|--------|------------|----------------|
| **5-A** (suma por columna) | **Cuadro 3** | Totales por ramo de 5-A = totales "Seguros de Personas" en Cuadro 3 (9 ramos, mismo orden). |
| **5-B** (suma por columna) | **Cuadro 3** | Totales por ramo de 5-B = totales "Seguros Patrimoniales" en Cuadro 3 (16 ramos). |
| **5-C** (suma por columna) | **Cuadro 3** | Totales por ramo de 5-C = totales "Seguros Obligacionales" en Cuadro 3 (8 ramos). |
| **7** (suma por columna) | **Cuadro 6** | Suma por columna en 7 = valor del ramo correspondiente en Cuadro 6 (Hospitalización Ind./Col., Automóvil Casco, Resto, TOTAL). |
| **8-A** (suma por columna) | **Cuadro 6** | Suma de las 10 columnas 8-A = subtotal "Seguro de Personas" en Cuadro 6; por ramo, suma 8-A = ramo en Cuadro 6. |
| **8-B** (suma por columna) | **Cuadro 6** | Suma por columna 8-B = ramo "Seguros Patrimoniales" en Cuadro 6 (16 ramos). |
| **8-C** (suma por columna) | **Cuadro 6** | Suma por columna 8-C = ramo "Seguros Obligacionales" en Cuadro 6 (8 ramos). |
| **10** (col. Retención por sección) | **Cuadro 9** | RETENCION_PROPIA de "SEGURO DE PERSONAS" en 10 = "RESERVAS DE PRIMA SEGUROS DE PERSONAS" en 9. RETENCION_PROPIA "SEGUROS PATRIMONIALES" = "Patrimoniales" en 9. RETENCION_PROPIA "SEGUROS DE RESPONSABILIDAD" = "Obligacionales o de responsabilidad" en 9. |
| **11** (suma empresas) | **Cuadro 10** | Suma de RETENCION_PROPIA, A_CARGO_REASEGURADORES y TOTAL sobre todas las empresas en 11 = fila TOTAL del Cuadro 10. |
| **12** (suma empresas) | **Cuadro 10** | Suma empresas en 12 = fila "SEGURO DE PERSONAS" del Cuadro 10 (Retención propia, A cargo reaseguradores, Total). |
| **13** (suma empresas) | **Cuadro 10** | Suma empresas en 13 = fila "SEGUROS PATRIMONIALES" del Cuadro 10. |
| **14** (suma empresas) | **Cuadro 10** | Suma empresas en 14 = fila "SEGUROS DE RESPONSABILIDAD" del Cuadro 10. |
| **15** (totales y agrupaciones) | **Cuadro 9** | TOTAL C15 (Retención) = C9 "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES". Vida Individual (C15) = Vida (C9). Hospitalización Ind. + Accidentes Pers. Ind. (C15) = Individual de Personas (C9). Vida Col. + Accid. Col. + Hosp. Col. (C15) = Colectivos de Personas (C9). Funerario = Funerarios. SEGUROS PATRIMONIALES/RESPONSABILIDAD (C15) = Patrimoniales/Obligacionales (C9). |
| **16** (suma empresas) | **Cuadro 15** | Suma de RETENCION_PROPIA, A_CARGO_REASEGURADORES y TOTAL sobre todas las empresas en 16 = fila TOTAL del Cuadro 15. |
| **17** (suma empresas) | **Cuadro 15** | Suma empresas en 17 = fila "SEGURO DE PERSONAS" del Cuadro 15 (Retención, Reaseguro, Total). |
| **18** (suma empresas) | **Cuadro 15** | Suma empresas en 18 = fila "SEGUROS PATRIMONIALES" del Cuadro 15. |
| **19** (suma empresas) | **Cuadro 15** | Suma empresas en 19 = fila "SEGUROS DE RESPONSABILIDAD" del Cuadro 15. |
| **20-A** (suma por columnas 9 ramos) | **Cuadro 12** | Suma de las columnas de los 9 ramos en 20-A (pág 47 + pág 48, sin columna TOTAL) = total "Por Retención propia de la Empresa" en Cuadro 12 (fila TOTAL o suma de empresas). |
| **20-B** (suma por columnas 16 ramos) | **Cuadro 13** | Suma de las columnas de los 16 ramos en 20-B (pág 49 + 50 + 51, sin columna TOTAL) = total "Por Retención propia de la Empresa" en Cuadro 13 (fila TOTAL o suma de empresas). |
| **20-C** (suma por columnas 8 ramos) | **Cuadro 14** | Suma de las columnas de los 8 ramos en 20-C (pág 52 + 53, sin columna TOTAL) = total "Por Retención propia de la Empresa" en Cuadro 14 (fila TOTAL o suma de empresas). |
| **20-D** (suma por columnas 9 ramos) | **Cuadro 17 y Cuadro 15** | Suma de los 9 ramos en 20-D = total Retención propia en Cuadro 17 = fila "SEGURO DE PERSONAS" del Cuadro 15. |
| **20-E** (suma por columnas 16 ramos) | **Cuadro 18 y Cuadro 15** | Suma de los 16 ramos en 20-E = total Retención propia en Cuadro 18 = fila "SEGUROS PATRIMONIALES" del Cuadro 15. |
| **20-F** (suma por columnas 8 ramos) | **Cuadro 19 y Cuadro 15** | Suma de los 8 ramos en 20-F = total Retención propia en Cuadro 19 = fila "SEGUROS DE RESPONSABILIDAD" del Cuadro 15. |
| **22** (col. Primas Netas por empresa) | **Cuadro 4** | Para cada empresa, PRIMAS_NETAS en Cuadro 22 = TOTAL en Cuadro 4 (misma empresa). |
| **23** (col. Primas Netas por ramo) | **Cuadro 3** | Para cada ramo, PRIMAS_NETAS en Cuadro 23 = SEGURO DIRECTO en Cuadro 3 (mismo ramo). Sección "SEGUROS OBLIGACIONALES O DE RESPONSABILIDAD" = suma de los 8 ramos obligacionales en C3. |
| **23-A** (suma total) | **Cuadro 23** | Suma de todas las celdas (o col. TOTAL pág 65) = Cuadro 23 fila "SEGURO DE PERSONAS" col. COMISIONES_GASTOS_ADQUISICION. |
| **23-B** (suma total) | **Cuadro 23** | Suma total = Cuadro 23 fila "SEGUROS PATRIMONIALES" col. COMISIONES_GASTOS_ADQUISICION. |
| **23-C** (suma total) | **Cuadro 23** | Suma total = Cuadro 23 fila "SEGUROS OBLIGACIONALES..." col. COMISIONES_GASTOS_ADQUISICION. |
| **23-D** (suma total) | **Cuadro 23** | Suma total = Cuadro 23 fila "SEGURO DE PERSONAS" col. GASTOS_ADMINISTRACION. |
| **23-E** (suma total) | **Cuadro 23** | Suma total = Cuadro 23 fila "SEGUROS PATRIMONIALES" col. GASTOS_ADMINISTRACION. |
| **23-F** (suma total) | **Cuadro 23** | Suma total = Cuadro 23 fila "SEGUROS OBLIGACIONALES..." col. GASTOS_ADMINISTRACION. |
| **25-A** (Primas Aceptadas Reaseguro) | **Cuadro 3** | "Primas Aceptadas Seguros de Personas" = C3 REASEGURO ACEPTADO (fila SEGURO DE PERSONAS). "Primas Aceptadas Seguros Generales" = C3 REASEGURO ACEPTADO (fila SEGUROS PATRIMONIALES). |
| **25-A** (Primas del Ejercicio) | **Cuadro 3** | Comparación informativa: Primas del Ejercicio Personas/Generales vs C3 TOTAL o SEGURO DIRECTO por segmento (pueden diferir por criterio devengado/cobrado o bruto/neto). |
| **25-B** (Siniestros/Prestaciones) | **Cuadro 6** | Prestaciones Pagadas + Siniestros Pagados (Personas) = C6 TOTAL SEGURO DE PERSONAS. Siniestros Pagados (Generales) = C6 TOTAL PATRIMONIALES + OBLIGACIONALES. |
| **25-B** (Comisiones y Gastos Adm) | **Cuadro 23** | Comisiones y Gastos de Adquisición (Personas/Generales) = C23 COMISIONES_GASTOS_ADQUISICION por segmento. Gastos de Administración (Personas/Generales) = C23 GASTOS_ADMINISTRACION por segmento. |
| **26** (PRODUCTO BRUTO TOTAL) | **Cuadro 25-A** | PRODUCTO BRUTO TOTAL (C26) = fila "GESTIÓN GENERAL DE LA EMPRESA" en 25-A (ingresos). |
| **26** (TOTAL EGRESOS GESTIÓN) | **Cuadro 25-B** | TOTAL EGRESOS POR LA GESTIÓN GENERAL (C26) = fila "GESTIÓN GENERAL DE LA EMPRESA" en 25-B (egresos). PRODUCTO NETO = PRODUCTO BRUTO − TOTAL EGRESOS. |
| **27** (col. Producto de Inversiones) | **Cuadro 26** | Suma de la columna PRODUCTO_INVERSIONES (C27) por empresas = "A.PRODUCTO DE INVERSIONES" en C26. |
| **28** (TOTAL BENEFICIO / TOTAL PÉRDIDA 2023) | **Cuadro 24** | Para el año 2023: TOTAL BENEFICIO (C28) = UTILIDAD DEL EJERCICIO (C24); TOTAL PÉRDIDA (C28, valor absoluto) = PÉRDIDA DEL EJERCICIO (C24). |
| **31-A** (PRIMAS_2023) | **Cuadro 4** | Por empresa: PRIMAS_2023 (C31-A) = TOTAL (C4). |
| **31-B** (fila 2023) | **C31-A / C4 y C6** | Última línea (2023): PRIMAS_NETAS_COBRADAS = C31-A Total (o suma C4); PRESTACIONES_SINIESTROS_PAGADOS = C6 TOTAL. |
| **32** (TOTAL y por empresa) | **C10, C15, 20-A, 20-D** | TOTAL C32 (3 cols prima) = C10 Hospitalización Individual; TOTAL C32 (3 cols siniestros) = C15 Hospitalización Individual. Por empresa: col. Retención prima = 20-A Hospitalización Individual; col. Retención siniestros = 20-D Hospitalización Individual. |
| **33** (TOTAL y por empresa) | **C10, C15, 20-A, 20-D** | Igual que C32 pero ramo Hospitalización Colectivo: TOTAL C33 = C10/C15 "Hospitalización Colectivo"; por empresa = 20-A/20-D col. Hospitalización Colectivo. |
| **34** (consistencia interna y referencia) | **Cuadro 3** | Suma empresas (excl. TOTAL) = fila TOTAL en cada una de las 6 columnas. Referencia: C34 TOTAL Personas (3 cols) vs C3 "SEGURO DE PERSONAS"; C34 TOTAL Generales vs C3 (TOTAL − Personas − Solidarios); diferencias esperables (brutas vs por ramo). |
| **35** (consistencia interna) | — | Suma empresas (excl. TOTAL) = fila TOTAL en cada una de las 6 columnas (Devolución de primas Personas/Generales). |
| **36** (TOTAL = A+B y col. A) | **Cuadro 16** | Consistencia: TOTAL = PRESTACIONES_SINIESTROS_PENDIENTES_A + SINIESTROS_OCURRIDOS_NO_NOTIFICADOS_B. Columna (A) C36 = RETENCION_PROPIA C16 por empresa. |
| **38** (totales por columna) | **Cuadro 37** | C38 fila TOTAL (POLIZAS, SINIESTROS) = C37 fila TOTAL. Suma empresas en C38 = fila TOTAL C38. |
| **41-A** (cruce con C40 y 41-B) | **Cuadro 40, Cuadro 41-B** | UTILIDAD DEL EJERCICIO (C40) = Total Ingresos (C41-A) − Total Egresos (C41-B). Se verifica cuando existe 41-B. |
| **42** (suma por fila) | **Cuadro 40** | Para cada concepto del Cuadro 42, suma RIV + KAIROS + PROVINCIAL + DELTA = MONTO del concepto correspondiente en Cuadro 40 (Balance condensado reaseguros). |
| **43-A** (suma montos por fila) | **Cuadro 41-A** | Para cada concepto, suma RIV_MONTO + KAIROS_MONTO + PROVINCIAL_MONTO + DELTA_MONTO (C43-A) = MONTO (C41-A). |
| **43-B** (suma montos por fila) | **Cuadro 41-B** | Para cada concepto, suma de los 4 montos (C43-B) = MONTO (C41-B). |
| **44** (indicadores por empresa) | **43-A, 43-B, 42** | (1) % Siniestralidad, (2) % Gastos Adm, (3) % Comisión, (6) Utilidad/Patrimonio derivables de 43-A, 43-B y 42 por empresa. Referencia (definiciones en Notas Finales). |
| **49** (fila TOTAL) | **Cuadro 48** | OPERACIONES_POR_FINANCIAMIENTO (C49) = "OPERACIONES DE FINANCIAMIENTO" (C48); POR_FINANCIAMIENTO (C49) = "POR FINANCIAMIENTO" (C48); AJUSTE_DE_VALORES (C49) = "AJUSTE DE VALORES" (C48). TOTAL (C49) = suma de las tres columnas (no incluye OTROS INGRESOS de C48). |
| **50** (fila TOTAL o suma col. TOTAL) | **Cuadro 47** | Total Circulante (activo) en C50 = concepto CIRCULANTE (activo) en C47 (primera ocurrencia, bajo sección ACTIVOS). |
| **55-A / 55-B** | **Entre sí** | TOTAL GENERAL (55-A) = TOTAL GENERAL (55-B). TOTAL INGRESOS − TOTAL EGRESOS = UTILIDAD − PÉRDIDA. |
| **57** (fila TOTAL, col. TOTAL_RESERVAS) | **Cuadro 54** | TOTAL de la segunda tabla (columna TOTAL_RESERVAS en fila TOTAL) = concepto RESERVAS TÉCNICAS del Cuadro 54 (sección PASIVO). |
| **29** (1) % Siniestralidad Pagada | **C4, C7** | Por empresa: C29 col(1) = C7 TOTAL / C4 TOTAL × 100. |
| **29** (2) % Gastos de Administración | **C22** | Por empresa: C29 col(2) = C22 PORCENTAJE. |
| **29** (3) % Comisión y Gastos de Adquisición | **C4, 23-A, 23-B, 23-C** | Por empresa: C29 col(3) = suma(comisiones 23-A+23-B+23-C) / C4 TOTAL × 100. |
| **29** (4) Cobertura Reservas | **C4, C11** | Referencia: C11 TOTAL / C4 TOTAL × 100 (puede diferir por definición en anuario). |
| **29** (5) Índice Utilidad/Pérdida vs Patrimonio | **C28, C24** | Agregado: resultado C28 / patrimonio (C24). |

---

## 5. Índice de cuadros y scripts de verificación

| # | Cuadro | Archivo CSV | Verificación interna / cruce |
|---|--------|-------------|------------------------------|
| 3 | Primas por ramo | `cuadro_03_primas_por_ramo.csv` | Totales por ramo |
| 4 | Primas por ramo/empresa | `cuadro_04_primas_por_ramo_empresa.csv` | Suma TOTAL = total cuadro |
| 5-A | Primas Personas (2 págs) | `cuadro_05A_pag20_5_ramos.csv`, `cuadro_05A_pag21_4_ramos_total.csv` | `verificar_cruce_5A_cuadro3.py` |
| 5-B | Primas Patrimoniales (3 págs) | `cuadro_05B_pag22_5_ramos.csv`, … | `verificar_cruce_5B_cuadro3.py` |
| 5-C | Primas Obligacionales (2 págs) | `cuadro_05C_pag25_5_ramos.csv`, … | `verificar_cruce_5C_cuadro3.py` |
| 6 | Siniestros por ramo | `cuadro_06_siniestros_pagados_por_ramo.csv` | `verificar_cuadro_6_siniestros.py` |
| 7 | Siniestros por ramo/empresa | `cuadro_07_siniestros_por_ramo_empresa.csv` | `verificar_cruce_cuadro7_cuadro6.py` |
| 8-A | Siniestros Personas (2 págs) | `cuadro_08A_pag29_5_ramos.csv`, … | `verificar_cruce_8A_cuadro6.py` |
| 8-B | Siniestros Patrimoniales (3 págs) | `cuadro_08B_pag31_5_ramos.csv`, … | `verificar_cruce_8B_cuadro6.py` |
| 8-C | Siniestros Obligacionales (2 págs) | `cuadro_08C_pag34_5_ramos.csv`, … | `verificar_cruce_8C_cuadro6.py` |
| 9 | Reservas técnicas | `cuadro_09_reservas_tecnicas.csv` | `verificar_cuadro_9_reservas.py` |
| 10 | Reservas prima por ramo | `cuadro_10_reservas_prima_por_ramo.csv` | `verificar_cruce_cuadro10_cuadro9.py` |
| 11 | Reservas prima por empresa | `cuadro_11_reservas_prima_por_empresa.csv` | `verificar_cruce_cuadro11_cuadro10.py` |
| 12 | Reservas prima Personas por empresa | `cuadro_12_reservas_prima_personas_por_empresa.csv` | `verificar_cruce_cuadros12_13_14_cuadro10.py` |
| 13 | Reservas prima Patrimoniales por empresa | `cuadro_13_reservas_prima_patrimoniales_por_empresa.csv` | (mismo script) |
| 14 | Reservas prima Obligacionales por empresa | `cuadro_14_reservas_prima_obligacionales_por_empresa.csv` | (mismo script) |
| 15 | Reservas prestaciones/siniestros pendientes por ramo | `cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv` | `verificar_cruce_cuadro15_cuadro9.py` |
| 16 | Reservas prestaciones/siniestros pendientes por empresa | `cuadro_16_reservas_prestaciones_siniestros_por_empresa.csv` | `verificar_cruce_cuadro16_cuadro15.py` |
| 17 | Reservas prestaciones/siniestros Personas por empresa | `cuadro_17_reservas_prestaciones_siniestros_personas_por_empresa.csv` | `verificar_cruce_cuadro17_cuadro15.py` |
| 18 | Reservas prestaciones/siniestros Patrimoniales por empresa | `cuadro_18_reservas_prestaciones_siniestros_patrimoniales_por_empresa.csv` | `verificar_cruce_cuadros18_19_cuadro15.py` |
| 19 | Reservas prestaciones/siniestros Obligacionales por empresa | `cuadro_19_reservas_prestaciones_siniestros_obligacionales_por_empresa.csv` | (mismo script) |
| 20-A | Reservas de prima por ramo/empresa Personas (2 págs) | `cuadro_20A_pag47_5_ramos.csv`, `cuadro_20A_pag48_4_ramos_total.csv` | `verificar_cruce_cuadro20A_cuadro12.py` |
| 20-B | Reservas de prima por ramo/empresa Patrimoniales (3 págs) | `cuadro_20B_pag49_6_ramos.csv`, `cuadro_20B_pag50_6_ramos.csv`, `cuadro_20B_pag51_4_ramos_total.csv` | `verificar_cruce_cuadro20B_cuadro13.py` |
| 20-C | Reservas de prima por ramo/empresa Obligacionales (2 págs) | `cuadro_20C_pag52_5_ramos.csv`, `cuadro_20C_pag53_3_ramos_total.csv` | `verificar_cruce_cuadro20C_cuadro14.py` |
| 20-D | Reservas prestaciones/siniestros pendientes por ramo/empresa Personas (2 págs) | `cuadro_20D_pag54_5_ramos.csv`, `cuadro_20D_pag55_4_ramos_total.csv` | `verificar_cruce_cuadro20D_cuadro17.py` |
| 20-E | Reservas prestaciones/siniestros pendientes por ramo/empresa Patrimoniales (3 págs) | `cuadro_20E_pag56_6_ramos.csv`, `cuadro_20E_pag57_6_ramos.csv`, `cuadro_20E_pag58_4_ramos_total.csv` | `verificar_cruce_cuadro20E_cuadro18.py` |
| 20-F | Reservas prestaciones/siniestros pendientes por ramo/empresa Obligacionales (2 págs) | `cuadro_20F_pag59_5_ramos.csv`, `cuadro_20F_pag60_3_ramos_total.csv` | `verificar_cruce_cuadro20F_cuadro19.py` |
| 21 | Inversiones aptas para reservas técnicas | `cuadro_21_inversiones_reservas_tecnicas.csv` | Verificación interna en `guardar_tablas_verificadas_2023.py` (suma subdivisiones = sección) |
| 22 | Gastos administración vs primas por empresa | `cuadro_22_gastos_admin_vs_primas_por_empresa.csv` | `verificar_cruce_cuadro22_cuadro4.py` (Primas Netas = C4 TOTAL) |
| 23 | Gastos producción vs primas por ramo | `cuadro_23_gastos_produccion_vs_primas_por_ramo.csv` | `verificar_cruce_cuadro23_cuadro3.py` (Primas Netas = C3 SEGURO DIRECTO) |
| 23-A | Comisiones por ramo/empresa Personas (2 págs) | `cuadro_23A_pag64_comisiones_5_ramos.csv`, `cuadro_23A_pag65_comisiones_4_ramos_total.csv` | `verificar_cruce_cuadros23_ABCDEF_cuadro23.py` (suma = C23 COMISIONES Personas) |
| 23-B | Comisiones por ramo/empresa Patrimoniales (3 págs) | `cuadro_23B_pag66/67/68_comisiones_*.csv` | Idem (suma = C23 COMISIONES Patrimoniales) |
| 23-C | Comisiones por ramo/empresa Obligacionales (2 págs) | `cuadro_23C_pag69/70_comisiones_*.csv` | Idem (suma = C23 COMISIONES Obligacionales) |
| 23-D | Gastos adm por ramo/empresa Personas (2 págs) | `cuadro_23D_pag71/72_gastos_adm_*.csv` | Idem (suma = C23 GASTOS_ADM Personas) |
| 23-E | Gastos adm por ramo/empresa Patrimoniales (3 págs) | `cuadro_23E_pag73/74/75_gastos_adm_*.csv` | Idem (suma = C23 GASTOS_ADM Patrimoniales) |
| 23-F | Gastos adm por ramo/empresa Obligacionales (2 págs) | `cuadro_23F_pag76/77_gastos_adm_*.csv` | Idem (suma = C23 GASTOS_ADM Obligacionales) |
| 24 | Balance condensado | `cuadro_24_balance_condensado.csv` | Validación interna: dos filas "TOTAL GENERAL" con mismo MONTO. |
| 25-A | Estado Ganancias y Pérdidas - Ingresos | `cuadro_25A_estado_ganancias_perdidas_ingresos.csv` | `verificar_cruce_cuadro25A_cuadro3.py` (Primas Aceptadas = C3 REASEGURO; Primas del Ejercicio vs C3 informativo). Validación interna en script de guardado (sumas por sección). |
| 25-B | Estado Ganancias y Pérdidas - Egresos | `cuadro_25B_estado_ganancias_perdidas_egresos.csv` | `verificar_cruce_cuadro25B_cuadro6_cuadro23.py` (Siniestros = C6; Comisiones y Gastos Adm = C23). Validación interna en script de guardado. |
| 26 | Gestión general | `cuadro_26_gestion_general.csv` | `verificar_cruce_cuadro26_cuadro25A_25B.py` (Producto bruto = 25-A Gestión; Total egresos = 25-B Gestión; Producto neto = Bruto − Egresos). |
| 27 | Rentabilidad inversiones por empresa | `cuadro_27_rentabilidad_inversiones_por_empresa.csv` | `verificar_cruce_cuadro27_cuadro26.py` (Suma Producto de Inversiones = C26 A.PRODUCTO DE INVERSIONES). |
| 28 | Resultados del ejercicio 2019-2023 por empresa | `cuadro_28_resultados_ejercicio_2019_2023_por_empresa.csv` | `verificar_cruce_cuadro28_cuadro24.py` (TOTAL BENEFICIO 2023 = C24 UTILIDAD; TOTAL PÉRDIDA 2023 = C24 PÉRDIDA). |
| 29 | Indicadores financieros 2023 por empresa | `cuadro_29_indicadores_financieros_2023_por_empresa.csv` | `verificar_cruce_cuadro29_indicadores.py` (5 columnas: (1) C7/C4, (2) C22, (3) 23-A,B,C/C4, (4) C11/C4 ref., (5) agregado). |
| 30 | Suficiencia patrimonio/solvencia 2022-2023 | `cuadro_30_suficiencia_patrimonio_solvencia_2022_2023.csv` | Estructura: 3 cols 31/12/2022 + 3 cols 31/12/2023 por empresa. |
| 31-A | Primas netas cobradas 2023 vs 2022 | `cuadro_31A_primas_netas_cobradas_2023_vs_2022.csv` | `verificar_cruce_cuadro31A_cuadro4.py` (PRIMAS_2023 = C4 TOTAL). |
| 31-B | Primas / Prestaciones y siniestros (1990-2023) | `cuadro_31B_primas_prestaciones_siniestros_1990_2023.csv` | `verificar_cruce_cuadro31B_2023.py` (solo fila 2023 vs C31-A/C4 y C6). |
| 32 | Reservas prima/siniestros Hospitalización Individual | `cuadro_32_reservas_prima_siniestros_hospitalizacion_individual.csv` | `verificar_cruce_cuadro32_cuadros10_15_20A_20D.py` (TOTAL = C10/C15; por empresa = 20-A/20-D). |
| 33 | Reservas prima/siniestros Hospitalización Colectivo | `cuadro_33_reservas_prima_siniestros_hospitalizacion_colectivo.csv` | `verificar_cruce_cuadro33_cuadros10_15_20A_20D.py` (mismo criterio que C32, ramo Colectivo). |
| 34 | Primas brutas Personas/Generales por empresa | `cuadro_34_primas_brutas_personas_generales_por_empresa.csv` | `verificar_cruce_cuadro34_cuadro3.py` (consistencia interna; referencia C3). |
| 35 | Devolución de primas Personas/Generales por empresa | `cuadro_35_devolucion_primas_personas_generales_por_empresa.csv` | `verificar_cruce_cuadro35.py` (consistencia interna). |
| 36 | Reservas prestaciones/siniestros pendientes + ocurridos no notificados por empresa | `cuadro_36_reservas_prestaciones_siniestros_pendientes_ocurridos_no_notificados.csv` | `verificar_cruce_cuadro36_cuadro16.py` (TOTAL=A+B; col. A = C16 RETENCION_PROPIA). |
| 37 | Cantidad de pólizas y siniestros por ramo | `cuadro_37_cantidad_polizas_siniestros_por_ramo.csv` | Sin script de cruce; columnas son cantidades (no montos). |
| 38 | Cantidad de pólizas y siniestros por empresa | `cuadro_38_cantidad_polizas_siniestros_por_empresa.csv` | `verificar_cruce_cuadro38_cuadro37.py` (totales = C37 TOTAL). |
| 39 | Empresas de reaseguro autorizadas | `cuadro_39_empresas_reaseguro_autorizadas.csv` | Lista; sin cruce. Inicio serie reaseguros. |
| 40 | Balance condensado reaseguros | `cuadro_40_balance_condensado_reaseguros.csv` | `verificar_cuadro40_balance_reaseguros.py` (totales y subtotales internos). |
| 41-A | Estado Ganancias y Pérdidas - Ingresos (reaseguros) | `cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros.csv` | `verificar_cuadro41A_ingresos_reaseguros.py` (internos; cruce C40 con 41-B). |
| 41-B | Estado Ganancias y Pérdidas - Egresos (reaseguros) | `cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros.csv` | `verificar_cuadro41B_egresos_reaseguros.py` (internos; cruce C40 y 41-A). |
| 42 | Balance condensado por empresa (reaseguros) | `cuadro_42_balance_condensado_por_empresa_reaseguros.csv` | `verificar_cruce_cuadro42_cuadro40.py` (suma por fila = C40 por concepto). |
| 43-A | Estado Ganancias y Pérdidas - Ingresos por empresa (reaseguros) | `cuadro_43A_estado_ganancias_perdidas_ingresos_por_empresa_reaseguros.csv` | `verificar_cruce_cuadros43_41.py` (suma 4 montos = C41-A por concepto). |
| 43-B | Estado Ganancias y Pérdidas - Egresos por empresa (reaseguros) | `cuadro_43B_estado_ganancias_perdidas_egresos_por_empresa_reaseguros.csv` | `verificar_cruce_cuadros43_41.py` (suma 4 montos = C41-B por concepto). |
| 44 | Indicadores financieros 2023 reaseguros | `cuadro_44_indicadores_financieros_2023_reaseguros.csv` | `verificar_cuadro44_indicadores_reaseguros.py` (ratios vs 43-A, 43-B, 42). |
| 45 | Suficiencia patrimonio vs margen solvencia reaseguros (30/6/2022 y 30/6/2023) | `cuadro_45_suficiencia_patrimonio_solvencia_reaseguros_2022_2023.csv` | Estructura: 3 columnas por corte (Margen, Patrimonio no comprometido, % suficiencia/insuficiencia). |
| 46 | Empresas financiadoras de primas autorizadas | `cuadro_46_empresas_financiadoras_primas_autorizadas.csv` | Lista; sin cruce. Sujeto regulado: financiadoras de primas. |
| 47 | Balance condensado financiadoras de primas | `cuadro_47_balance_condensado_financiadoras_primas.csv` | CONCEPTO; MONTO; TIPO. Validación interna de totales por sección (como C40). |
| 48 | Estado Ganancias y Pérdidas - Ingresos y Egresos (financiadoras de primas) | `cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas.csv` | CONCEPTO; MONTO; TIPO. Validación interna: dos TOTAL GENERAL iguales. |
| 49 | Ingresos por empresa (financiadoras de primas) | `cuadro_49_ingresos_por_empresa_financiadoras_primas.csv` | `verificar_cruce_cuadro49_cuadro48.py` (fila TOTAL = C48 Operaciones, Por Financiamiento, Ajuste de Valores). |
| 50 | Circulante (Activo) por empresa (financiadoras de primas) | `cuadro_50_circulante_activo_por_empresa_financiadoras_primas.csv` | `verificar_cruce_cuadro50_cuadro47.py` (Total C50 = C47 CIRCULANTE activo). |
| 51 | Gastos operativos, administrativos y financieros por empresa (financiadoras de primas) | `cuadro_51_gastos_operativos_administrativos_financieros_por_empresa_financiadoras_primas.csv` | `verificar_cruce_cuadro51_cuadro48.py` (Totales C51 = C48 Gastos operacionales, administración, financieros). |
| 52 | Indicadores financieros 2023 (financiadoras de primas) | `cuadro_52_indicadores_financieros_2023_financiadoras_primas.csv` | 5 columnas: Solvencia, Endeudamiento, Rentabilidad Financiera, Rentabilidad Ingresos, Apalancamiento. (1)-(5) Ver Notas Finales. |
| 53 | Empresas de medicina prepagada autorizadas | `cuadro_53_empresas_medicina_prepagada_autorizadas.csv` | Lista; sujeto regulado: medicina prepagada. |
| 54 | Balance condensado medicina prepagada | `cuadro_54_balance_condensado_medicina_prepagada.csv` | `verificar_cuadro54_balance_medicina_prepagada.py` (totales y subtotales internos). |
| 55-A | Estado Ganancias y Pérdidas - Ingresos (medicina prepagada) | `cuadro_55A_estado_ganancias_perdidas_ingresos_medicina_prepagada.csv` | `verificar_cuadros55_medicina_prepagada.py` (internos + cruce con 55-B). |
| 55-B | Estado Ganancias y Pérdidas - Egresos (medicina prepagada) | `cuadro_55B_estado_ganancias_perdidas_egresos_medicina_prepagada.csv` | (mismo script). |
| 56 | Ingresos netos por empresa (medicina prepagada) | `cuadro_56_ingresos_netos_por_empresa_medicina_prepagada.csv` | NOMBRE_EMPRESA; INGRESOS_POR_CONTRATOS. Fila TOTAL = total del documento (ej. 2023: 72.141). |
| 57 | Reservas técnicas por empresa (medicina prepagada) | `cuadro_57_reservas_tecnicas_por_empresa_medicina_prepagada.csv` | Dos tablas: (1) 4 columnas reservas; (2) 5 columnas (Reintegro, Cuotas/Vales anticipado, Depósitos, TOTAL). Fila TOTAL col. TOTAL_RESERVAS = C54 RESERVAS TÉCNICAS. `verificar_cruce_cuadro57_cuadro54.py`. |
| 58 | Indicadores financieros 2023 (medicina prepagada) | `cuadro_58_indicadores_financieros_2023_medicina_prepagada.csv` | Dos tablas: (1) Comisiones y Gastos Adquisición %, Gastos Administración %, Utilidad o Pérdida %; (2) Índice Cobertura Reservas Técnicas, Índice Solvencia. 6 empresas. (1)-(5) Notas Finales. |

**Total:** 100 archivos CSV, correspondientes a 56 cuadros (cuadros 3 a 58; varios cuadros generan 2 o 3 archivos). La lista de archivos y su orden por cuadro es la de `scripts/verificar_indice_anuario.py` (`INDICE_CSV_POR_CUADRO` + `ORDEN_CUADROS`); `scripts/verificar_csv_verificadas.py` usa la misma fuente.

**Generación:** `python scripts/guardar_tablas_verificadas_2023.py --year 2023` (sustituir `2023` por el año del anuario).  
**Formato CSV:** `python scripts/verificar_csv_verificadas.py --year 2023`.  
**Consistencia reglas vs archivos:** `python scripts/verificar_consistencia_reglas_archivos.py --year 2023` (comprueba que existan los 100 CSV, que no haya archivos sin cuadro y que los scripts de verificación referenciados existan).  
Los CSV se escriben en `data/staged/{año}/verificadas/`. La mayoría de scripts de cruce aceptan `--year`.

---

## 6. Generalización a otros años

### 6.1 Criterios reutilizables

- **Páginas:** El índice del anuario (páginas 4-6 del PDF) indica el número de cuadro y la página. Ejecutar `scripts/verificar_indice_anuario.py --year YYYY` para comprobar cobertura y ver la tabla página → cuadro. Si la paginación cambia con el año, ajustar en `scripts/verificar_indice_anuario.py`: `PAGINAS_POR_CUADRO` (y, si cambian archivos esperados, `INDICE_CSV_POR_CUADRO`). En `guardar_tablas_verificadas_2023.py` ajustar las constantes `PAGINA_CUADRO_*` según el índice del nuevo anuario.
- **Estructura:** La misma lógica de secciones (MAYÚSCULAS) y subdivisiones aplica a reservas y ramos; los nombres de ramos pueden variar levemente entre años (normalizar acentos y mayúsculas en cruces).
- **Tolerancia:** En sumas y cruces usar una tolerancia numérica (ej. 50 unidades o 0,01 % del total) para redondeos.
- **Orden recomendado:** Extraer primero los cuadros “resumen” (3, 6, 9, 10) y luego los desagregados (4, 5-A/B/C, 7, 8-A/B/C, 11), verificando cada uno antes de pasar al siguiente.
- **Documentar:** Para cada año nuevo, actualizar este archivo si aparecen nuevos cuadros o cambian reglas de cruce; revisar las Notas al final del PDF (págs. 137-139 en 2023) por si cambian fórmulas de indicadores.

### 6.2 Pasos para usar con otro año (checklist)

1. **Obtener el PDF** del anuario del año deseado (ej. Seguro en Cifras 2024).
2. **Revisar el índice** (págs. 4-6 del PDF): anotar la página de cada cuadro; si difieren de 2023, actualizar `PAGINAS_POR_CUADRO` en `scripts/verificar_indice_anuario.py` y las constantes `PAGINA_CUADRO_*` en `scripts/guardar_tablas_verificadas_2023.py`.
3. **Revisar las Notas al final** del PDF (en 2023: págs. 137-139): comprobar si las fórmulas de indicadores (Cuadros 27, 29, 44, 52, 58) o definiciones (primas netas, retención propia) han cambiado; actualizar `docs/NOTAS_ANUARIO_PAGS_137_139.md` si aplica.
4. **Extraer tablas:** `python scripts/guardar_tablas_verificadas_2023.py --year YYYY`. Los CSV se generan en `data/staged/YYYY/verificadas/`.
5. **Verificar cobertura:** `python scripts/verificar_indice_anuario.py --year YYYY` (debe listar todos los cuadros 3-58 y confirmar que existen sus CSV).
6. **Verificar formato CSV:** `python scripts/verificar_csv_verificadas.py --year YYYY`.
7. **Ejecutar scripts de cruce** que apliquen (la mayoría aceptan `--year YYYY`) para validar totales y consistencia entre cuadros.

---

## 7. Resumen de criterios por tipo

| Tipo | Criterio |
|------|----------|
| **Escritura** | CSV con `;`, UTF-8-sig, primera línea = nombres de campos, texto entre comillas cuando haga falta. |
| **Lectura** | Mismo separador y encoding; validar número de columnas por fila. |
| **Interna** | Sumas por fila/columna, totales por sección, Retención + Reaseguro = Total donde aplique. |
| **Entre tablas** | Cuadros desagregados (por empresa o por ramo) suman al cuadro resumen correspondiente (Cuadro 3, 6, 9, 10). |

Este archivo se irá ampliando tabla a tabla y entre tablas según se incorporen más cuadros del anuario.
