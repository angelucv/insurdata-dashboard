# scripts/preparar_publicacion.py
"""
Prepara la base de datos en Supabase y ejecuta todos los ETL necesarios para que
el dashboard tenga todas las salidas listas para publicación.

Pasos:
  1. Ejecutar migraciones 006 y 007 en Supabase (si SUPABASE_DB_URL está configurado).
  2. Ejecutar el ETL completo del anuario (balances, listados, capital/garantía, primas,
     estados de resultado, gestión general, siniestros, reservas).
  3. Ejecutar la verificación de carga (conteos CSV vs Supabase).

Uso:
  python scripts/preparar_publicacion.py [--year 2023]

Requisitos:
  - .env con SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (para el ETL).
  - Opcional: SUPABASE_DB_URL para ejecutar 006 y 007 desde este script (si no,
    ejecute manualmente 006 y 007 en el SQL Editor de Supabase).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_env = ROOT / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

from config.settings import DATA_DB_SCHEMA, SUPABASE_DB_URL


def run_migraciones() -> bool:
    """Ejecuta 006 y 007 en Supabase si SUPABASE_DB_URL está configurado."""
    if not SUPABASE_DB_URL or not SUPABASE_DB_URL.strip():
        print("[Migraciones] SUPABASE_DB_URL no configurado.")
        print("              Ejecute en Supabase SQL Editor:")
        print("              - data/db/schema/006_anuario_cuadros_1_2_y_capital_garantia.sql")
        print("              - data/db/schema/007_anuario_siniestros_por_ramo_empresa.sql")
        return False

    try:
        import psycopg2
        conn = psycopg2.connect(SUPABASE_DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        ok = True
        for nombre, archivo in [
            ("006 (cuadros 1/2 + capital_garantia)", "006_anuario_cuadros_1_2_y_capital_garantia.sql"),
            ("007 (siniestros por ramo y empresa)", "007_anuario_siniestros_por_ramo_empresa.sql"),
        ]:
            sql_path = DATA_DB_SCHEMA / archivo
            if not sql_path.exists():
                print(f"[Migraciones] No encontrado: {sql_path}")
                ok = False
                continue
            sql = sql_path.read_text(encoding="utf-8")
            try:
                cur.execute(sql)
                print(f"[Migraciones] {nombre} ejecutado correctamente.")
            except Exception as e:
                print(f"[Migraciones] Error en {nombre}: {e}")
                ok = False
        cur.close()
        conn.close()
        return ok
    except ImportError:
        print("[Migraciones] psycopg2 no instalado. Ejecute las migraciones 006 y 007 en el SQL Editor de Supabase.")
        return False
    except Exception as e:
        print(f"[Migraciones] Error de conexión: {e}")
        return False


def main():
    p = argparse.ArgumentParser(description="Preparar Supabase y ETL para publicación del dashboard")
    p.add_argument("--year", type=int, default=2023, help="Año del anuario a cargar")
    p.add_argument("--skip-migraciones", action="store_true", help="No ejecutar 006/007 (ya aplicadas)")
    args = p.parse_args()

    print("=== Preparación para publicación del dashboard anuario ===\n")

    if not args.skip_migraciones:
        print("--- Paso 1: Migraciones 006 y 007 ---\n")
        run_migraciones()
        print()
    else:
        print("--- Paso 1: Migraciones omitidas (--skip-migraciones) ---\n")

    print("--- Paso 2: ETL completo ---\n")
    from scripts.etl_anuario_a_supabase import run_etl
    ok_etl = run_etl(args.year)

    print("\n--- Paso 3: Verificación de carga ---\n")
    from scripts.verificar_carga_anuario_supabase import run_verificacion
    ok_ver = run_verificacion(args.year)

    print("\n" + "=" * 50)
    if ok_etl and ok_ver:
        print("Listo para publicación: ETL y verificación OK.")
        print("Ejecute el dashboard (streamlit run app.py) y compruebe todas las pestañas.")
        sys.exit(0)
    if not ok_etl:
        print("El ETL terminó con errores. Revise SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env")
    if not ok_ver:
        print("La verificación encontró diferencias. Revise los conteos anteriores.")
    sys.exit(1)


if __name__ == "__main__":
    main()
