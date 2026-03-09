"""
Pipeline de auditoría 100% local: extrae datos a estructura espejo en disco
(entities, primas_mensuales, etc.) sin tocar la base de datos.
Para arqueo y verificación antes de cargar a Supabase.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from config.audit_paths import (
    ensure_mirror_dirs,
    MIRROR_ENTITIES_CSV,
    MIRROR_PRIMAS_CSV,
    MANIFEST_INDEX_JSON,
    MIRROR_ENTITIES,
    MIRROR_PRIMAS,
    DATA_AUDIT_RAW_PDF_TEXT,
)
from src.etl.transformers import normalize_entity_name
from src.extraction.pdf_extractor import PDFTableExtractor

try:
    from src.extraction.pdf_ocr import extract_text_auto
except ImportError:
    extract_text_auto = None

# Reutilizar constantes del ETL Supabase
_MES_SHEET = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def _year_from_path(path: Path) -> int | None:
    m = re.search(r"20\d{2}", path.name)
    if m:
        return int(m.group(0))
    m = re.search(r"19[6-9]\d", path.name)
    return int(m.group(0)) if m else None


def _safe_float(x) -> float | None:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    try:
        v = float(x)
        return None if pd.isna(v) else round(v, 2)
    except (TypeError, ValueError):
        return None


def extract_primas_from_excel_local(path: Path) -> tuple[list[dict], list[dict], list[pd.DataFrame]]:
    """
    Extrae filas tipo primas_mensuales desde un Excel (resumen, primas netas, cuadro resultados).
    Retorna (rows_primas, rows_entities, list_of_raw_dfs_for_by_source).
    Cada row en rows_primas tiene entity_normalized_name, periodo, primas_netas_ves, etc.
    """
    path = Path(path)
    year = _year_from_path(path)
    rows_primas = []
    rows_entities = []
    raw_dfs = []
    entities_seen = set()

    def add_entity(norm: str, canonical: str):
        if not norm or norm == "_empty":
            return
        key = (norm, canonical)
        if key not in entities_seen:
            entities_seen.add(key)
            rows_entities.append({"normalized_name": norm, "canonical_name": canonical})

    name_lower = path.name.lower()

    # Resumen por empresa
    if "resumen" in name_lower and "empresa" in name_lower and year:
        try:
            xl = pd.ExcelFile(path)
        except Exception:
            return rows_primas, rows_entities, raw_dfs
        for sheet in xl.sheet_names:
            month_num = _MES_SHEET.get(sheet.lower().strip())
            if not month_num:
                continue
            try:
                df = pd.read_excel(path, sheet_name=sheet, header=8)
            except Exception:
                continue
            raw_dfs.append(df.assign(_sheet=sheet, _source=path.name))
            if df.empty or len(df.columns) < 3:
                continue
            col_empresa = col_primas = col_siniestros = col_comisiones = col_gastos_admin = None
            for c in df.columns:
                s = str(c).lower()
                if ("empresa" in s or "seguros" in s) and col_empresa is None:
                    col_empresa = c
                if "primas" in s and "netas" in s and col_primas is None:
                    col_primas = c
                if "siniestros" in s and "pagados" in s and col_siniestros is None:
                    col_siniestros = c
                if "comisiones" in s and "gastos" in s and col_comisiones is None:
                    col_comisiones = c
                if "gastos" in s and "administr" in s and col_gastos_admin is None:
                    col_gastos_admin = c
            if not col_empresa or col_primas not in df.columns:
                continue
            periodo_str = f"{year}-{month_num:02d}-01"
            for _, row in df.iterrows():
                emp = row.get(col_empresa)
                if pd.isna(emp) or not str(emp).strip() or "total" in str(emp).lower():
                    continue
                emp_str = str(emp).strip()
                try:
                    val_primas = float(row.get(col_primas, 0) or 0)
                except (TypeError, ValueError):
                    continue
                if pd.isna(val_primas):
                    continue
                primas_ves = val_primas * 1000 if val_primas < 1e9 else val_primas
                siniestros_ves = None
                if col_siniestros and col_siniestros in df.columns:
                    try:
                        v = float(row.get(col_siniestros, 0) or 0)
                        if not pd.isna(v):
                            siniestros_ves = v * 1000 if v < 1e9 else v
                    except (TypeError, ValueError):
                        pass
                gastos_ves = None
                for col_g in (col_comisiones, col_gastos_admin):
                    if col_g and col_g in df.columns:
                        try:
                            v = float(row.get(col_g, 0) or 0)
                            if not pd.isna(v):
                                if gastos_ves is None:
                                    gastos_ves = 0.0
                                gastos_ves += v * 1000 if v < 1e9 else v
                        except (TypeError, ValueError):
                            pass
                norm = normalize_entity_name(emp_str)
                add_entity(norm, emp_str)
                rows_primas.append({
                    "entity_normalized_name": norm,
                    "periodo": periodo_str,
                    "primas_netas_ves": _safe_float(primas_ves),
                    "siniestros_pagados_ves": _safe_float(siniestros_ves),
                    "gastos_operativos_ves": _safe_float(gastos_ves),
                    "source_file": path.name,
                    "source_sheet": sheet,
                })
        return rows_primas, rows_entities, raw_dfs

    # Primas netas por empresa
    if "primas" in name_lower and ("cobradas" in name_lower or "netas" in name_lower) and "empresa" in name_lower and year:
        try:
            xl = pd.ExcelFile(path)
        except Exception:
            return rows_primas, rows_entities, raw_dfs
        for sheet in xl.sheet_names:
            month_num = _MES_SHEET.get(sheet.lower().strip())
            if not month_num:
                continue
            try:
                df = pd.read_excel(path, sheet_name=sheet, header=9)
            except Exception:
                continue
            raw_dfs.append(df.assign(_sheet=sheet, _source=path.name))
            if df.empty or len(df.columns) < 3:
                continue
            col_empresa = col_primas = None
            for c in df.columns:
                s = str(c).lower()
                if "empresa" in s or "seguros" in s:
                    col_empresa = c
                if "primas" in s and "netas" in s:
                    col_primas = c
            col_empresa = col_empresa or (df.columns[2] if len(df.columns) > 2 else None)
            col_primas = col_primas or (df.columns[3] if len(df.columns) > 3 else None)
            if not col_empresa or not col_primas:
                continue
            periodo_str = f"{year}-{month_num:02d}-01"
            for _, row in df.iterrows():
                emp = row.get(col_empresa)
                if pd.isna(emp) or not str(emp).strip() or "total" in str(emp).lower():
                    continue
                emp_str = str(emp).strip()
                try:
                    val = float(row.get(col_primas, 0) or 0)
                except (TypeError, ValueError):
                    continue
                primas_ves = val * 1000 if val < 1e9 else val
                norm = normalize_entity_name(emp_str)
                add_entity(norm, emp_str)
                rows_primas.append({
                    "entity_normalized_name": norm,
                    "periodo": periodo_str,
                    "primas_netas_ves": _safe_float(primas_ves),
                    "siniestros_pagados_ves": None,
                    "gastos_operativos_ves": None,
                    "source_file": path.name,
                    "source_sheet": sheet,
                })
        return rows_primas, rows_entities, raw_dfs

    # Cuadro resultados
    if "cuadro" in name_lower and "resultados" in name_lower and year:
        try:
            xl = pd.ExcelFile(path)
        except Exception:
            return rows_primas, rows_entities, raw_dfs
        for sheet in xl.sheet_names:
            month_num = _MES_SHEET.get(sheet.lower().strip())
            if not month_num:
                continue
            try:
                df = pd.read_excel(path, sheet_name=sheet, header=9)
            except Exception:
                continue
            raw_dfs.append(df.assign(_sheet=sheet, _source=path.name))
            if df.empty or len(df.columns) < 3:
                continue
            col_empresa = col_primas = None
            for c in df.columns:
                s = str(c).lower()
                if "empresa" in s or "seguros" in s:
                    col_empresa = c
                if "primas" in s and "netas" in s:
                    col_primas = c
            col_empresa = col_empresa or (df.columns[2] if len(df.columns) > 2 else None)
            col_primas = col_primas or (df.columns[3] if len(df.columns) > 3 else None)
            if not col_empresa or not col_primas:
                continue
            periodo_str = f"{year}-{month_num:02d}-01"
            for _, row in df.iterrows():
                emp = row.get(col_empresa)
                if pd.isna(emp) or not str(emp).strip() or "total" in str(emp).lower():
                    continue
                emp_str = str(emp).strip()
                try:
                    val = float(row.get(col_primas, 0) or 0)
                except (TypeError, ValueError):
                    continue
                primas_ves = val * 1000 if val < 1e9 else val
                norm = normalize_entity_name(emp_str)
                add_entity(norm, emp_str)
                rows_primas.append({
                    "entity_normalized_name": norm,
                    "periodo": periodo_str,
                    "primas_netas_ves": _safe_float(primas_ves),
                    "siniestros_pagados_ves": None,
                    "gastos_operativos_ves": None,
                    "source_file": path.name,
                    "source_sheet": sheet,
                })
        return rows_primas, rows_entities, raw_dfs

    return rows_primas, rows_entities, raw_dfs


def extract_tables_from_pdf_local(path: Path, use_ocr: bool = True) -> list[pd.DataFrame]:
    """Extrae tablas de un PDF (Camelot/pdfplumber/OCR si escaneado)."""
    path = Path(path)
    if not path.exists() or path.suffix.lower() != ".pdf":
        return []
    ext = PDFTableExtractor()
    return ext.extract(path, use_ocr_if_scanned=use_ocr)


def run_audit_pipeline(raw_dir: Path | None = None) -> dict:
    """
    Recorre raw_dir (por defecto DATA_RAW), extrae todo a la estructura espejo
    y escribe el manifest. Retorna estadísticas.
    """
    raw_dir = raw_dir or DATA_RAW
    ensure_mirror_dirs()
    manifest_entries = []
    all_primas: list[dict] = []
    all_entities: dict[str, str] = {}  # normalized -> canonical

    excel_files = list(raw_dir.rglob("*.xlsx")) + list(raw_dir.rglob("*.xls"))
    for path in sorted(excel_files):
        rel = path.relative_to(raw_dir)
        try:
            rows_primas, rows_entities, raw_dfs = extract_primas_from_excel_local(path)
        except Exception as e:
            manifest_entries.append({
                "file": str(rel),
                "type": "excel",
                "rows_primas": 0,
                "rows_entities": 0,
                "error": str(e),
                "tables_raw": 0,
            })
            continue
        for e in rows_entities:
            all_entities[e["normalized_name"]] = e.get("canonical_name") or e["normalized_name"]
        all_primas.extend(rows_primas)
        # Guardar by_source
        if raw_dfs:
            out_name = path.stem + "_extract.csv"
            out_path = DATA_AUDIT_BY_SOURCE / out_name
            try:
                pd.concat(raw_dfs, ignore_index=True).to_csv(out_path, index=False, encoding="utf-8-sig")
            except Exception:
                pass
        manifest_entries.append({
            "file": str(rel),
            "type": "excel",
            "rows_primas": len(rows_primas),
            "rows_entities": len(rows_entities),
            "tables_raw": len(raw_dfs),
        })

    pdf_files = list(raw_dir.rglob("*.pdf"))
    DATA_AUDIT_RAW_PDF_TEXT.mkdir(parents=True, exist_ok=True)
    for path in sorted(pdf_files):
        rel = path.relative_to(raw_dir)
        pdf_text_chars = 0
        pdf_used_ocr = None
        try:
            # Crudo: texto completo (nativo o OCR si está escaneado)
            if extract_text_auto:
                text, method = extract_text_auto(path)
                pdf_used_ocr = method == "ocr"
                pdf_text_chars = len(text)
                if text.strip():
                    safe_name = re.sub(r"[^\w\-\.]", "_", path.stem) + ".txt"
                    txt_path = DATA_AUDIT_RAW_PDF_TEXT / safe_name
                    try:
                        txt_path.write_text(text, encoding="utf-8")
                    except Exception:
                        pass
            tables = extract_tables_from_pdf_local(path)
        except Exception as e:
            manifest_entries.append({
                "file": str(rel),
                "type": "pdf",
                "tables_extracted": 0,
                "pdf_text_chars": 0,
                "error": str(e),
            })
            continue
        if tables:
            out_name = re.sub(r"[^\w\-\.]", "_", path.stem) + "_tables.csv"
            out_path = DATA_AUDIT_BY_SOURCE / out_name
            try:
                pd.concat(tables, ignore_index=True).to_csv(out_path, index=False, encoding="utf-8-sig")
            except Exception:
                pass
        manifest_entries.append({
            "file": str(rel),
            "type": "pdf",
            "tables_extracted": len(tables),
            "pdf_text_chars": pdf_text_chars,
            "pdf_used_ocr": pdf_used_ocr,
        })

    # Escribir mirror
    if all_entities:
        entities_df = pd.DataFrame([
            {"normalized_name": k, "canonical_name": v} for k, v in all_entities.items()
        ])
        MIRROR_ENTITIES.mkdir(parents=True, exist_ok=True)
        entities_df.to_csv(MIRROR_ENTITIES_CSV, index=False, encoding="utf-8-sig")
    if all_primas:
        primas_df = pd.DataFrame(all_primas)
        MIRROR_PRIMAS.mkdir(parents=True, exist_ok=True)
        primas_df.to_csv(MIRROR_PRIMAS_CSV, index=False, encoding="utf-8-sig")

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "raw_dir": str(raw_dir),
        "total_primas_rows": len(all_primas),
        "total_entities": len(all_entities),
        "sources": manifest_entries,
    }
    with open(MANIFEST_INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return {
        "primas_rows": len(all_primas),
        "entities": len(all_entities),
        "excel_processed": len([e for e in manifest_entries if e.get("type") == "excel"]),
        "pdf_processed": len([e for e in manifest_entries if e.get("type") == "pdf"]),
        "manifest_path": str(MANIFEST_INDEX_JSON),
    }
