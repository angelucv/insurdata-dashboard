# Pasos: cargar esquema anuario en Supabase y mostrarlo en Streamlit

Guía para hacer una prueba completa: **esquema en Supabase** → **carga de datos** → **app Streamlit** mostrando la información del anuario.

---

## 1. Cargar el esquema en Supabase

1. **Abrir el SQL Editor** de tu proyecto en [Supabase Dashboard](https://supabase.com/dashboard) → tu proyecto → SQL Editor.

2. **Ejecutar en este orden** (copiar y ejecutar el contenido de cada archivo):
   - `data/db/schema/001_anuario_dimensiones.sql`  
     → Crea schema `anuario` y tabla `anuario.cuadros` (con seed de cuadros 1 a 58).
   - `data/db/schema/002_anuario_tablas_tematicas.sql`  
     → Crea las tablas temáticas (incl. `listados_empresas`, `capital_garantia_por_empresa` para Cuadros 1 y 2).
   - `data/db/schema/003_anuario_rls.sql`  
     → Habilita RLS y políticas de lectura.
   - `data/db/schema/004_anuario_exponer_api.sql`  
     → Da permisos para que la API pueda leer el schema `anuario`.

3. **Exponer el schema en la API:**  
   En el Dashboard: **Settings** → **API** → sección **Exposed schemas**. Añadir **`anuario`** y guardar. Sin este paso, el cliente no podrá consultar las tablas del schema.

4. **Comprobar:** En **Table Editor**, si tu proyecto muestra otros schemas, deberías ver el schema **anuario** con las tablas (cuadros, balances_condensados, etc.). Si solo ves `public`, igualmente las tablas existen; el siguiente paso (carga de datos) confirmará que todo está bien.

---

## 2. Cargar datos de prueba (ETL mínimo)

Los CSV del anuario están en `data/staged/2023/verificadas/`. El ETL carga **balances_condensados**, **listados_empresas** (Cuadros 1, 39, 46, 53: seguro directo, reaseguro, financiadoras, medicina prepagada) y **capital_garantia_por_empresa** (Cuadro 2).

El ETL hace **DELETE** e **INSERT** en Supabase. Esos permisos no los tiene la clave **anon** (publishable); hace falta la clave **service_role** (secret).

1. En tu `.env` añade la clave secret de Supabase (Dashboard → Settings → API → Secret key):
   ```env
   SUPABASE_SERVICE_ROLE_KEY=tu_clave_secret_aquí
   ```
   (Sigue usando `SUPABASE_URL` y `SUPABASE_KEY` para la app; `SUPABASE_SERVICE_ROLE_KEY` solo para este script. No expongas la secret en el front.)

2. Desde la raíz del proyecto:
   ```bash
   python scripts/etl_anuario_a_supabase.py --year 2023
   ```

3. Verificar que se cargaron los datos (usa la clave anon; solo lectura):
   ```bash
   python scripts/verificar_carga_anuario_supabase.py --year 2023
   ```
   Debe mostrar conteos de `cuadros`, `balances_condensados`, `listados_empresas` y `capital_garantia_por_empresa`.

---

## 3. Conectar Streamlit y mostrar el anuario

1. **Variables de entorno:** En `.env` (o en el entorno donde ejecutes Streamlit) deben estar:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

2. **Arrancar la app:**
   ```bash
   streamlit run app.py
   ```
   (o el punto de entrada que uses, por ejemplo `Home.py` o `streamlit run .` según tu proyecto.)

3. **Ir a la página del anuario:** En el menú lateral de Streamlit debe aparecer una página tipo **"Anuario Seguro en Cifras"** (o **"4_Anuario_Seguro_En_Cifras"**). Ahí se muestra:
   - Catálogo de cuadros (tabla `anuario.cuadros`)
   - Balances condensados (por sector y año)
   - Listados de empresas (seguro directo Cuadro 1, reaseguro, financiadoras, medicina prepagada) y Capital y garantía por empresa (Cuadro 2)
   - Selector de año y de tabla para ver detalle

La app usa el **mismo Supabase** que el resto del dashboard; solo cambia que las consultas se hacen al schema **`anuario`** (mediante un cliente configurado con ese schema).

---

## 4. Resumen de orden

| Paso | Acción |
|------|--------|
| 1 | Ejecutar 001, 002, 003 y 004 en Supabase SQL Editor. |
| 2 | En Dashboard → Settings → API → Exposed schemas → añadir `anuario`. |
| 3 | Ejecutar `python scripts/etl_anuario_a_supabase.py --year 2023`. |
| 4 | Arrancar Streamlit y abrir la página del anuario. |

Si algo falla: revisar que el schema esté expuesto, que las variables de Supabase estén definidas y que el ETL haya terminado sin errores (revisar salida en consola).
