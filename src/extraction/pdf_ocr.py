"""
Extracción de texto desde PDFs escaneados (sin capa de texto) usando OCR.
Para anuarios y boletines antiguos que solo están como imagen.
"""
from pathlib import Path
import re

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
    from PIL import Image
    # En Windows, Tesseract suele estar en Program Files si no está en PATH
    import sys
    if sys.platform == "win32":
        _tesseract_exe = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if _tesseract_exe.exists():
            pytesseract.pytesseract.tesseract_cmd = str(_tesseract_exe)
except ImportError:
    pytesseract = None
    Image = None


# Umbral: si un PDF tiene menos de N caracteres de texto extraíble, se considera escaneado
MIN_TEXT_CHARS_FOR_NATIVE = 200


def _get_text_native(pdf_path: Path) -> str:
    """Extrae texto nativo del PDF (PyMuPDF)."""
    if not fitz:
        return ""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() or ""
        doc.close()
        return text.strip()
    except Exception:
        return ""


def is_likely_scanned(pdf_path: Path) -> bool:
    """
    True si el PDF parece escaneado (poco o ningún texto extraíble).
    Útil para decidir si usar OCR.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        return True
    text = _get_text_native(pdf_path)
    return len(text) < MIN_TEXT_CHARS_FOR_NATIVE


def extract_text_ocr(pdf_path: Path, lang: str = "spa") -> str:
    """
    Extrae texto de un PDF escaneado vía OCR (Tesseract).
    Si el idioma solicitado (ej. spa) no está instalado, usa 'eng'.
    """
    if not fitz or not pytesseract or not Image:
        return ""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return ""
    full_text = []
    for lang_try in (lang, "eng"):
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang=lang_try)
                if text.strip():
                    full_text.append(text)
            doc.close()
            return "\n\n".join(full_text)
        except Exception as e:
            if "spa" in str(e).lower() or "tessdata" in str(e).lower() or "language" in str(e).lower():
                if lang_try == "eng":
                    return f"[OCR Error: {e}]"
                continue
            return f"[OCR Error: {e}]"
    return ""


def extract_text_auto(pdf_path: Path, lang: str = "spa") -> tuple[str, str]:
    """
    Extrae texto del PDF: usa capa nativa si hay suficiente texto,
    si no usa OCR. Retorna (texto, "native"|"ocr").
    """
    pdf_path = Path(pdf_path)
    native = _get_text_native(pdf_path)
    if len(native) >= MIN_TEXT_CHARS_FOR_NATIVE:
        return native, "native"
    ocr = extract_text_ocr(pdf_path, lang=lang)
    return ocr, "ocr"


def extract_tables_from_ocr_text(text: str) -> list[list[list[str]]]:
    """
    Heurística simple: divide el texto OCR en bloques por líneas vacías
    y luego por columnas (espacios múltiples o tabulaciones).
    Retorna lista de "tablas" (cada una lista de filas, cada fila lista de celdas).
    Para tablas más complejas haría falta post-procesado con regex o ML.
    """
    tables = []
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    for block in blocks:
        rows = []
        for line in block.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Dividir por múltiples espacios (columnas aproximadas)
            cells = re.split(r"\s{2,}|\t", line)
            cells = [c.strip() for c in cells if c.strip()]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables
