# Base de datos – Anuarios "Seguro en Cifras"

**Alcance:** Todo lo que está en esta carpeta (`data/db/`) y en el schema **`anuario`** (PostgreSQL) es **exclusivamente para los anuarios** "Seguro en Cifras" (PDF → CSV extraídos en `data/staged/{año}/verificadas/`). Otras fuentes de información (por ejemplo **Excel**) tendrán su propia estructura, schema y documentación; no se mezclan aquí. Ver `docs/FUENTES_DE_DATOS.md` para el mapa de fuentes del proyecto.

---

Estructura para tener los cuadros del anuario en **réplica local** (SQLite o PostgreSQL) y en **Supabase** (PostgreSQL). La misma estructura lógica: dimensiones (cuadros) + 23 tablas temáticas con PK, FK e índices.

- **Fuente de datos (solo anuarios):** los CSV en `data/staged/{año}/verificadas/` (no se mueven ni se borran).
- **Propuesta y mapa ER:** `docs/PROPUESTA_REORGANIZACION_OPCION_2.md`, `docs/MAPA_ENTIDAD_RELACION_ANUARIO.md`.

---

## Carpetas

| Carpeta | Contenido |
|--------|-----------|
| `local/` | Bases SQLite: `anuario.db` (100 tablas crudas, script anterior) y/o `anuario_tematico.db` (23 tablas temáticas). `manifest_carga.json` si aplica. |
| `schema/` | DDL **PostgreSQL** para Supabase (y para réplica local si usas Postgres). |
| `schema/sqlite/` | DDL **SQLite** para réplica local con la misma estructura (tablas con prefijo `anuario_`). |

---

## DDL: estructura física (Supabase y réplica local)

### PostgreSQL (Supabase y réplica local con Postgres)

Ejecutar en este orden en el **SQL Editor** de Supabase (o en una base PostgreSQL local):

1. **`schema/001_anuario_dimensiones.sql`**  
   Crea el schema `anuario`, la tabla `anuario.cuadros` y el seed de cuadros 3 a 58.

2. **`schema/002_anuario_tablas_tematicas.sql`**  
   Crea las 23 tablas temáticas con `id`, `anio`, `cuadro_id` (FK a `anuario.cuadros`), columnas de dato e índices.

3. **`schema/003_anuario_rls.sql`**  
   Habilita RLS y políticas de lectura (anon/authenticated) para Supabase. Opcional en réplica local.

Después de ejecutar 001 y 002 (y 003 en Supabase), la base queda con la estructura lista para cargar datos desde los CSV (ETL por implementar).

### SQLite (réplica local en archivo)

Para tener la **misma estructura** en un archivo SQLite (`local/anuario_tematico.db`):

```bash
python scripts/crear_replica_local_anuario_tematico.py
```

O, si tienes `sqlite3` instalado:  
`sqlite3 data/db/local/anuario_tematico.db < data/db/schema/sqlite/001_anuario_local.sql`

- Crea la tabla `anuario_cuadros` (y seed) y las 23 tablas con prefijo `anuario_`.
- Equivalente a 001 + 002 en PostgreSQL pero sin schema (prefijo en nombres) y con `datos` en TEXT en lugar de JSONB.

---

## ¿Qué base usar dónde?

| Uso | Base | DDL |
|-----|------|-----|
| **Subir a Supabase** | PostgreSQL (Supabase) | `001_anuario_dimensiones.sql` + `002_anuario_tablas_tematicas.sql` + `003_anuario_rls.sql` |
| **Réplica local (PostgreSQL)** | Postgres local | Los mismos 001 y 002 (003 opcional) |
| **Réplica local (archivo)** | SQLite `local/anuario_tematico.db` | `schema/sqlite/001_anuario_local.sql` |

La estructura (tablas, columnas, relaciones) es la misma; solo cambia el motor y, en SQLite, el uso de prefijo `anuario_` y TEXT para lo que en Postgres es JSONB.

---

## Carga de datos (ETL)

- El script **`scripts/load_anuario_to_local_db.py`** sigue cargando los 100 CSV en **100 tablas crudas** en `local/anuario.db` (una tabla por CSV). No usa aún las 23 tablas temáticas.
- Para llenar las **23 tablas temáticas** (local o Supabase) hace falta un ETL que lea los CSV, aplique el mapeo de `docs/PROPUESTA_REORGANIZACION_OPCION_2.md` e inserte en las tablas correspondientes (por implementar).

---

## Resumen

- **Estructura definida a nivel físico:** sí, en `schema/` (PostgreSQL) y `schema/sqlite/` (SQLite).
- **Subir a Supabase:** ejecutar 001, 002 y 003 en el SQL Editor del proyecto.
- **Réplica local:** misma estructura con 001+002 en Postgres local o con `schema/sqlite/001_anuario_local.sql` en SQLite.
