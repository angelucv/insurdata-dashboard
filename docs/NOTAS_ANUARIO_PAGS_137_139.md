# Notas al final del anuario (páginas 137 a 139)

Este documento transcribe las **Notas** que aclaran los cálculos utilizados a lo largo del anuario "Seguro en Cifras" y las relaciona con los cuadros y columnas extraídos en este proyecto.

---

## 1. Primas netas cobradas (aplicable a varios cuadros)

**Fórmula:**

```
Primas Netas Cobradas = PCSD + PCRA - DP
```

- **PCSD** = Primas Cobradas por Seguro Directo  
- **PCRA** = Primas Cobradas por Reaseguro Aceptado  
- **DP** = Devoluciones de Primas  

**Uso en el proyecto:** Cuadros de primas (3, 4, 5-A/B/C, 10, 11, 31-A, 31-B, 34, 35). La validación de totales y cruces entre cuadros debe considerar esta definición cuando se comparen “primas netas” con otros conceptos.

---

## 2. “Por retención propia de la empresa”

Donde se indique **“POR RETENCIÓN PROPIA DE LA EMPRESA”**, se refiere a cantidades netas de empresas reaseguradoras inscritas en el Registro de Empresas Reaseguradoras que lleva la Superintendencia de la Actividad Aseguradora, de acuerdo a los artículos 58 y 81 de la Ley de la Actividad Aseguradora vigente para el ejercicio económico del año 2023.

**Uso en el proyecto:** Cuadros 9, 10, 11-19, 20-A a 20-F, etc. Las columnas o conceptos que incluyan “retención propia” deben interpretarse en este sentido.

---

## 3. Cuadro N° 27 – Rentabilidad de las inversiones (fórmula de Hardy)

**Fórmula:**

```
TASA DE RENDIMIENTO = 2I / (A + B - I)
```

- **I** = Producto de las Inversiones para el período de cierre  
- **A** = Representación de las Reservas Técnicas + Garantía a la Nación + Inversiones no Aptas para la Representación de las Reservas Técnicas correspondientes al período de cierre  
- **B** = Representación de las Reservas Técnicas + Garantía a la Nación + Inversiones no Aptas para la Representación de las Reservas Técnicas correspondientes al año inmediatamente anterior al período de cierre  

**Archivo CSV:** `cuadro_27_rentabilidad_inversiones_por_empresa.csv`. Las columnas de rentabilidad/rendimiento reflejan esta fórmula. No se recalcula en los scripts de verificación; solo se comprueba coherencia de totales cuando aplica.

---

## 4. Cuadro N° 29 – Indicadores financieros (Empresas de Seguros)

Los indicadores (1)-(5) se determinan así:

| Código | Nombre en notas | Fórmula |
|--------|------------------|--------|
| (1) | Siniestralidad Pagada % | (Prestaciones y Siniestros Pagados netos de salvamentos) / Primas Netas Cobradas × 100 |
| (2) | Gastos de Administración % | Gastos de Administración / Primas Netas Cobradas × 100 |
| (3) | Comisión y Gastos de Adquisición % | Comisiones y Gastos de Adquisición / Primas Netas Cobradas × 100 |
| (4) | Índice de Cobertura de Reservas | Bienes Aptos para la Representación de Reservas Técnicas / Reservas Técnicas |
| (5) | Utilidad o Pérdida vs Patrimonio | Utilidad o Pérdida del Ejercicio / Patrimonio |

**Archivo CSV:** `cuadro_29_indicadores_financieros_2023_por_empresa.csv`. Las columnas del CSV deben corresponder a (1)-(5) en el orden indicado en el PDF. Ver Notas Finales del anuario para el orden exacto de columnas.

---

## 5. Cuadro N° 44 – Indicadores financieros (Empresas de Reaseguros)

| Código | Fórmula |
|--------|--------|
| (1) | Siniestralidad Pagada % = (Prestaciones y Siniestros Pagados / Primas) × 100 |
| (2) | Gastos de Administración % = Gastos de Administración / Primas × 100 |
| (3) | Comisión y Gastos de Adquisición % = Comisiones y Gastos de Adquisición / Primas × 100 |
| (4) | Índice de Cobertura de Reservas = Bienes Aptos para la Representación de Reservas Técnicas / Reservas Técnicas |
| (5) | Índice de Endeudamiento = Total Pasivo / Patrimonio |
| (6) | Utilidad o Pérdida vs Patrimonio = Utilidad o Pérdida del Ejercicio / Patrimonio |

**Archivo CSV:** `cuadro_44_indicadores_financieros_2023_reaseguros.csv`. Seis indicadores por empresa.

---

## 6. Cuadro N° 52 – Indicadores (Financiadoras de Primas / Cuotas)

| Código | Fórmula |
|--------|--------|
| (1) | Solvencia Financiera = Activo Circulante / Pasivo Total |
| (2) | Endeudamiento = Pasivo Total / Capital |
| (3) | Apalancamiento = Activo / Patrimonio |
| (4) | Rentabilidad de Ingresos = Utilidad / Ingresos |
| (5) | Rentabilidad Operacional = Utilidad / Patrimonio |

**Archivo CSV:** `cuadro_52_indicadores_financieros_2023_financiadoras_primas.csv`. Columnas: SOLVENCIA, ENDEUDAMIENTO, RENTABILIDAD_FINANCIERA, RENTABILIDAD_INGRESOS, APALANCAMIENTO. Ver Notas Finales para la correspondencia exacta (1)-(5).

---

## 7. Cuadro N° 58 – Indicadores (Empresas de Medicina Prepagada)

| Código | Fórmula |
|--------|--------|
| (1) | Comisión y Gastos de Adquisición % = (Comisiones y Gastos de Adquisición / Ingresos Netos Cobrados) × 100 |
| (2) | Gastos de Administración % = (Gastos de Administración / Ingresos Netos Cobrados) × 100 |
| (3) | Utilidad o Pérdida = Utilidad o Pérdida del Ejercicio / Patrimonio |
| (4) | Índice de Cobertura de Reservas = Bienes Aptos para la Representación de Reservas Técnicas / Reservas Técnicas |
| (5) | Índice de Solvencia = (Reservas Técnicas − Cuentas de Reservas a Cargo de Reaseguradores) / Patrimonio |

**Archivo CSV:** `cuadro_58_indicadores_financieros_2023_medicina_prepagada.csv`. Columnas: COMISIONES_GASTOS_ADQUISICION_PCT (1), GASTOS_ADMINISTRACION_PCT (2), UTILIDAD_PERDIDA_PCT (3), INDICE_COBERTURA_RESERVAS_TECNICAS (4), INDICE_SOLVENCIA (5).

---

## Verificación de lo realizado

- **Cuadros 29, 44, 52, 58:** Los nombres de columnas en los CSV coinciden con los indicadores (1)-(5) o (1)-(6) descritos en estas notas. No se recalculan los indicadores en los scripts; las validaciones existentes comprueban totales y cruces entre cuadros (p. ej. totales de balance vs estado de resultados).
- **Cuadro 27:** La fórmula de Hardy se documenta aquí; el CSV contiene los valores publicados.
- **Primas netas (nota 1):** Se usa como referencia en las reglas de cruce entre cuadros de primas (3, 4, 5-A/B/C, 10, 11, etc.) en `REGLAS_VALIDACION_SEGURO_EN_CIFRAS.md`.
- **Retención propia (nota 2):** Aclaración conceptual; no implica una validación numérica adicional en los scripts actuales.

Para más detalle sobre reglas por cuadro y cruces, ver `REGLAS_VALIDACION_SEGURO_EN_CIFRAS.md`.
