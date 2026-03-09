# Metodología de conversión a USD y factores de reconversión

Este documento explica la lógica aplicada para convertir las magnitudes de los **Anuarios de Seguros en Cifras** (SUDEASEG) a dólares estadounidenses (USD) y para tratar las reconversiones monetarias de Venezuela. La base técnica es el *Análisis Técnico de la Evolución Cambiaria y Normalización Estadística del Sector Asegurador Venezolano (2014-2024)*.

---

## 1. Objetivo

- Llevar todos los valores monetarios a **USD** para comparabilidad.
- Mostrar en el dashboard tanto el **valor original** (en la unidad del anuario: miles de Bs, Bs.F, Bs.S o Bs.D) como el **valor en USD**.
- Aplicar tasas oficiales BCV y distinguir variables de **stock** (tasa de cierre) y de **flujo** (tasa promedio anual).

---

## 2. Escala de los anuarios: "miles de bolívares"

En los cuadros estadísticos de SUDEASEG, las cifras suelen expresarse en **miles de bolívares**. Es decir:

- Un valor reportado como **1.515** en el anuario = **1.515.000** unidades monetarias (1.515 × 1.000).
- En este proyecto, los valores en `anuario_metricas.csv` se guardan en **miles**; la conversión a unidades del año se hace multiplicando por **1.000** antes de dividir por la tasa de cambio.

Fórmula base:

$$\text{Valor USD} = \frac{\text{Valor (miles)} \times 1.000}{\text{Tasa BCV (unidades por 1 USD)}}$$

---

## 3. Reconversiones monetarias (Venezuela)

Durante el periodo de los anuarios han ocurrido varias reconversiones. La **unidad de cuenta** cambia de nombre y escala:

| Fecha      | Reconversión   | Relación con la unidad anterior |
|-----------|----------------|----------------------------------|
| 2008      | Bs → Bs.F      | 1 Bs.F = 1.000 Bs               |
| 20 Ago 2018 | Bs.F → Bs.S  | 1 Bs.S = 100.000 Bs.F            |
| 1 Oct 2021 | Bs.S → Bs.D  | 1 Bs.D = 1.000.000 Bs.S (6 ceros) |

Para **comparar cifras en la misma unidad** (por ejemplo, expresar todo en la unidad actual), se aplicaría un factor acumulado desde Bs.F (2014) hasta la unidad 2024:

$$\text{Factor acumulado (2014 → 2024)} = 10^5 \times 10^6 = 10^{11}$$

En este proyecto **no** reexpresamos todas las series a la unidad 2024 antes de convertir. En su lugar, cada año se convierte **directamente a USD** con la tasa BCV de ese año (en la unidad de ese año). Así se evita confusión y se mantiene trazabilidad: valor original en miles de [Bs.F/Bs.S/Bs.D] + valor USD.

---

## 4. Tasa BCV vs. tasa mercado sugerida

La tasa oficial BCV ha operado con rezago respecto a la dinámica de precios en la calle. Para **siniestros pagados** (reposición de piezas, servicios médicos indexados al dólar de mercado) se utiliza una **tasa mercado sugerida** (referencias paralelo/SIMADI-DICOM por año), de modo que el **índice de siniestralidad** (siniestros/primas en USD) refleje la siniestralidad real. Las **primas** se convierten con tasa BCV (oficial).

- **Primas netas cobradas**: tasa BCV promedio anual (flujo).
- **Siniestros pagados**: tasa mercado sugerida (cierre) — ver tabla en §5.
- **Reservas, capital, balance**: tasa BCV cierre (stock).

El archivo `tasa_cambio_bcv_2014_2024.csv` incluye: `tasa_bcv_cierre`, `tasa_bcv_promedio`, `tasa_mercado_cierre`, `factor_ajuste_ceros`.

## 5. Normalización a unidad 2024 (evitar saltos por reconversión)

Para que un dato de 2014 sea comparable con uno de 2024 en la misma escala:

- **2014–2017** (Bs.F): dividir la cifra en unidades del año entre **10¹¹** (cien mil millones).
- **2018–2020** (Bs.S): dividir entre **10⁶** (un millón).
- **2021 en adelante** (Bs.D/actual): factor **1** (unidad actual).

Así se neutralizan las reconversiones (5 ceros en 2018, 6 ceros en 2021). La conversión a **USD equivalente 2024** consiste en: (1) normalizar a Bs. actual con el factor anterior, (2) dividir entre la tasa de cierre 2024. Esto evita “brincos” en la serie por cambio de unidad.

## 6. Variables de stock vs. flujo (BCV)

- **Stock** (reservas, capital, activo/pasivo): tasa BCV cierre.
- **Flujo** (primas, comisiones, resultados): tasa BCV promedio. Para **siniestros** se usa tasa mercado (véase §4).

La asignación está en `src/etl/tasas_cambio.py` (`METRICAS_STOCK`, `METRICAS_FLUJO`, `METRICAS_SINIESTROS`).

---

## 7. Tasas BCV y tasa mercado (2014-2024)

La siguiente tabla resume las tasas que usa el proyecto para el periodo 2014-2024. Fuente: BCV (cierre 31-Dic y promedio anual según disponibilidad). Para 2014-2017 se utiliza la tasa más alta oficialmente disponible (SICAD/DICOM) para una visión más conservadora del sector.

| Año | Unidad   | Tasa cierre (31-Dic) | Tasa promedio anual | Uso principal      |
|-----|----------|----------------------|----------------------|--------------------|
| 2014 | Bs.F    | 12,00 (SICAD)        | 12,00                | Stock y flujo      |
| 2015 | Bs.F    | 198,70 (SIMADI)      | 198,70               | Stock y flujo      |
| 2016 | Bs.F    | 673,73 (DICOM)       | 673,73               | Stock y flujo      |
| 2017 | Bs.F    | 3.345,00 (DICOM)     | 3.345,00             | Stock y flujo      |
| 2018 | Bs.S    | 638,18               | 638,18               | Stock y flujo      |
| 2019 | Bs.S    | 46.620,83            | 46.620,83            | Stock y flujo      |
| 2020 | Bs.S    | 1.107.198,58         | 1.107.198,58         | Stock y flujo      |
| 2021 | Bs.D    | 4,58                 | 0,49                 | Cierre stock; promedio flujo |
| 2022 | Bs.     | 17,48                | 4,64                 | Cierre stock; promedio flujo |
| 2023 | Bs.     | 35,95                | 17,48                | Cierre stock; promedio flujo |
| 2024 | Bs.     | ~51,93 (proy.)       | ~35,67 (est.)        | Cierre stock; promedio flujo |

Además, para **siniestros** se usa la **tasa mercado sugerida** (columna `tasa_mercado_cierre` en el CSV), por ejemplo: 2014 → 171; 2015 → 833; 2016 → 3.164; 2017 → 111.413; 2018 → 730; 2019 → 56.122; 2020 → 1.027.812; 2021 → 4,71; 2022 → 18,55; 2023 → 39,35; 2024 → 66,25 (brecha ~27,6 %).

Para años anteriores a 2014 se usa `tasa_cambio_anual.csv` (una sola tasa por año).

---

## 8. Verificación de consistencia antes del dashboard

**No se debe pasar a la etapa del dashboard si la serie histórica no es consistente.** El objetivo es mostrar la serie de los 10 años (2014-2024) sin saltos incoherentes.

1. Ejecutar **corrida en frío** y **serie 10y**:
   - `python scripts/indicadores_corrida_fria.py`
   - `python scripts/serie_historica_10y_usd.py`
2. Revisar salidas:
   - `indice/serie_historica_10y_usd.csv`: primas y siniestros en USD y en USD equivalente 2024.
   - `indice/analisis_consistencia_serie_10y.txt`: años con datos, alertas de saltos, conclusión.
3. Criterio: si hay **alertas de salto** (ratio año a año &gt; 5 o &lt; 0,2) o años sin datos en la ventana, resolver antes de exponer la serie en el dashboard.

## 9. Lógica aplicada en código

1. **Valor original**  
   - Se conserva siempre en **miles** (`valor_miles`) y en **unidades del año** (`valor_miles × 1.000`) para mostrar “cifra original” en el dashboard.

2. **Elección de tasa**  
   - **Siniestros pagados** → `tasa_mercado_cierre`. Resto **flujo** (primas, etc.) → `tasa_bcv_promedio`. **Stock** → `tasa_bcv_cierre`. Años &lt; 2014: `tasa_cambio_anual.csv`.

3. **Conversión a USD**  
   - `valor_usd = (valor_miles × 1.000) / tasa_elegida`.

4. **USD equivalente 2024**  
   - Normalizar: `valor_bs_actual = (valor_miles × 1.000) / factor_ajuste` (10¹¹, 10⁶ o 1). Luego `valor_usd_equiv_2024 = valor_bs_actual / tasa_cierre_2024`.

5. **Presentación**  
   - En informes y dashboard: mostrar **valor original** (con etiqueta de unidad: Bs.F, Bs.S, Bs., etc.) y **valor USD** (indicando si se usó tasa cierre o promedio cuando aplique).

---

## 10. Archivos de datos

| Archivo | Contenido |
|--------|-----------|
| `data/audit/seguro_en_cifras/variables/tasa_cambio_anual.csv` | Tasas únicas por año (1999–2013 y respaldo). |
| `data/audit/seguro_en_cifras/variables/tasa_cambio_bcv_2014_2024.csv` | Tasas BCV cierre y promedio 2014–2024. |
| `data/audit/seguro_en_cifras/variables/README_TASAS_Y_RECONVERSION.md` | Resumen de reconversiones y uso de tasas. |

---

## 11. Referencia

- *Análisis Técnico de la Evolución Cambiaria y Normalización Estadística del Sector Asegurador Venezolano (2014-2024)* (documento interno / investigación citada).
- BCV: [Tipo de cambio de referencia](https://www.bcv.org.ve/estadisticas/tipo-de-cambio-de-referencia), [Series históricas](https://www.bcv.org.ve/estadisticas/cuentas-nacionales-series-historicas).
- NIC 21 (Efectos de las variaciones en las tasas de cambio), NIC 29 (Información financiera en economías hiperinflacionarias).
