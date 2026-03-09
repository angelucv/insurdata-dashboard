"""
Regenera la serie 2014-2024 desde cero (o solo pipeline a partir de by_source):
1) Opcional: elimina by_source *_tables.csv para 2014-2023 y re-extrae desde PDF.
2) Ejecuta vaciado secuencial, base madre e indicadores.
Uso:
  python scripts/regenerar_serie_2014_2024_desde_pdf.py          # solo vaciado + base madre + indicadores (usa CSV existentes)
  python scripts/regenerar_serie_2014_2024_desde_pdf.py --full  # borra _tables 2014-2023, re-extrae PDF, luego vaciado + ...
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from config.anuarios_paths import (
    INDICE_FUENTES_CSV,
    SEGURO_EN_CIFRAS_VACIADO,
    SEGURO_EN_CIFRAS_INDICE,
)
from src.etl.anuarios_seguro_en_cifras import build_indice_fuentes, _nombre_archivo_to_tables_csv

VENTANA_INICIO = 2014
VENTANA_FIN = 2024
ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / "venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)


def run_script(name: str) -> bool:
    path = ROOT / "scripts" / name
    if not path.exists():
        print(f"  No encontrado: {path}")
        return False
    r = subprocess.run([str(PY), str(path)], cwd=str(ROOT), timeout=300)
    return r.returncode == 0


def main() -> None:
    do_full = "--full" in sys.argv
    print("=" * 60)
    print("REGENERACIÓN SERIE 2014-2024" + (" (re-extracción PDF + pipeline)" if do_full else " (solo pipeline)"))
    print("=" * 60)

    build_indice_fuentes()
    if not INDICE_FUENTES_CSV.exists():
        print("No existe índice de fuentes. Abortando.")
        sys.exit(1)

    fuentes = pd.read_csv(INDICE_FUENTES_CSV)
    fuentes["anio"] = pd.to_numeric(fuentes["anio"], errors="coerce")
    pdf_2014_2023 = fuentes[(fuentes["anio"] >= VENTANA_INICIO) & (fuentes["anio"] < VENTANA_FIN) & (fuentes["tipo"] == "pdf")]
    by_source = Path(DATA_AUDIT_BY_SOURCE)

    step = 1
    if do_full:
        # 1) Borrar *_tables.csv de 2014-2023
        print("\n[1/5] Eliminando tablas extraídas (by_source) para 2014-2023...")
        deleted = 0
        for _, row in pdf_2014_2023.iterrows():
            nombre = row.get("nombre_archivo", "")
            tables_name = _nombre_archivo_to_tables_csv(nombre)
            path = by_source / tables_name
            if path.exists():
                path.unlink()
                deleted += 1
                print(f"  Eliminado: {tables_name}")
        print(f"  Total eliminados: {deleted}")

        # 2) Re-extraer PDFs 2014-2023
        print("\n[2/5] Re-extracción de tablas desde PDF (2014-2023)...")
        from src.extraction.pdf_extractor import PDFTableExtractor

        extractor = PDFTableExtractor(flavor="lattice")
        for _, row in pdf_2014_2023.iterrows():
            anio = int(row["anio"])
            nombre = row.get("nombre_archivo", "")
            ruta_rel = row.get("ruta_relativa", "")
            pdf_path = Path(DATA_RAW) / ruta_rel.replace("/", "\\")
            if not pdf_path.exists():
                print(f"  Saltando {anio}: no existe {pdf_path}")
                continue
            tables_name = _nombre_archivo_to_tables_csv(nombre)
            out_path = by_source / tables_name
            try:
                tables = extractor.extract(pdf_path, use_ocr_if_scanned=True)
            except Exception as e:
                print(f"  Error {anio}: {e}")
                continue
            if tables:
                df = pd.concat(tables, ignore_index=True)
                df.to_csv(out_path, index=False, encoding="utf-8-sig")
                print(f"  {anio}: {len(tables)} tablas -> {tables_name} ({len(df)} filas)")
            else:
                print(f"  {anio}: sin tablas extraídas")
        step = 3
    else:
        print("\nUsando _tables.csv existentes en by_source (ejecute con --full para re-extraer desde PDF).")

    # Vaciado secuencial
    print(f"\n[{step}/5] Vaciado secuencial (anuarios_vaciado_secuencial.py)...")
    if not run_script("anuarios_vaciado_secuencial.py"):
        print("  Falló el vaciado.")
        sys.exit(1)

    # Base madre 2014-2024
    print(f"\n[{step+1}/5] Matriz base madre (anuarios_base_madre_2014_2024.py)...")
    if not run_script("anuarios_base_madre_2014_2024.py"):
        print("  Falló base madre.")
        sys.exit(1)

    # Indicadores corrida fría
    print(f"\n[{step+2}/5] Indicadores y USD (indicadores_corrida_fria.py)...")
    if not run_script("indicadores_corrida_fria.py"):
        print("  Falló indicadores.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Listo. Ver serie: python scripts/mostrar_series_usd_terminal.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
