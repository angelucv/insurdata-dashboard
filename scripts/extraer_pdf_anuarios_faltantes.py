"""
Re-extrae desde PDF los anuarios indicados (2006, 2014, 2023) y escribe
by_source/<nombre>_tables.csv y opcionalmente pdf_text/<nombre>.txt.
Luego se puede ejecutar el vaciado secuencial para incorporar esos datos.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATA_RAW
from config.audit_paths import DATA_AUDIT_BY_SOURCE, DATA_AUDIT_RAW_PDF_TEXT
from src.extraction.pdf_extractor import PDFTableExtractor

try:
    from src.extraction.pdf_ocr import extract_text_auto
except ImportError:
    extract_text_auto = None

# Anios a re-extraer desde PDF
ANIOS_OBJETIVO = (2006, 2014, 2023)  # 2006, 2014, 2023


def main():
    raw_pdf_dir = Path(DATA_RAW) / "pdf"
    by_source = Path(DATA_AUDIT_BY_SOURCE)
    pdf_text_dir = Path(DATA_AUDIT_RAW_PDF_TEXT)
    pdf_text_dir.mkdir(parents=True, exist_ok=True)

    # Buscar PDFs de anuarios para esos anios (seguros-en-cifra-YYYY.pdf)
    archivos = []
    for f in raw_pdf_dir.glob("*.pdf"):
        name = f.name
        if "boletin" in name.lower() or "bolet" in name.lower():
            continue
        if "seguro" not in name.lower() and "cifra" not in name.lower():
            continue
        for anio in ANIOS_OBJETIVO:
            if str(anio) in name and "cifra" in name.lower():
                archivos.append((anio, f))
                break

    if not archivos:
        print("No se encontraron PDFs de anuarios para 2006, 2014, 2023 en", raw_pdf_dir)
        sys.exit(1)

    extractor = PDFTableExtractor(flavor="lattice")
    for anio, pdf_path in sorted(archivos):
        stem = pdf_path.stem
        safe_stem = re.sub(r"[^\w\-\.]", "_", stem)
        tables_path = by_source / (safe_stem + "_tables.csv")

        print("Procesando %s (anio %d)..." % (pdf_path.name, anio))

        # Texto (nativo o OCR)
        if extract_text_auto:
            try:
                text, method = extract_text_auto(pdf_path)
                if text.strip():
                    txt_path = pdf_text_dir / (safe_stem + ".txt")
                    txt_path.write_text(text, encoding="utf-8")
                    print("  Texto guardado: %s (%s, %d caracteres)" % (txt_path.name, method, len(text)))
            except Exception as e:
                print("  Texto: error %s" % e)

        # Tablas
        try:
            tables = extractor.extract(pdf_path, use_ocr_if_scanned=True)
        except Exception as e:
            print("  Tablas: error %s" % e)
            tables = []

        if tables:
            import pandas as pd
            df = pd.concat(tables, ignore_index=True)
            df.to_csv(tables_path, index=False, encoding="utf-8-sig")
            print("  Tablas: %d tablas -> %s (%d filas)" % (len(tables), tables_path.name, len(df)))
        else:
            print("  Tablas: ninguna extraida; no se escribe CSV.")

    print("")
    print("Listo. Ejecuta: python scripts/anuarios_vaciado_secuencial.py")
    print("Luego: python scripts/anuarios_auditar_vaciado.py")


if __name__ == "__main__":
    main()
