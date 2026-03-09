"""
Verificación de que los datos del año 2023 convertidos desde PDF (Boletín en Cifras)
fueron extraídos de manera correcta.

Compara:
- Estructura y legibilidad de los CSV generados desde PDF (_tables.csv).
- Conteo de celdas numéricas y filas con datos.
- Opcional: totales de referencia desde Excel 2023 para comparar.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

# Rutas: asumimos ejecución desde raíz del proyecto
try:
    from config.settings import BASE_DIR
    from config.audit_paths import DATA_AUDIT_BY_SOURCE
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_AUDIT_BY_SOURCE = BASE_DIR / "data" / "audit" / "by_source"

YEAR_VERIFY = 2023
# Nombres de mes en archivos Boletín (variantes: Ene, Abri, Marz, etc.)
MONTH_PATTERNS = [
    "ene", "feb", "marz", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic",
    "abri", "marzo", "junio", "julio", "agosto", "sept", "octubre", "noviembre", "diciembre",
]


def _normalize_filename_for_month(name: str) -> str | None:
    """Extrae mes del nombre de archivo (ej. Boletín en Cifras Ene 2023 -> ene)."""
    n = name.lower().replace("%20", " ").replace("_", " ")
    # 202023 puede ser 2020 o 2023; priorizamos 2023
    if "2023" not in n and "202023" not in n:
        return None
    for m in MONTH_PATTERNS:
        if m in n:
            return m[:3] if len(m) > 3 else m
    return None


def _parse_european_number(s: Any) -> float | None:
    """Convierte '1.868.606,33' -> 1868606.33."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip()
    if not t or t in ("-", "—", ""):
        return None
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _count_numeric_cells(df: pd.DataFrame) -> tuple[int, int, float | None]:
    """
    Cuenta celdas que se pueden interpretar como número (formato europeo).
    Devuelve (total_celdas_numericas, filas_con_al_menos_un_numero, suma_total_si_hay).
    """
    total_cells = 0
    rows_with_number = 0
    all_vals: list[float] = []
    for _, row in df.iterrows():
        row_has = False
        for v in row:
            x = _parse_european_number(v)
            if x is not None:
                total_cells += 1
                row_has = True
                all_vals.append(x)
        if row_has:
            rows_with_number += 1
    suma = sum(all_vals) if all_vals else None
    return total_cells, rows_with_number, suma


def _has_expected_headers(df: pd.DataFrame) -> bool:
    """Comprueba si aparece al menos uno de los encabezados típicos del boletín (Primas, Empresa, Miles)."""
    full_text = " ".join(str(c) for c in df.columns) + " " + " ".join(str(v) for v in df.values.ravel())[:2000]
    low = full_text.lower()
    return any(k in low for k in ("primas", "empresa", "miles", "resultado técnico", "asegurador"))


def verify_one_pdf_table_csv(path: Path) -> dict[str, Any]:
    """
    Verifica un único CSV extraído de PDF (Boletín 2023).
    Devuelve dict con: ok, filas, columnas, celdas_numericas, filas_con_datos, tiene_encabezados_esperados, error.
    """
    out = {
        "archivo": path.name,
        "ok": False,
        "filas": 0,
        "columnas": 0,
        "celdas_numericas": 0,
        "filas_con_datos": 0,
        "tiene_encabezados_esperados": False,
        "suma_numerica": None,
        "error": None,
    }
    try:
        df = pd.read_csv(path, encoding="utf-8-sig", on_bad_lines="warn", low_memory=False)
    except Exception as e:
        out["error"] = str(e)
        return out
    out["filas"], out["columnas"] = len(df), len(df.columns)
    cells, rows_data, suma = _count_numeric_cells(df)
    out["celdas_numericas"] = cells
    out["filas_con_datos"] = rows_data
    out["suma_numerica"] = round(suma, 2) if suma is not None else None
    out["tiene_encabezados_esperados"] = _has_expected_headers(df)
    # Criterio: tiene filas, columnas y al menos algo de contenido numérico o encabezados esperados
    out["ok"] = out["filas"] > 0 and out["columnas"] > 0 and (out["celdas_numericas"] > 0 or out["tiene_encabezados_esperados"])
    return out


def list_pdf_2023_csv_files(by_source_dir: Path | None = None) -> list[Path]:
    """Lista CSV que corresponden a extracciones de PDF del año 2023 (Boletín en Cifras), sin duplicados por mes."""
    by_source_dir = by_source_dir or DATA_AUDIT_BY_SOURCE
    if not by_source_dir.exists():
        return []
    seen_months: set[str] = set()
    out: list[Path] = []
    for path in sorted(by_source_dir.glob("*.csv")):
        if "_tables.csv" not in path.name:
            continue
        # Debe ser 2023 (o 202023 en nombres tipo Ene202023)
        if "2023" not in path.name and "202023" not in path.name:
            continue
        month_key = _normalize_filename_for_month(path.name)
        if month_key and month_key not in seen_months:
            seen_months.add(month_key)
            out.append(path)
    return out


def get_excel_2023_reference(by_source_dir: Path | None = None) -> dict[str, Any]:
    """
    Carga el extracto Excel de resumen por empresa 2023 y devuelve totales de referencia
    (suma de Primas Netas Cobradas) para comparar con lo extraído del PDF.
    """
    by_source_dir = by_source_dir or DATA_AUDIT_BY_SOURCE
    ref = {
        "ok": False,
        "archivo": "resumen-por-empresa-2023_extract.csv",
        "total_primas_miles": None,
        "filas": 0,
        "error": None,
    }
    path = by_source_dir / "resumen-por-empresa-2023_extract.csv"
    if not path.exists():
        ref["error"] = f"No existe {path}"
        return ref
    try:
        df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except Exception as e:
        ref["error"] = str(e)
        return ref
    ref["filas"] = len(df)
    # Columna "Primas Netas Cobradas" puede estar con salto de línea en el nombre
    primas_col = None
    for c in df.columns:
        if "primas" in str(c).lower() and "netas" in str(c).lower() and "cobradas" in str(c).lower():
            primas_col = c
            break
    if primas_col is None:
        primas_col = [c for c in df.columns if "primas" in str(c).lower()][:1]
        primas_col = primas_col[0] if primas_col else None
    if primas_col:
        s = pd.to_numeric(df[primas_col], errors="coerce")
        ref["total_primas_miles"] = float(s.sum()) if s.notna().any() else None
        ref["ok"] = ref["total_primas_miles"] is not None
    else:
        ref["error"] = "No se encontró columna de Primas Netas Cobradas"
    return ref


def run_verification_2023(by_source_dir: Path | None = None) -> dict[str, Any]:
    """
    Ejecuta la verificación completa: CSV de PDF 2023 + referencia Excel.
    Devuelve un dict con resultados por archivo y resumen.
    """
    by_source_dir = by_source_dir or DATA_AUDIT_BY_SOURCE
    pdf_files = list_pdf_2023_csv_files(by_source_dir)
    results = []
    for path in pdf_files:
        results.append(verify_one_pdf_table_csv(path))
    excel_ref = get_excel_2023_reference(by_source_dir)
    n_ok = sum(1 for r in results if r.get("ok"))
    return {
        "anio": YEAR_VERIFY,
        "archivos_pdf_csv": results,
        "total_archivos": len(results),
        "archivos_ok": n_ok,
        "todos_ok": n_ok == len(results) if results else False,
        "referencia_excel": excel_ref,
    }
