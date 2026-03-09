# scripts/extract_pdf_anuario_tabla_a_tabla.py
"""
Extrae el PDF del anuario (Seguro en Cifras) tabla a tabla usando el índice.
Cada cuadro (Nº 4, 5-A, etc.) tiene título y página; se extrae solo esa página
y se guarda un CSV por cuadro en audit/by_source/.

Uso:
  python scripts/extract_pdf_anuario_tabla_a_tabla.py [--year 2023] [--dry-run]

Requisito: tener ya el índice (p. ej. en by_source/seguros-en-cifra-2023_tables.csv
o en las primeras páginas del PDF). Si existe el CSV global, se parsea el índice desde ahí.
"""
from __future__ import annotations

import re
import sys
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from src.extraction.pdf_extractor import PDFTableExtractor


ANIO_DEFAULT = 2023
PDF_NAME = "seguros-en-cifra-2023.pdf"  # nombre esperado en raw/pdf/


def _normalize_cuadro_id(num: str) -> str:
    """Normaliza id de cuadro para nombre de archivo: 5-A -> 5A, 20-D -> 20D."""
    s = str(num).strip().upper().replace("-", "").replace(" ", "")
    return re.sub(r"[^\w]", "", s) or "unknown"


def parse_indice_desde_csv(csv_path: Path) -> list[dict]:
    """
    Parsea el índice desde el CSV global extraído (columnas 0=Nº, 1=Sección, 2=Título, 3=Página).
    Devuelve lista de dict con cuadro_id, seccion, titulo, pagina, pagina_camelot.
    """
    if not csv_path.exists():
        return []
    try:
        df = pd.read_csv(csv_path, header=None, encoding="utf-8", on_bad_lines="skip")
    except Exception:
        return []
    filas = []
    for _, row in df.iterrows():
        if len(row) < 4:
            continue
        num = row.iloc[0]
        seccion = row.iloc[1]
        titulo = row.iloc[2]
        pagina = row.iloc[3]
        if pd.isna(num) or pd.isna(pagina):
            continue
        num_str = str(num).strip()
        pag_str = str(pagina).strip()
        # Página debe ser número o rango (19, 20-21, 7-15)
        if not re.match(r"^\d+(-\d+)?$", pag_str):
            continue
        # Excluir cabecera del CSV (0,1,2,3) y filas sin número de cuadro válido (ej. 4, 5-A, 20-D)
        if not num_str or re.match(r"^[0123]$", num_str):
            continue
        if not re.match(r"^\d+([-]?[A-Fa-f])?$", num_str):
            continue
        # Cuadro id para nombre de archivo
        cid = _normalize_cuadro_id(num_str)
        # Camelot acepta "19" o "20-21"
        pagina_camelot = pag_str
        filas.append({
            "cuadro_id": cid,
            "cuadro_num": num_str,
            "seccion": str(seccion).strip() if pd.notna(seccion) else "",
            "titulo": str(titulo).strip() if pd.notna(titulo) else "",
            "pagina": pag_str,
            "pagina_camelot": pagina_camelot,
        })
    return filas


def extract_pdf_pages(pdf_path: Path, pages: str) -> list[pd.DataFrame]:
    """Extrae tablas de un rango de páginas del PDF. pages: '19' o '20-21'."""
    ext = PDFTableExtractor()
    return ext.extract_with_camelot(pdf_path, pages=pages)


def run_tabla_a_tabla(anio: int = ANIO_DEFAULT, dry_run: bool = False) -> dict:
    """
    Ejecuta extracción tabla a tabla para el anuario del año dado.
    Usa el índice en by_source/seguros-en-cifra-{anio}_tables.csv si existe.
    """
    pdf_path = DATA_RAW / "pdf" / f"seguros-en-cifra-{anio}.pdf"
    if not pdf_path.exists():
        # Intentar sin subcarpeta
        pdf_path = DATA_RAW / f"seguros-en-cifra-{anio}.pdf"
    if not pdf_path.exists():
        return {"error": f"No se encontró PDF para año {anio}", "cuadros_extraidos": 0}

    csv_global = DATA_AUDIT_BY_SOURCE / f"seguros-en-cifra-{anio}_tables.csv"
    indice = parse_indice_desde_csv(csv_global)
    if not indice:
        return {"error": "No se pudo parsear el índice (ejecutar antes el pipeline que genera el CSV global)", "cuadros_extraidos": 0}

    DATA_AUDIT_BY_SOURCE.mkdir(parents=True, exist_ok=True)
    manifest = []
    extractor = PDFTableExtractor()

    for i, item in enumerate(indice):
        cid = item["cuadro_id"]
        pag = item["pagina_camelot"]
        titulo = (item["titulo"] or "")[:60].replace("/", "-")
        out_name = f"seguros-en-cifra-{anio}_cuadro_{cid}_p{pag}.csv"
        out_path = DATA_AUDIT_BY_SOURCE / out_name

        if dry_run:
            print(f"  [DRY-RUN] Cuadro {item['cuadro_num']} p.{pag} -> {out_name}")
            manifest.append({"cuadro_id": cid, "pagina": pag, "archivo": out_name, "titulo": item["titulo"]})
            continue

        try:
            tables = extractor.extract_with_camelot(pdf_path, pages=pag)
        except Exception as e:
            print(f"  [AVISO] Cuadro {cid} p.{pag}: {e}")
            manifest.append({"cuadro_id": cid, "pagina": pag, "archivo": out_name, "error": str(e)})
            continue

        if not tables:
            manifest.append({"cuadro_id": cid, "pagina": pag, "archivo": out_name, "filas": 0})
            continue

        # Unir tablas si hay varias (p. ej. páginas 20-21)
        combined = pd.concat(tables, ignore_index=True)
        combined.to_csv(out_path, index=False, encoding="utf-8-sig")
        manifest.append({
            "cuadro_id": cid,
            "cuadro_num": item["cuadro_num"],
            "pagina": pag,
            "titulo": item["titulo"],
            "archivo": out_name,
            "filas": len(combined),
        })
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  Cuadro {item['cuadro_num']} p.{pag} -> {out_name} ({len(combined)} filas)")

    manifest_path = DATA_AUDIT_BY_SOURCE / f"seguros-en-cifra-{anio}_cuadros_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"anio": anio, "generado": datetime.now().isoformat(), "cuadros": manifest}, f, indent=2, ensure_ascii=False)

    n_ok = sum(1 for m in manifest if m.get("filas", 0) > 0)
    return {"cuadros_indice": len(indice), "cuadros_extraidos": n_ok, "manifest": str(manifest_path)}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Extracción PDF anuario tabla a tabla")
    p.add_argument("--year", type=int, default=ANIO_DEFAULT, help="Año del anuario (ej. 2023)")
    p.add_argument("--dry-run", action="store_true", help="Solo listar cuadros, no extraer")
    args = p.parse_args()

    print("=== Extracción PDF anuario (tabla a tabla) ===\n")
    res = run_tabla_a_tabla(anio=args.year, dry_run=args.dry_run)
    if res.get("error"):
        print("  Error:", res["error"])
        return
    print(f"\n  Cuadros en índice: {res.get('cuadros_indice', 0)}")
    print(f"  Cuadros con datos extraídos: {res.get('cuadros_extraidos', 0)}")
    print(f"  Manifest: {res.get('manifest', '')}")
    if not args.dry_run:
        print("\n  Revisar data/audit/by_source/ seguros-en-cifra-*_cuadro_*_p*.csv")


if __name__ == "__main__":
    main()
