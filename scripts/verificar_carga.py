# scripts/verificar_carga.py
"""Verificación post-carga: compara datos en Supabase con lo esperado según los Excel de origen."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_RAW
from src.db import get_supabase_client
from src.etl.sudeaseg_to_supabase import (
    _MES_SHEET,
    _year_from_path,
    load_primas_netas_por_empresa_excel,
    normalize_entity_name,
    get_or_create_entity_id,
)


def contar_filas_esperadas_primas_netas(path: Path) -> int:
    """Cuenta filas que deberían cargarse de un Excel 'primas netas cobradas por empresa'."""
    name = path.name.lower()
    if "20" not in name:
        return 0
    import re
    year_match = re.search(r"20\d{2}", name)
    if not year_match:
        return 0
    year = int(year_match.group(0))
    total = 0
    try:
        xl = pd.ExcelFile(path)
    except Exception:
        return 0
    for sheet in xl.sheet_names:
        if sheet.lower().strip() not in _MES_SHEET:
            continue
        try:
            df = pd.read_excel(path, sheet_name=sheet, header=9)
        except Exception:
            continue
        if df.empty or len(df.columns) < 3:
            continue
        col_empresa = None
        for c in df.columns:
            if "empresa" in str(c).lower() or "seguros" in str(c).lower():
                col_empresa = c
                break
        if col_empresa is None:
            continue
        for _, row in df.iterrows():
            emp = row.get(col_empresa)
            if pd.isna(emp) or not str(emp).strip() or "total" in str(emp).lower():
                continue
            total += 1
    return total


def verificar_supabase_vs_excel(raw_dir: Path) -> dict:
    """
    Compara: para cada Excel de primas netas, cuenta filas esperadas y filas en Supabase
    para los mismos periodo (año del archivo). Devuelve resumen de coincidencias.
    """
    sb = get_supabase_client()
    if not sb:
        return {"error": "Supabase no configurado", "checks": []}
    resultados = []
    archivos = list(raw_dir.rglob("primas*netas*cobradas*empresa*.xlsx")) + list(raw_dir.rglob("primas*cobradas*empresa*.xlsx"))
    archivos = [p for p in archivos if "primas" in p.name.lower() and "empresa" in p.name.lower()]
    for path in archivos[:15]:
        esperado = contar_filas_esperadas_primas_netas(path)
        year = _year_from_path(path)
        if not year:
            continue
        error_msg = ""
        try:
            r = sb.table("primas_mensuales").select("id").gte("periodo", f"{year}-01-01").lte("periodo", f"{year}-12-31").limit(5000).execute()
            en_bd = len(r.data or [])
            if hasattr(r, "count") and r.count is not None:
                en_bd = r.count
        except Exception as e:
            en_bd = -1
            error_msg = str(e)
        ok = (esperado <= en_bd or abs(esperado - en_bd) < 100) if en_bd >= 0 else False
        resultados.append({
            "archivo": path.name,
            "esperado": esperado,
            "en_supabase": en_bd if en_bd >= 0 else error_msg,
            "ok": ok,
        })
    return {"checks": resultados, "resumen": f"{sum(1 for x in resultados if x.get('ok'))}/{len(resultados)} archivos coherentes"}


def main():
    raw_dir = DATA_RAW
    print("Verificando consistencia Excel vs Supabase...")
    out = verificar_supabase_vs_excel(raw_dir)
    if "error" in out:
        print(out["error"])
        return
    for c in out["checks"]:
        status = "OK" if c.get("ok") else "REVISAR"
        print(f"  [{status}] {c['archivo']}: esperado ~{c['esperado']} filas, Supabase: {c['en_supabase']}")
    print("\n", out.get("resumen", ""))


if __name__ == "__main__":
    main()
