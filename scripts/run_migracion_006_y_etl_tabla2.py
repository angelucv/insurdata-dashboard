# scripts/run_migracion_006_y_etl_tabla2.py
"""
Ejecuta todo lo necesario para la tabla capital_garantia_por_empresa (Cuadro 2):
1. Migración 006 en Supabase (crea la tabla si existe SUPABASE_DB_URL).
2. ETL (carga balances, listados, capital_garantia).
3. Verificación de la carga.

Uso: python scripts/run_migracion_006_y_etl_tabla2.py [--year 2023]

Si SUPABASE_DB_URL no está en .env, la migración se omite (ejecute 006 en el SQL Editor de Supabase).
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


def run_migracion_006() -> bool:
    """Ejecuta 006_anuario_cuadros_1_2_y_capital_garantia.sql si hay SUPABASE_DB_URL."""
    if not SUPABASE_DB_URL or not SUPABASE_DB_URL.strip():
        print("[Migración] SUPABASE_DB_URL no configurado. Omitiendo migración 006.")
        print("            Para crear la tabla desde aqui, anada SUPABASE_DB_URL en .env (Dashboard > Database > Connection string URI).")
        return False

    sql_file = DATA_DB_SCHEMA / "006_anuario_cuadros_1_2_y_capital_garantia.sql"
    if not sql_file.exists():
        print(f"[Migración] No encontrado: {sql_file}")
        return False

    sql = sql_file.read_text(encoding="utf-8")
    # Quitar comentarios de una línea y ejecutar por bloques (PostgreSQL acepta múltiples sentencias)
    try:
        import psycopg2
        conn = psycopg2.connect(SUPABASE_DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute(sql)
            print("[Migración] 006 ejecutado correctamente (tabla capital_garantia_por_empresa creada/actualizada).")
        finally:
            cur.close()
            conn.close()
        return True
    except Exception as e:
        print(f"[Migración] Error ejecutando 006: {e}")
        return False


def main():
    p = argparse.ArgumentParser(description="Migración 006 + ETL + verificación para Cuadro 2")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()

    print("=== Paso 1: Migración 006 (tabla capital_garantia_por_empresa) ===\n")
    run_migracion_006()

    print("\n=== Paso 2: ETL anuario ===\n")
    from scripts.etl_anuario_a_supabase import run_etl
    ok_etl = run_etl(args.year)

    print("\n=== Paso 3: Verificación ===\n")
    from scripts.verificar_carga_anuario_supabase import run_verificacion
    ok_ver = run_verificacion(args.year)

    if ok_etl and ok_ver:
        print("\nTodo correcto: ETL y verificación OK.")
        sys.exit(0)
    if not ok_ver:
        print("\nVerificación con diferencias o errores.")
        sys.exit(1)
    sys.exit(0 if ok_etl else 1)


if __name__ == "__main__":
    main()
