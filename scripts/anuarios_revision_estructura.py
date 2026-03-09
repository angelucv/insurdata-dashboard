"""
Revisión de estructura de todos los anuarios Seguro en Cifras:
- Lista fuentes (indice), rangos de años, tipo (PDF/Excel).
- Para cada fuente en by_source (tablas y texto extraídos), reporta dimensiones y variables detectadas.
- Escribe data/audit/seguro_en_cifras/indice/revision_estructura.csv y resumen en consola.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from config.anuarios_paths import ensure_anuarios_dirs, SEGURO_EN_CIFRAS_INDICE, INDICE_FUENTES_CSV


def _is_anuario_name(name: str) -> bool:
    if "boletin" in name.lower() or "bolet" in name.lower():
        return False
    if "seguro" not in name.lower() and "seguros" not in name.lower():
        return False
    if "cifra" in name.lower() or "cifras" in name.lower():
        return True
    return False


def _year_from_name(name: str) -> int | None:
    m = re.search(r"20\d{2}", name)
    if m:
        return int(m.group(0))
    m = re.search(r"19[6-9]\d", name)
    return int(m.group(0)) if m else None


def main():
    ensure_anuarios_dirs()

    # 1) Fuentes en data/raw
    raw_sources = []
    for ext in ("*.pdf", "*.xlsx"):
        for path in DATA_RAW.rglob(ext):
            if not _is_anuario_name(path.name):
                continue
            y = _year_from_name(path.name)
            if y is None:
                continue
            raw_sources.append({
                "anio": y,
                "archivo": path.name,
                "tipo": path.suffix.lower().replace(".", ""),
                "origen": "data/raw",
            })

    # 2) Extracciones en by_source (tablas y texto)
    by_source = Path(DATA_AUDIT_BY_SOURCE)
    revision = []
    for f in sorted(by_source.iterdir()):
        if f.is_dir():
            continue
        name = f.name
        if not _is_anuario_name(name):
            continue
        y = _year_from_name(name)
        if y is None:
            continue
        row = {"anio": y, "archivo_extraido": name, "tiene_tablas": False, "tiene_texto": False, "filas_tablas": None, "columnas_tablas": None}
        if name.endswith("_tables.csv"):
            try:
                df = pd.read_csv(f, nrows=5, header=None)
                row["tiene_tablas"] = True
                row["filas_tablas"] = sum(1 for _ in open(f, encoding="utf-8", errors="ignore")) - 1
                row["columnas_tablas"] = len(df.columns) if not df.empty else 0
            except Exception:
                pass
            revision.append(row)
        else:
            continue

    # Texto PDF
    pdf_text_dir = by_source / "pdf_text"
    if pdf_text_dir.exists():
        for f in pdf_text_dir.iterdir():
            if f.suffix != ".txt":
                continue
            name = f.stem
            if not _is_anuario_name(name):
                continue
            y = _year_from_name(name)
            if y is None:
                continue
            revision.append({
                "anio": y,
                "archivo_extraido": name + ".txt",
                "tiene_tablas": False,
                "tiene_texto": True,
                "filas_tablas": None,
                "columnas_tablas": None,
            })

    # 3) Consolidar por año
    anios = sorted(set(r["anio"] for r in raw_sources) | set(r["anio"] for r in revision))
    resumen = []
    for anio in anios:
        raw = [r for r in raw_sources if r["anio"] == anio]
        ext = [r for r in revision if r["anio"] == anio]
        tablas_rows = [r for r in ext if r.get("tiene_tablas")]
        resumen.append({
            "anio": anio,
            "fuentes_raw": len(raw),
            "archivos_raw": "; ".join(r["archivo"] for r in raw[:3]) if raw else "",
            "tiene_extraccion_tablas": any(r.get("tiene_tablas") for r in ext),
            "tiene_extraccion_texto": any(r.get("tiene_texto") for r in ext),
            "total_filas_tablas": max((r.get("filas_tablas") or 0) for r in tablas_rows) if tablas_rows else None,
        })

    df_revision = pd.DataFrame(resumen)
    out_csv = SEGURO_EN_CIFRAS_INDICE / "revision_estructura.csv"
    df_revision.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("Revision de estructura - Seguro en Cifras")
    print("=" * 55)
    print("Rango de anios (fuentes en data/raw):", min(anios) if anios else "N/A", "-", max(anios) if anios else "N/A")
    print("Total anios con al menos una fuente:", len(anios))
    print()
    print("Resumen por año (primeros/ultimos 10):")
    print(df_revision.head(10).to_string(index=False))
    print("...")
    print(df_revision.tail(10).to_string(index=False))
    print()
    print("Guardado:", out_csv)


if __name__ == "__main__":
    main()
