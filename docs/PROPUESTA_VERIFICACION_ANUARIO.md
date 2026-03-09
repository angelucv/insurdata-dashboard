# Propuesta: verificación del anuario y uso de las tablas

## Opciones

| Enfoque | Descripción | Pros | Contras |
|--------|-------------|------|--------|
| **A. Tabla a tabla por año** | Guardar cada cuadro en un archivo (por año), sin verificar todas antes | Rápido para tener datos guardados | Riesgo de errores no detectados; sin cruces entre cuadros |
| **B. Verificar todo el anuario 2023, luego guardar** | Verificar (y cruzar donde aplique) todos los cuadros del 2023; después guardar tabla a tabla por año | Calidad alta; cruces (ej. Cuadro 3 vs 4) validan consistencia | Más tiempo antes de tener todo guardado |
| **C. Año a año completo** | Completar 2023 (verificación + guardado), luego pasar a 2022, etc. | Un año “cerrado” antes de pasar al siguiente | Retrasa otros años |

## Recomendación: **B + guardado tabla a tabla por año**

1. **Cerrar la verificación del anuario 2023**  
   Recorrer los cuadros en orden (3, 4, 5-A, 5-B, …), con:
   - Verificación suma vs TOTAL en cada cuadro (como en Cuadro 4).
   - **Cruces de totales** donde tenga sentido:
     - **Cuadro 3** (Primas netas por ramo) vs **Cuadro 4** (Primas por ramo/empresa): la suma por ramo en el Cuadro 4 debe coincidir con el total del mismo ramo en el Cuadro 3.
   - Nombres de columnas/campos claros en salida para poder usar la información.

2. **Guardar tabla a tabla por año**  
   Una vez verificada cada tabla (y cruzada si aplica):
   - Un archivo por cuadro y año, ej.: `staged/2023/cuadro_3_primas_por_ramo.csv`, `staged/2023/cuadro_4_primas_por_ramo_empresa.csv`, etc.
   - Mismo esquema: columnas con nombres definidos, una fila por registro, año y número de cuadro en el nombre o en columnas.

3. **Orden sugerido para 2023**  
   - **Cuadro 3** (p.18): Primas netas por ramo → verificar TOTAL y extraer totales por ramo.  
   - **Cuadro 4** (p.19): ya verificado; usar sus totales por ramo para cruzar con Cuadro 3.  
   - Luego 5-A, 5-B, 6, 7, … en el orden del índice, verificando cada uno y cruzando cuando exista un cuadro agregado (por ramo) que lo respalde.

4. **Otros años**  
   Cuando 2023 esté verificado y guardado tabla a tabla, repetir el mismo proceso para 2022, 2021, etc., reutilizando la misma lógica de verificación y cruce.

## Cruce Cuadro 3 ↔ Cuadro 4

- **Cuadro 3:** una fila por ramo (Hospitalización Individual, Hospitalización Colectivo, Automóvil Casco, Resto de Ramos, etc.) con el **total del ramo**.
- **Cuadro 4:** una fila por empresa con columnas por ramo; el **total por ramo** es la suma de esa columna sobre todas las empresas.
- **Comprobación:** para cada ramo, `sum(Cuadro 4[rama])` debe ser igual al total de ese ramo en Cuadro 3 (con tolerancia por redondeo).

## Próximo paso inmediato

1. Verificar **Cuadro 3** (extracción, TOTAL, nombres de columnas).  
2. Calcular totales por ramo en Cuadro 4 (ya tenemos los datos) y compararlos con los totales por ramo del Cuadro 3.  
3. Si el cruce cuadra, seguir con Cuadro 5-A y así sucesivamente; si no, revisar extracción o definición de ramos antes de guardar.

---

## Cruce Cuadro 5-A (9 ramos) con Cuadro 3

El Cuadro 5-A está en **dos páginas**:
- **Página 20:** 5 ramos (columnas): Vida Individual, Vida Desgravamen Hipot., Rentas Vitalicias, Vida Colectivo, Accidentes Pers. Individual.
- **Página 21:** 4 ramos + TOTAL: Accidentes Pers. Colectivo, Hospitalización Ind., Hospitalización Col., Seguros Funerarios, TOTAL.

Esos **9 ramos** están en el **mismo orden** que en el Cuadro 3 (Seguros de Personas). La suma por columna en 5-A debe coincidir con el total por ramo del Cuadro 3.

**Script de verificación:** `python scripts/verificar_cruce_5A_cuadro3.py --year 2023`  
Comprueba que las sumas por ramo (5-A, 51 empresas, bloque principal) coinciden con los totales del Cuadro 3 (con tolerancia por redondeo).

---

## Nota sobre Cuadro 3 (primera verificación)

- **Estructura:** Columnas = RAMO DE SEGUROS | SEGURO DIRECTO | REASEGURO ACEPTADO | TOTAL | %  
- **Contenido:** Una fila por ramo (Hospitalización Individual 9.962.045, Hospitalización Colectivo 7.436.014, Automóvil casco 1.555.380, etc.) y fila TOTAL.  
- **Cruce con Cuadro 4:** La suma de la columna "Hospitalización Individual" en Cuadro 4 (todas las empresas) debe ser **9.962.045**; "Hospitalización Colectivo" debe sumar **7.436.014**; "Automóvil Casco" **1.555.380**; "Resto de Ramos" el resto hasta el total 24.976.109.  
- La verificación automática (suma vs TOTAL) en el script actual está pensada para tablas tipo Cuadro 4; para Cuadro 3 habría que usar la columna TOTAL explícita. El cruce con Cuadro 4 es la validación más útil para Cuadro 3.
