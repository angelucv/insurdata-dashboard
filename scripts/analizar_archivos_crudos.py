# scripts/analizar_archivos_crudos.py
"""
Analiza data/raw/ y reporta: tipos de archivo, años detectables, coherencia con loaders ETL.
Ejecutar: python scripts/analizar_archivos_crudos.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW


def year_from_name(name: str) -> int | None:
    """Extrae año del nombre (20XX o 19XX)."""
    m = re.search(r"20\d{2}", name)
    if m:
        return int(m.group(0))
    m = re.search(r"19[6-9]\d", name)
    return int(m.group(0)) if m else None


def classifier_xlsx(name: str) -> str:
    """Clasifica Excel según nombre (mismo criterio que _excel_loader_name)."""
    n = name.lower()
    if "primas" in n and ("cobradas" in n or "netas" in n) and "empresa" in n:
        return "primas_netas_por_empresa"
    if "cuadro" in n and "resultados" in n:
        return "cuadro_resultados"
    if "resumen" in n and "empresa" in n:
        return "resumen_por_empresa"
    if ("seguro" in n and "cifras" in n) or ("cuadros" in n and "descargables" in n):
        return "seguro_en_cifras_anual"
    if "margen" in n and "solvencia" in n:
        return "margen_solvencia"
    if "indice" in n or "índice" in n:
        return "indices_por_empresa"
    if "saldo" in n and "operaciones" in n:
        return "saldo_operaciones"
    if "series" in n and "historicas" in n:
        return "series_historicas"
    return "otro"


def main():
    if not DATA_RAW.exists():
        print("No existe data/raw/")
        return

    print("=== ANÁLISIS DE ARCHIVOS CRUDOS (data/raw/) ===\n")

    # Recoger todos los archivos
    xlsx = list(DATA_RAW.rglob("*.xlsx")) + list(DATA_RAW.rglob("*.xls"))
    pdf = list(DATA_RAW.rglob("*.pdf"))

    # Excel por clasificación y año
    by_loader: dict[str, list[tuple[Path, int | None]]] = defaultdict(list)
    sin_anio: list[Path] = []
    for p in xlsx:
        rel = p.relative_to(DATA_RAW)
        y = year_from_name(p.name)
        kind = classifier_xlsx(p.name)
        by_loader[kind].append((rel, y))
        if y is None:
            sin_anio.append(rel)

    # PDF por año
    pdf_years: dict[int | None, int] = defaultdict(int)
    for p in pdf:
        y = year_from_name(p.name)
        pdf_years[y] += 1

    print("--- Excel por tipo (loader ETL) ---")
    for kind in sorted(by_loader.keys()):
        items = by_loader[kind]
        years = sorted(set(y for _, y in items if y is not None))
        n_with_year = sum(1 for _, y in items if y is not None)
        n_no_year = sum(1 for _, y in items if y is None)
        print(f"  {kind:30} {len(items):>3} archivos  años: {years!r}  (sin año: {n_no_year})")

    print("\n--- Excel sin año en el nombre (se omiten con --year) ---")
    for p in sin_anio[:25]:
        print(f"    {p}")
    if len(sin_anio) > 25:
        print(f"    ... y {len(sin_anio) - 25} más")

    print("\n--- PDF por año detectado ---")
    for y in sorted(k for k in pdf_years if k is not None):
        print(f"  {y}: {pdf_years[y]} PDF")
    if pdf_years.get(None, 0):
        print(f"  sin año en nombre: {pdf_years[None]} PDF")

    print("\n--- Resumen ---")
    print(f"  Excel total: {len(xlsx)}  |  PDF total: {len(pdf)}")
    print(f"  Loaders dedicados (resumen, primas, cuadro, seguro cifras): coherentes con opciones A/B/C.")
    print("  margen_solvencia / indices / saldo / series: sin loader especifico -> excel_generico.")
    print("  Detalle y propuesta: docs/ANALISIS_ARCHIVOS_CRUDOS_Y_PROPUESTA.md")


if __name__ == "__main__":
    main()
