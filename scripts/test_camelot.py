# scripts/test_camelot.py
"""Prueba Camelot extrayendo tablas de un PDF (generado o existente)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Crear PDF de prueba con una tabla si no existe
DATA_RAW = ROOT / "data" / "raw"
TEST_PDF = DATA_RAW / "test_camelot_tabla.pdf"


def crear_pdf_prueba():
    """Genera un PDF simple con una tabla para probar Camelot."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    except ImportError:
        print("Instalando reportlab para generar PDF de prueba...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "-q"])
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(TEST_PDF), pagesize=A4)
    data = [
        ["Empresa", "Primas netas (VES)", "Siniestros (VES)", "Periodo"],
        ["Aseguradora A", "1.500.000", "800.000", "2024-01"],
        ["Aseguradora B", "2.100.000", "1.200.000", "2024-01"],
        ["Aseguradora C", "950.000", "400.000", "2024-01"],
    ]
    t = Table(data)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
    ]))
    doc.build([t])
    print(f"PDF de prueba creado: {TEST_PDF}")
    return TEST_PDF


def main():
    # Usar PDF existente o crear uno de prueba
    pdf_path = None
    for p in (TEST_PDF, *(DATA_RAW.glob("*.pdf") if DATA_RAW.exists() else [])):
        if p.exists():
            pdf_path = p
            break
    if not pdf_path or not pdf_path.exists():
        pdf_path = crear_pdf_prueba()

    print(f"\nExtrayendo tablas de: {pdf_path}")
    print("-" * 50)

    from src.extraction.pdf_extractor import PDFTableExtractor

    for flavor in ("lattice", "stream"):
        extractor = PDFTableExtractor(flavor=flavor)
        tables = extractor.extract_with_camelot(pdf_path)
        print(f"\n[Camelot flavor={flavor}] Tablas encontradas: {len(tables)}")
        for i, df in enumerate(tables):
            print(f"\n  Tabla {i + 1}:")
            print(df.to_string())
            print()

    # Resumen con método unificado
    extractor = PDFTableExtractor(flavor="lattice")
    all_tables = extractor.extract(pdf_path)
    print("-" * 50)
    print(f"Total tablas (extract): {len(all_tables)}")
    if all_tables:
        print("\nPrimera tabla (extract_first_table):")
        first = extractor.extract_first_table(pdf_path)
        if first is not None:
            print(first.to_string())
    print("\nPrueba Camelot finalizada correctamente.")


if __name__ == "__main__":
    main()
