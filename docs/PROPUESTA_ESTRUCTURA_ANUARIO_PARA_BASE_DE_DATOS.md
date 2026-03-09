# Propuesta: Estructura para llevar el anuario “Seguro en Cifras” a base de datos (local y Supabase)

## 1. Qué hacer con los archivos en `verificadas/`

- **Mantener los CSV en `data/staged/2023/verificadas/`** (y en el futuro `data/staged/{año}/verificadas/`).
- Esos archivos son la **fuente de verdad** extraída del PDF; no se renombran ni se mueven.
- La base de datos (local o Supabase) se **alimenta desde esos CSV**, no los reemplaza. Así siempre puedes re-generar la BD desde los mismos archivos.

---

## 2. Objetivo

- Tener una **estructura lista para “vaciar” en Supabase** (PostgreSQL).
- Empezar con una **base local** (por ejemplo SQLite) en otra carpeta para:
  - Probar esquema y carga sin tocar la nube.
  - Revisar datos y consultas antes de subir a Supabase.

---

## 3. Estructura de carpetas propuesta

```
data/
├── staged/                        # Sin cambios
│   └── 2023/
│       └── verificadas/           # 100 CSV del anuario 2023 (fuente de verdad)
│
├── db/                            # NUEVO: todo lo relacionado con la BD del anuario
│   ├── local/                     # Base de datos local (SQLite)
│   │   ├── anuario.db             # Una BD por año o una sola con tabla "anio"
│   │   └── manifest_carga.json    # Fecha de carga, archivos cargados, conteo filas
│   │
│   ├── schema/                    # DDL reutilizable (PostgreSQL / Supabase)
│   │   ├── 001_schema_anuario.sql # CREATE SCHEMA anuario; tablas por cuadro
│   │   └── 002_rls_anuario.sql    # (opcional) RLS para schema anuario
│   │
│   └── README.md                  # Cómo usar: crear BD local, cargar CSV, subir a Supabase
│
└── replica_db/                    # Ya existe: réplica tablas “operativas” (entities, primas_mensuales…)
```

- **`data/staged/{año}/verificadas/`**: se deja tal cual; solo se lee.
- **`data/db/`**: agrupa todo lo de “base de datos del anuario”: local + DDL para Supabase.
- **`data/replica_db/`**: sigue siendo la réplica de las tablas actuales del dashboard (entities, primas_mensuales, etc.); el anuario es un bloque aparte.

---

## 4. Estrategia de tablas (anuario en Supabase)

- **Esquema dedicado en PostgreSQL:** por ejemplo `anuario` (o `seguro_en_cifras`).
- **Una tabla por cuadro:** cada CSV se mapea a una tabla, con nombre estable:
  - Ej.: `anuario.cuadro_03_primas_por_ramo`, `anuario.cuadro_54_balance_condensado_medicina_prepagada`.
- **Columna `anio`:** en cada tabla, columna `anio INTEGER` (ej. 2023) para poder tener varios años en la misma tabla sin mezclar con otros esquemas.
- **Columnas de datos:** las mismas que el CSV (normalizadas a nombres válidos en SQL: sin espacios, sin `%` → p. ej. `pct`). El DDL se puede generar a partir de los encabezados de los CSV.

Ventajas:
- Consultas directas por cuadro.
- Fácil cargar solo un año o añadir años nuevos.
- Mismo diseño en SQLite (local) y en PostgreSQL (Supabase).

---

## 5. Base local (SQLite) en `data/db/local/`

- **Un archivo:** por ejemplo `anuario.db`.
- **Tablas:** mismas que en Supabase (mismo nombre lógico), con columna `anio`.
- **Uso:**
  1. Script que lee la lista de CSV desde `verificar_indice_anuario` (misma fuente que las reglas).
  2. Por cada CSV: crea la tabla si no existe (inferiendo tipos desde el CSV o usando TEXT para simplicidad) y hace `INSERT`.
  3. Escribe `manifest_carga.json` (archivos cargados, filas por tabla, checksum opcional).
- Así puedes:
  - Validar que todos los cuadros cargan bien.
  - Hacer consultas y pruebas en local antes de subir a Supabase.

---

## 6. Flujo sugerido

| Paso | Acción |
|------|--------|
| 1 | Dejar los 100 CSV en `data/staged/2023/verificadas/` (sin mover). |
| 2 | Crear `data/db/`, `data/db/local/`, `data/db/schema/`. |
| 3 | Script “crear BD local”: crea `data/db/local/anuario.db`, crea tablas (una por cuadro), carga todos los CSV del año indicado, escribe `manifest_carga.json`. |
| 4 | (Opcional) Script que genere DDL PostgreSQL a partir de los CSV (o de un registro de “plantillas” por cuadro) y lo guarde en `data/db/schema/`. |
| 5 | Cuando la carga local esté validada: script o proceso que lea desde `data/db/local/` (o desde los CSV) y cargue a Supabase (schema `anuario`, mismas tablas). |

---

## 7. Resumen

- **CSV en `verificadas/`:** se quedan ahí; son la fuente de verdad.
- **Nueva estructura:** `data/db/` con:
  - **local/**: SQLite para probar en local.
  - **schema/**: DDL PostgreSQL listo para Supabase.
- **Tablas:** una por cuadro, con `anio`; nombres alineados con los CSV.
- **Carga:** primero local (SQLite), luego Supabase (mismo esquema lógico), sin duplicar ni sustituir los CSV.

Si quieres, el siguiente paso puede ser: (1) crear las carpetas y un `README` en `data/db/`, y (2) un script que cree `anuario.db` y cargue los 100 CSV desde `verificadas/` con la lista del índice.
