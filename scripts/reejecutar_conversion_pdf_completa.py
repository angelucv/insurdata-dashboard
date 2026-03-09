"""
Re-ejecuta todo desde cero: borra archivos base, reconvierte todos los PDF de anuarios
a _tables.csv, verifica coherencia (conversión vs extensión del PDF) y ejecuta vaciado + base madre + indicadores.

Uso: python scripts/reejecutar_conversion_pdf_completa.py
"""
from __future__ import annotations

import re
import subprocess
import sys
import warnings
from pathlib import Path

# Reducir ruido de Camelot (PDF image-based) para que se vea el progreso
warnings.filterwarnings("ignore", message=".*image-based.*", module="camelot")
warnings.filterwarnings("ignore", message=".*does not lie in column range.*", module="camelot")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from config.anuarios_paths import (
    INDICE_FUENTES_CSV,
    SEGURO_EN_CIFRAS_VACIADO,
    SEGURO_EN_CIFRAS_INDICE,
)
from src.etl.anuarios_seguro_en_cifras import build_indice_fuentes, _nombre_archivo_to_tables_csv

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / "venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)


def run_script(name: str, timeout: int = 300) -> bool:
    path = ROOT / "scripts" / name
    if not path.exists():
        print(f"  No encontrado: {path}")
        return False
    r = subprocess.run([str(PY), str(path)], cwd=str(ROOT), timeout=timeout)
    return r.returncode == 0


def pdf_pages_and_size(pdf_path: Path) -> tuple[int, int]:
    """Retorna (número de páginas, tamaño en bytes)."""
    if not pdf_path.exists():
        return 0, 0
    size = pdf_path.stat().st_size
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return len(reader.pages), size
    except Exception:
        return 0, size


def main() -> None:
    print("=" * 70)
    print("RE-EJECUCIÓN COMPLETA: borrar base -> convertir PDF -> verificar -> pipeline")
    print("=" * 70)

    build_indice_fuentes()
    if not INDICE_FUENTES_CSV.exists():
        print("No existe índice de fuentes. Abortando.")
        sys.exit(1)

    fuentes = pd.read_csv(INDICE_FUENTES_CSV)
    fuentes["anio"] = pd.to_numeric(fuentes["anio"], errors="coerce")
    pdf_fuentes = fuentes[fuentes["tipo"] == "pdf"].copy()
    by_source = Path(DATA_AUDIT_BY_SOURCE)

    # ---------- 1) Borrar archivos base ----------
    print("\n[1/6] Borrando archivos base...")
    deleted_tables = 0
    for _, row in pdf_fuentes.iterrows():
        nombre = row.get("nombre_archivo", "")
        tables_name = _nombre_archivo_to_tables_csv(nombre)
        path = by_source / tables_name
        if path.exists():
            path.unlink()
            deleted_tables += 1
    print(f"  Eliminados {deleted_tables} *_tables.csv en by_source")

    for name, path in [
        ("anuario_metricas.csv", SEGURO_EN_CIFRAS_VACIADO / "anuario_metricas.csv"),
        ("anuario_entidades.csv", SEGURO_EN_CIFRAS_VACIADO / "anuario_entidades.csv"),
        ("matriz_base_madre_2014_2024.csv", SEGURO_EN_CIFRAS_VACIADO / "matriz_base_madre_2014_2024.csv"),
        ("indicadores_corrida_fria.csv", SEGURO_EN_CIFRAS_INDICE / "indicadores_corrida_fria.csv"),
        ("vaciado_secuencial_resumen.csv", SEGURO_EN_CIFRAS_INDICE / "vaciado_secuencial_resumen.csv"),
    ]:
        if path.exists():
            path.unlink()
            print(f"  Eliminado: {path.relative_to(ROOT)}")

    # ---------- 2) Re-convertir todos los PDF a _tables.csv ----------
    print("\n[2/6] Convirtiendo PDF -> _tables.csv (Camelot/pdfplumber/OCR)...")
    from src.extraction.pdf_extractor import PDFTableExtractor

    extractor = PDFTableExtractor(flavor="lattice")
    conversion_log = []

    for _, row in pdf_fuentes.iterrows():
        anio = int(row["anio"]) if pd.notna(row["anio"]) else 0
        nombre = row.get("nombre_archivo", "")
        ruta_rel = row.get("ruta_relativa", "")
        pdf_path = Path(DATA_RAW) / ruta_rel.replace("/", "\\")
        tables_name = _nombre_archivo_to_tables_csv(nombre)
        out_path = by_source / tables_name

        pages, size_bytes = pdf_pages_and_size(pdf_path)
        size_kb = round(size_bytes / 1024, 1)

        if not pdf_path.exists():
            print(f"  {anio} {nombre}: NO EXISTE PDF -> {pdf_path}")
            conversion_log.append({
                "anio": anio,
                "nombre_archivo": nombre,
                "pdf_paginas": 0,
                "pdf_size_kb": 0,
                "csv_filas": 0,
                "csv_columnas": 0,
                "n_tablas": 0,
                "coherente": False,
                "observacion": "PDF no encontrado",
            })
            continue

        try:
            tables = extractor.extract(pdf_path, use_ocr_if_scanned=True)
        except Exception as e:
            print(f"  {anio} {nombre}: Error extracción -> {e}")
            conversion_log.append({
                "anio": anio,
                "nombre_archivo": nombre,
                "pdf_paginas": pages,
                "pdf_size_kb": size_kb,
                "csv_filas": 0,
                "csv_columnas": 0,
                "n_tablas": 0,
                "coherente": False,
                "observacion": str(e)[:80],
            })
            continue

        if tables:
            df = pd.concat(tables, ignore_index=True)
            df.to_csv(out_path, index=False, encoding="utf-8-sig")
            n_rows, n_cols = df.shape
            # Coherente: PDF con muchas páginas debería dar bastantes filas; si tiene páginas y 0 filas, incoherente
            coherente = n_rows > 0 or pages < 3
            if pages >= 10 and n_rows < 50:
                coherente = False
            conversion_log.append({
                "anio": anio,
                "nombre_archivo": nombre,
                "pdf_paginas": pages,
                "pdf_size_kb": size_kb,
                "csv_filas": n_rows,
                "csv_columnas": n_cols,
                "n_tablas": len(tables),
                "coherente": coherente,
                "observacion": "OK" if coherente else "Pocas filas para tamaño PDF",
            })
            print(f"  {anio} {nombre}: {len(tables)} tablas -> {n_rows} filas x {n_cols} cols (PDF: {pages} pg, {size_kb} KB)")
        else:
            conversion_log.append({
                "anio": anio,
                "nombre_archivo": nombre,
                "pdf_paginas": pages,
                "pdf_size_kb": size_kb,
                "csv_filas": 0,
                "csv_columnas": 0,
                "n_tablas": 0,
                "coherente": pages < 5,
                "observacion": "Sin tablas extraídas",
            })
            print(f"  {anio} {nombre}: sin tablas extraídas (PDF: {pages} pg, {size_kb} KB)")

    # ---------- 3) Verificación: conversión vs extensión PDF ----------
    print("\n[3/6] Verificación: conversión vs extensión de cada PDF...")
    verif_path = SEGURO_EN_CIFRAS_INDICE / "verificacion_conversion_pdf.csv"
    verif_df = pd.DataFrame(conversion_log)
    verif_df.to_csv(verif_path, index=False, encoding="utf-8-sig")
    print(f"  Guardado: {verif_path}")

    incoherentes = verif_df[verif_df["coherente"] == False]
    if len(incoherentes) > 0:
        print(f"  Alertas ({len(incoherentes)}): PDFs con posible conversión insuficiente:")
        for _, r in incoherentes.iterrows():
            print(f"    - {r['anio']} {r['nombre_archivo']}: {r['pdf_paginas']} pg, {r['pdf_size_kb']} KB -> {r['csv_filas']} filas | {r['observacion']}")
    else:
        print("  Todas las conversiones coherentes con la extensión de los PDF.")

    # Resumen numérico
    with open(SEGURO_EN_CIFRAS_INDICE / "verificacion_conversion_pdf_resumen.txt", "w", encoding="utf-8") as f:
        f.write("=== Verificación conversión PDF -> _tables.csv ===\n\n")
        f.write("Criterio coherencia: csv_filas > 0 o pdf_paginas < 3; si pdf_paginas >= 10 y csv_filas < 50 -> incoherente.\n\n")
        f.write(verif_df.to_string() + "\n\n")
        f.write(f"Incoherentes: {len(incoherentes)}\n")
    print(f"  Resumen: {SEGURO_EN_CIFRAS_INDICE / 'verificacion_conversion_pdf_resumen.txt'}")

    # ---------- 4) Vaciado secuencial ----------
    print("\n[4/6] Vaciado secuencial...")
    if not run_script("anuarios_vaciado_secuencial.py", timeout=120000):
        print("  Falló vaciado.")
        sys.exit(1)

    # ---------- 5) Base madre 2014-2024 ----------
    print("\n[5/6] Matriz base madre 2014-2024...")
    if not run_script("anuarios_base_madre_2014_2024.py"):
        print("  Falló base madre.")
        sys.exit(1)

    # ---------- 6) Indicadores corrida fría ----------
    print("\n[6/6] Indicadores y USD...")
    if not run_script("indicadores_corrida_fria.py"):
        print("  Falló indicadores.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("Listo. Revisar:")
    print("  - indice/verificacion_conversion_pdf.csv (conversión vs extensión PDF)")
    print("  - indice/verificacion_conversion_pdf_resumen.txt")
    print("  - python scripts/mostrar_series_usd_terminal.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
