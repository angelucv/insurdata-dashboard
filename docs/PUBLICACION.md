# Publicación del dashboard Anuario Seguro en Cifras

Pasos para actualizar la base de datos en Supabase y ejecutar los ETL que alimentan todas las salidas del dashboard antes de publicar.

---

## 1. Base de datos en Supabase

### Si es la primera vez (instalación desde cero)

En el **SQL Editor** de Supabase, ejecute en este orden:

| Orden | Archivo | Descripción |
|-------|---------|-------------|
| 1 | `data/db/schema/001_anuario_dimensiones.sql` | Catálogo de cuadros (cuadros 1 a 58) |
| 2 | `data/db/schema/002_anuario_tablas_tematicas.sql` | Tablas temáticas (primas, siniestros, reservas, balances, estados, etc.) |
| 3 | `data/db/schema/003_anuario_rls.sql` | Row Level Security y políticas de lectura |
| 4 | `data/db/schema/004_anuario_exponer_api.sql` | Exponer esquema `anuario` en la API (Data API) |
| 5 | `data/db/schema/005_anuario_service_role_escritura.sql` | Permisos de escritura para ETL (service_role) |
| 6 | `data/db/schema/006_anuario_cuadros_1_2_y_capital_garantia.sql` | Cuadros 1 y 2 + tabla `capital_garantia_por_empresa` |
| 7 | `data/db/schema/007_anuario_siniestros_por_ramo_empresa.sql` | Tabla `siniestros_por_ramo_empresa` (Cuadro 7) |

### Si ya tiene 001 a 005 aplicados

Solo ejecute:

- `data/db/schema/006_anuario_cuadros_1_2_y_capital_garantia.sql`
- `data/db/schema/007_anuario_siniestros_por_ramo_empresa.sql`

---

## 2. Variables de entorno (.env)

En la raíz del proyecto, configure:

```env
SUPABASE_URL=https://su-proyecto.supabase.co
SUPABASE_KEY=eyJ...   # clave anon (lectura desde el dashboard)
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # clave service_role (solo para ETL, no exponer en front)
```

Opcional, para que el script ejecute las migraciones 006 y 007 desde su máquina:

```env
SUPABASE_DB_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

(La obtiene en Supabase: **Dashboard > Project Settings > Database > Connection string URI**.)

---

## 3. Ejecutar actualización y ETL (todo en uno)

Desde la raíz del proyecto:

```bash
python scripts/preparar_publicacion.py --year 2023
```

Este script:

1. **Migraciones:** Ejecuta 006 y 007 en Supabase (si `SUPABASE_DB_URL` está en `.env`). Si no, debe ejecutarlos a mano en el SQL Editor.
2. **ETL:** Carga todos los datos del anuario (balances, listados, capital/garantía, primas, estados de resultado, gestión general, siniestros por ramo y por empresa, reservas) desde `data/staged/2023/verificadas/`.
3. **Verificación:** Compara conteos CSV vs Supabase y muestra OK o diferencias.

Para omitir migraciones (por ejemplo si ya las aplicó):

```bash
python scripts/preparar_publicacion.py --year 2023 --skip-migraciones
```

---

## 4. Tablas que alimentan el dashboard

| Tabla | Contenido | Pestañas del dashboard |
|-------|-----------|-------------------------|
| `cuadros` | Catálogo de cuadros | Catálogo de cuadros |
| `balances_condensados` | Balances por sector | Inicio, Balances |
| `listados_empresas` | Empresas autorizadas por sector | Inicio, Listados y empresas |
| `capital_garantia_por_empresa` | Capital y garantía (Cuadro 2) | Listados y empresas |
| `primas_por_ramo` | Cuadros 3, 5-A, 5-B, 5-C | Primas |
| `primas_por_ramo_empresa` | Cuadro 4 | Primas |
| `estados_ingresos_egresos` | 25-A/B, 41-A/B, 48, 55-A/B | Estados de resultado |
| `gestion_general` | Cuadro 26 | Indicadores y gestión |
| `siniestros_por_ramo` | Cuadros 6, 8-A, 8-B, 8-C | Siniestros |
| `siniestros_por_ramo_empresa` | Cuadro 7 | Siniestros |
| `reservas_tecnicas_agregado` | Cuadro 9 | Reservas |
| `reservas_prima_por_ramo` | Cuadro 10 | Reservas |
| `reservas_prestaciones_por_ramo` | Cuadro 15 | Reservas |

---

## 5. Publicar el aplicativo

1. Asegúrese de que **Exposed schemas** en Supabase incluya `anuario` (Data API > Settings).
2. El dashboard usa **SUPABASE_URL** y **SUPABASE_KEY** (anon) para leer; no exponga la service_role en el front.
3. Ejecute el dashboard en local para comprobar:  
   `streamlit run app.py`
4. Para publicar en Streamlit Cloud (o similar), configure las **secrets** con `SUPABASE_URL` y `SUPABASE_KEY` (anon). No añada la service_role como secret del dashboard.

---

## 6. Ampliación futura

- Añadir más años: coloque los CSV en `data/staged/[año]/verificadas/` y ejecute `preparar_publicacion.py --year [año]`.
- Nuevos cuadros: defina la tabla en el esquema, cree migración si aplica, añada la carga en `scripts/etl_anuario_a_supabase.py` y la lectura en el dashboard.
