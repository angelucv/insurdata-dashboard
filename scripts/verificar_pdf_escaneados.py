"""
Verifica que se pueda extraer información de PDFs escaneados (OCR).
Prueba una muestra de PDFs en data/raw: detecta si son escaneados y extrae texto con Tesseract.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.extraction.pdf_ocr import (
    is_likely_scanned,
    _get_text_native,
    extract_text_ocr,
    extract_text_auto,
)


def main():
    raw = ROOT / "data" / "raw"
    if not raw.exists():
        print("No existe data/raw")
        return
    pdfs = list(raw.rglob("*.pdf"))
    print(f"=== Verificación de extracción en PDF (total: {len(pdfs)}) ===\n")
    # Probar hasta 8: 4 que parezcan escaneados y 4 normales
    scanned = []
    native_ok = []
    for p in pdfs:
        if is_likely_scanned(p):
            scanned.append(p)
        else:
            native_ok.append(p)
    print(f"PDF con poco texto (probable escaneado): {len(scanned)}")
    print(f"PDF con texto nativo suficiente: {len(native_ok)}\n")

    # Probar OCR en los primeros escaneados
    test_scanned = scanned[:4]
    if not test_scanned:
        test_scanned = pdfs[:3]
    print("--- Prueba de extracción (muestra) ---")
    for path in test_scanned:
        rel = path.relative_to(raw)
        is_scan = is_likely_scanned(path)
        native_len = len(_get_text_native(path))
        print(f"\n{rel.name}")
        print(f"  Escaneado (poco texto nativo): {is_scan} (caracteres nativos: {native_len})")
        if is_scan:
            text, method = extract_text_auto(path)
            print(f"  Método usado: {method}")
            print(f"  Caracteres extraídos: {len(text)}")
            if text.strip():
                sample = text.strip()[:300].replace("\n", " ")
                print(f"  Muestra: {sample}...")
            else:
                print("  [Sin texto extraído - revisar Tesseract/idioma spa]")
        else:
            text = _get_text_native(path)
            print(f"  Texto nativo: {len(text)} caracteres")
            if text.strip():
                print(f"  Muestra: {text.strip()[:200].replace(chr(10), ' ')}...")
    print("\n--- Conclusión ---")
    if scanned and test_scanned:
        ok = sum(1 for p in test_scanned if is_likely_scanned(p) and len(extract_text_ocr(p)) > 100)
        print(f"OCR funcionando en muestra de escaneados: {ok}/{len(test_scanned)}")
    print("Ejecuta el pipeline de extracción para volcar todo a crudo y luego al espejo.")


if __name__ == "__main__":
    main()
