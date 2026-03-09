# Fuentes de datos del proyecto

Este documento deja claro **qué datos pertenecen a qué fuente** y evita mezclar anuarios (PDF) con otras fuentes (por ejemplo Excel).

---

## 1. Anuarios "Seguro en Cifras" (PDF → CSV)

| Aspecto | Detalle |
|--------|---------|
| **Fuente** | PDF del anuario anual "Seguro en Cifras" (ej. 2023). |
| **Producto** | 100 CSV en `data/staged/{año}/verificadas/` (cuadros 3 a 58). |
| **Base de datos** | Schema **`anuario`** (PostgreSQL) o tablas con prefijo **`anuario_`** (SQLite). Dimensiones: `anuario.cuadros`. 23 tablas temáticas. |
| **Documentación** | `data/db/README.md`, `docs/PROPUESTA_REORGANIZACION_OPCION_2.md`, `docs/MAPA_ENTIDAD_RELACION_ANUARIO.md`, `docs/REGLAS_VALIDACION_SEGURO_EN_CIFRAS.md`. |
| **Scripts** | Extracción/validación en `scripts/guardar_tablas_verificadas_2023.py`, `scripts/verificar_*.py`. Carga local: `scripts/load_anuario_to_local_db.py`, `scripts/crear_replica_local_anuario_tematico.py`. |

Todo lo que hable de "cuadros", "anuario", "Seguro en Cifras" o de los CSV en `verificadas/` se refiere **solo** a esta fuente.

---

## 2. Otras fuentes (Excel, etc.)

| Aspecto | Detalle |
|--------|---------|
| **Fuente** | Otras publicaciones o reportes (por ejemplo archivos Excel). |
| **Producto** | Por definir (carpetas, formatos, tablas). |
| **Base de datos** | Estructura y schema **separados** de `anuario`. Se recomienda otro schema (ej. `excel` o por nombre de fuente) o su propia documentación. |
| **Documentación** | Por definir cuando se incorpore cada fuente. |

Al añadir una nueva fuente (p. ej. Excel):

- Definir dónde se almacenan los archivos crudos y los derivados.
- Definir schema/tablas propios (no reutilizar las tablas del anuario).
- Documentar en este archivo o en un doc específico de esa fuente.

---

## 3. Resumen

- **Anuarios (PDF):** schema `anuario`, CSV en `staged/{año}/verificadas/`, 23 tablas temáticas, docs y scripts ya referenciados arriba.
- **Otras fuentes (Excel, etc.):** estructura y documentación propias; no se mezclan con el schema ni con la lógica de los anuarios.

Así se mantiene claro que **todo lo de `data/db/` y schema `anuario` es referente a los anuarios**, y el resto de fuentes queda explícitamente separado.
