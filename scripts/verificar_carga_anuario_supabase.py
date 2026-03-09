# scripts/verificar_carga_anuario_supabase.py
"""
Comprueba que los datos del anuario se cargaron en Supabase de forma completa.
Compara conteos por cuadro_id: CSV origen (verificadas) vs Supabase (schema anuario).
Solo hace SELECT en Supabase; sirve con la clave anon (SUPABASE_KEY).
Uso: python scripts/verificar_carga_anuario_supabase.py [--year 2023]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_env = ROOT / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

from config.settings import DATA_STAGED, SUPABASE_URL, SUPABASE_KEY


def _verificadas_dir(year: int) -> Path:
    return DATA_STAGED / str(year) / "verificadas"


def _expected_balances_from_csv(year: int) -> tuple[Counter[str], int]:
    """Cuenta filas por cuadro_id que el ETL cargaría desde CSV. Devuelve (conteo por cuadro, total)."""
    from scripts.etl_anuario_a_supabase import load_balances_condensados
    verificadas = _verificadas_dir(year)
    if not verificadas.exists():
        return Counter(), 0
    rows = load_balances_condensados(verificadas, year)
    by_cuadro = Counter(r["cuadro_id"] for r in rows)
    return by_cuadro, len(rows)


def _expected_listados_from_csv(year: int) -> tuple[Counter[str], int]:
    """Cuenta filas por cuadro_id que el ETL cargaría desde CSV. Devuelve (conteo por cuadro, total)."""
    from scripts.etl_anuario_a_supabase import load_listados_empresas
    verificadas = _verificadas_dir(year)
    if not verificadas.exists():
        return Counter(), 0
    rows = load_listados_empresas(verificadas, year)
    by_cuadro = Counter(r["cuadro_id"] for r in rows)
    return by_cuadro, len(rows)


def _expected_capital_garantia_from_csv(year: int) -> int:
    """Cuenta filas que el ETL cargaría en capital_garantia_por_empresa (Cuadro 2)."""
    from scripts.etl_anuario_a_supabase import load_capital_garantia_por_empresa
    verificadas = _verificadas_dir(year)
    if not verificadas.exists():
        return 0
    rows = load_capital_garantia_por_empresa(verificadas, year)
    return len(rows)


def _fetch_supabase_counts(sb, table: str, year: int) -> tuple[Counter[str], int]:
    """Trae todos los registros de la tabla para el año y cuenta por cuadro_id. Devuelve (conteo por cuadro, total)."""
    all_data = []
    offset = 0
    page_size = 500
    while True:
        r = sb.table(table).select("cuadro_id").eq("anio", year).range(offset, offset + page_size - 1).execute()
        chunk = r.data or []
        if not chunk:
            break
        all_data.extend(chunk)
        if len(chunk) < page_size:
            break
        offset += page_size
    by_cuadro = Counter(row.get("cuadro_id") for row in all_data if row.get("cuadro_id"))
    return by_cuadro, len(all_data)


def run_verificacion(year: int) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[Verificación] Configure SUPABASE_URL y SUPABASE_KEY en .env")
        return False

    try:
        from src.db import get_supabase_anuario_client
        sb = get_supabase_anuario_client()
    except Exception as e:
        print(f"[Verificación] Error cliente: {e}")
        return False

    if sb is None:
        print("[Verificación] No se pudo conectar al schema anuario.")
        return False

    all_ok = True

    # --- Catálogo cuadros ---
    print("\n--- anuario.cuadros (catálogo) ---")
    try:
        r = sb.table("cuadros").select("cuadro_id", count="exact").execute()
        n = len(r.data or [])
        total = getattr(r, "count", None) if hasattr(r, "count") else None
        total = total if total is not None else n
        print(f"  Total: {total} registros (esperado: 58 cuadros del seed, incl. 1 y 2)")
    except Exception as e:
        print(f"  ERROR — {e}")
        all_ok = False

    # --- Balances condensados: CSV vs Supabase por cuadro ---
    print(f"\n--- anuario.balances_condensados (año {year}) ---")
    exp_bal, exp_bal_total = _expected_balances_from_csv(year)
    try:
        act_bal, act_bal_total = _fetch_supabase_counts(sb, "balances_condensados", year)
    except Exception as e:
        print(f"  ERROR al leer Supabase — {e}")
        act_bal, act_bal_total = Counter(), 0
        all_ok = False

    cuadros_bal = sorted(set(exp_bal.keys()) | set(act_bal.keys()))
    for c in cuadros_bal:
        e, a = exp_bal.get(c, 0), act_bal.get(c, 0)
        ok = e == a
        if not ok:
            all_ok = False
        sym = "OK" if ok else "DIF"
        print(f"  Cuadro {c}: CSV={e}  Supabase={a}  [{sym}]")
    print(f"  Total CSV: {exp_bal_total}  Total Supabase: {act_bal_total}  [{'OK' if exp_bal_total == act_bal_total else 'DIF'}]")
    if exp_bal_total != act_bal_total:
        all_ok = False

    # --- Listados empresas: CSV vs Supabase por cuadro ---
    print(f"\n--- anuario.listados_empresas (año {year}) ---")
    exp_list, exp_list_total = _expected_listados_from_csv(year)
    try:
        act_list, act_list_total = _fetch_supabase_counts(sb, "listados_empresas", year)
    except Exception as e:
        print(f"  ERROR al leer Supabase — {e}")
        act_list, act_list_total = Counter(), 0
        all_ok = False

    cuadros_list = sorted(set(exp_list.keys()) | set(act_list.keys()))
    for c in cuadros_list:
        e, a = exp_list.get(c, 0), act_list.get(c, 0)
        ok = e == a
        if not ok:
            all_ok = False
        sym = "OK" if ok else "DIF"
        print(f"  Cuadro {c}: CSV={e}  Supabase={a}  [{sym}]")
    print(f"  Total CSV: {exp_list_total}  Total Supabase: {act_list_total}  [{'OK' if exp_list_total == act_list_total else 'DIF'}]")
    if exp_list_total != act_list_total:
        all_ok = False

    # --- Capital y garantía por empresa (Cuadro 2) ---
    print(f"\n--- anuario.capital_garantia_por_empresa (año {year}) ---")
    exp_cg = _expected_capital_garantia_from_csv(year)
    try:
        _, act_cg_total = _fetch_supabase_counts(sb, "capital_garantia_por_empresa", year)
    except Exception as e:
        print(f"  ERROR al leer Supabase — {e}")
        act_cg_total = 0
        all_ok = False
    cg_ok = exp_cg == act_cg_total
    if not cg_ok:
        all_ok = False
    print(f"  CSV={exp_cg}  Supabase={act_cg_total}  [{'OK' if cg_ok else 'DIF'}]")

    return all_ok


def main():
    p = argparse.ArgumentParser(description="Verifica carga completa del anuario en Supabase (CSV vs Supabase por cuadro).")
    p.add_argument("--year", type=int, default=2023, help="Año a comprobar")
    args = p.parse_args()

    print(f"Verificación completa schema anuario (año {args.year})")
    ok = run_verificacion(args.year)
    print("\n" + ("Carga COMPLETA y coherente." if ok else "Hay diferencias o errores — revisar."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
