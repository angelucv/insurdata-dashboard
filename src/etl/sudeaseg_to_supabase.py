# src/etl/sudeaseg_to_supabase.py
"""Carga datos SUDEASEG a Supabase: normaliza columnas, resuelve entidades y inserta en entities + primas_mensuales."""
import re
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import DATA_RAW, DATA_PROCESSED
from config.sudeaseg_columns import COLUMN_MAPPING, PRIMAS_MENSUALES_COLUMNS
from src.db import get_supabase_client
from src.extraction.excel_loader import load_sudeaseg_excel
from src.extraction.pdf_extractor import PDFTableExtractor
from .transformers import flatten_multiindex_headers, impute_nulls_financial, normalize_entity_name


def _normalize_column_name(col: str) -> str:
    """Convierte nombre de columna a clave normalizada para el mapeo."""
    if pd.isna(col):
        return ""
    s = str(col).lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", "_", s).strip()
    return s


def map_columns_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renombra columnas del DataFrame según COLUMN_MAPPING.
    Añade columnas esperadas que falten (con None).
    """
    out = pd.DataFrame()
    for c in df.columns:
        key = _normalize_column_name(c)
        if key in COLUMN_MAPPING:
            target = COLUMN_MAPPING[key]
            if target not in out.columns:
                out[target] = df[c].values
    for col in ["primas_netas_ves", "primas_netas_usd", "siniestros_pagados_ves", "siniestros_pagados_usd",
                "gastos_operativos_ves", "gastos_operativos_usd"]:
        if col not in out.columns:
            out[col] = None
    if "entity_name" not in out.columns:
        for c in df.columns:
            key = _normalize_column_name(c)
            if key in ("empresa", "entidad", "razon_social", "aseguradora", "nombre"):
                out["entity_name"] = df[c].values
                break
        if "entity_name" not in out.columns and len(df.columns) > 0:
            out["entity_name"] = df.iloc[:, 0].values
    if "periodo" not in out.columns:
        for c in df.columns:
            key = _normalize_column_name(c)
            if key in ("periodo", "mes", "fecha", "anio", "año"):
                out["periodo"] = df[c].values
                break
    return out


def _parse_period(periodo: Any) -> str | None:
    """Convierte periodo a YYYY-MM-DD (primer día del mes)."""
    if pd.isna(periodo):
        return None
    s = str(periodo).strip()
    if hasattr(periodo, "strftime"):
        return periodo.strftime("%Y-%m-%d")
    # Mes nombre + año: "Enero 2024", "ene 2024"
    meses = {"ene": 1, "enero": 1, "feb": 2, "febrero": 2, "mar": 3, "marzo": 3, "abr": 4, "abril": 4,
             "may": 5, "mayo": 5, "jun": 6, "junio": 6, "jul": 7, "julio": 7, "ago": 8, "agosto": 8,
             "sep": 9, "septiembre": 9, "oct": 10, "octubre": 10, "nov": 11, "noviembre": 11,
             "dic": 12, "diciembre": 12}
    s_lower = s.lower()
    for name, num in meses.items():
        if name in s_lower:
            years = re.findall(r"20\d{2}", s)
            if years:
                return f"{years[0]}-{num:02d}-01"
            break
    # YYYY-MM o YYYY-MM-DD
    if re.match(r"20\d{2}-\d{2}", s):
        return s[:7] + "-01" if len(s) <= 7 else s[:10]
    # DD/MM/YYYY o MM/YYYY
    parts = re.findall(r"\d+", s)
    if len(parts) >= 2:
        if len(parts) == 2:
            y, m = int(parts[0]), int(parts[1])
            if m > 12:
                y, m = m, y
            return f"{y}-{m:02d}-01"
        if len(parts) == 3:
            return f"{parts[2]}-{int(parts[1]):02d}-{int(parts[0]):02d}"
    return s[:10] if len(s) >= 10 else None


def get_or_create_entity_id(sb: Any, normalized_name: str, canonical_name: str | None = None) -> str | None:
    """Obtiene el UUID de una entidad en Supabase; si no existe, la crea."""
    if not normalized_name or normalized_name == "_empty":
        return None
    try:
        r = sb.table("entities").select("id").eq("normalized_name", normalized_name).execute()
        if r.data and len(r.data) > 0:
            return r.data[0]["id"]
        r = sb.table("entities").insert({
            "normalized_name": normalized_name,
            "canonical_name": canonical_name or normalized_name,
        }).execute()
        if r.data and len(r.data) > 0:
            return r.data[0]["id"]
        # Insert puede no devolver datos en algunos proyectos; leer de nuevo
        r = sb.table("entities").select("id").eq("normalized_name", normalized_name).execute()
        return r.data[0]["id"] if r.data else None
    except Exception as e:
        print(f"[sudeaseg_to_supabase] Error entity {normalized_name}: {e}")
        return None


def df_to_primas_rows(df: pd.DataFrame, sb: Any) -> list[dict]:
    """
    Convierte un DataFrame con columnas mapeadas a lista de filas para primas_mensuales.
    Resuelve entity_name -> entity_id vía Supabase.
    """
    if "entity_name" not in df.columns:
        return []
    rows = []
    for _, row in df.iterrows():
        name = row.get("entity_name")
        if pd.isna(name) or not str(name).strip():
            continue
        norm = normalize_entity_name(str(name))
        entity_id = get_or_create_entity_id(sb, norm, str(name).strip())
        if not entity_id:
            continue
        periodo = row.get("periodo")
        periodo_str = _parse_period(periodo)
        if not periodo_str:
            continue
        r = {
            "entity_id": entity_id,
            "periodo": periodo_str,
            "primas_netas_ves": float(row["primas_netas_ves"]) if pd.notna(row.get("primas_netas_ves")) else None,
            "primas_netas_usd": float(row["primas_netas_usd"]) if pd.notna(row.get("primas_netas_usd")) else None,
            "siniestros_pagados_ves": float(row["siniestros_pagados_ves"]) if pd.notna(row.get("siniestros_pagados_ves")) else None,
            "siniestros_pagados_usd": float(row["siniestros_pagados_usd"]) if pd.notna(row.get("siniestros_pagados_usd")) else None,
            "gastos_operativos_ves": float(row["gastos_operativos_ves"]) if pd.notna(row.get("gastos_operativos_ves")) else None,
            "gastos_operativos_usd": float(row["gastos_operativos_usd"]) if pd.notna(row.get("gastos_operativos_usd")) else None,
        }
        rows.append(r)
    return rows


# Meses en español (nombre de hoja) -> número
_MES_SHEET = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def _year_from_path(path: Path) -> int | None:
    m = re.search(r"20\d{2}", path.name)
    return int(m.group(0)) if m else None


def _load_sheet_empresa_primas(
    path: Path, sb: Any, sheet: str, year: int, header_row: int,
    col_empresa: str | None, col_primas: str | None, col_siniestros: str | None = None,
) -> list[dict]:
    """Lee una hoja con cabecera en header_row y devuelve lista de filas para primas_mensuales."""
    month_num = _MES_SHEET.get(sheet.lower().strip())
    if not month_num:
        return []
    try:
        df = pd.read_excel(path, sheet_name=sheet, header=header_row)
    except Exception:
        return []
    if df.empty or len(df.columns) < 3:
        return []
    if not col_empresa:
        for c in df.columns:
            if "empresa" in str(c).lower() or "seguros" in str(c).lower():
                col_empresa = c
                break
        col_empresa = col_empresa or (df.columns[2] if len(df.columns) > 2 else None)
    if not col_primas:
        for c in df.columns:
            if "primas" in str(c).lower() and "netas" in str(c).lower():
                col_primas = c
                break
        col_primas = col_primas or (df.columns[3] if len(df.columns) > 3 else None)
    if not col_empresa or col_primas not in df.columns:
        return []
    periodo_str = f"{year}-{month_num:02d}-01"
    rows = []
    for _, row in df.iterrows():
        emp = row.get(col_empresa)
        if pd.isna(emp) or not str(emp).strip():
            continue
        emp_str = str(emp).strip()
        if "total" in emp_str.lower():
            continue
        try:
            val = float(row.get(col_primas, 0) or 0)
        except (TypeError, ValueError):
            continue
        primas_ves = val * 1000 if val < 1e9 else val
        siniestros_ves = None
        if col_siniestros and col_siniestros in df.columns:
            try:
                siniestros_ves = float(row.get(col_siniestros, 0) or 0)
                if siniestros_ves < 1e9:
                    siniestros_ves *= 1000
            except (TypeError, ValueError):
                pass
        norm = normalize_entity_name(emp_str)
        entity_id = get_or_create_entity_id(sb, norm, emp_str)
        if not entity_id:
            continue
        r = {
            "entity_id": entity_id,
            "periodo": periodo_str,
            "primas_netas_ves": round(primas_ves, 2),
            "primas_netas_usd": None,
            "siniestros_pagados_ves": round(siniestros_ves, 2) if siniestros_ves is not None else None,
            "siniestros_pagados_usd": None,
            "gastos_operativos_ves": None,
            "gastos_operativos_usd": None,
        }
        rows.append(r)
    return rows


def load_cuadro_resultados_excel(path: Path, sb: Any) -> int:
    """Carga 'Cuadro de Resultados' (por mes): Empresas de Seguros, Primas Netas Cobradas. Cabecera fila 9."""
    year = _year_from_path(path)
    if not year:
        try:
            df0 = pd.read_excel(path, sheet_name=0, header=None)
            for _, r in df0.head(8).iterrows():
                for c in r:
                    m = re.search(r"20\d{2}", str(c))
                    if m:
                        year = int(m.group(0))
                        break
                if year:
                    break
        except Exception:
            pass
    if not year:
        return 0
    total = 0
    try:
        xl = pd.ExcelFile(path)
    except Exception:
        return 0
    for sheet in xl.sheet_names:
        month_num = _MES_SHEET.get(sheet.lower().strip())
        if not month_num:
            continue
        rows = _load_sheet_empresa_primas(path, sb, sheet, year, 9, None, None, None)
        if rows:
            try:
                sb.table("primas_mensuales").upsert(rows, on_conflict="entity_id,periodo").execute()
                total += len(rows)
            except Exception as e:
                if "23505" not in str(e):
                    try:
                        sb.table("primas_mensuales").insert(rows).execute()
                        total += len(rows)
                    except Exception:
                        pass
                else:
                    total += len(rows)
    return total


def load_resumen_por_empresa_excel(path: Path, sb: Any) -> int:
    """
    Carga 'Resumen por empresa': Primas Netas, Siniestros Pagados y Gastos Operativos.

    Estructura típica (fila 7 indica "En Miles de Bs.", cabecera en fila 8):
      - Emp. de Seguros
      - Primas Netas Cobradas (1)
      - Siniestros Pagados (Netos de Salvamento) (2)
      - Comisiones y Gastos de Adquisición (6)
      - Gastos de Administración (7)
      - Saldo de Operaciones (8)

    Mapeo:
      - primas_netas_ves  <- "Primas Netas Cobradas" (x 1000)
      - siniestros_pagados_ves <- "Siniestros Pagados" (x 1000)
      - gastos_operativos_ves  <- (Comisiones y Gastos de Adquisición + Gastos de Administración) (x 1000)
    """
    year = _year_from_path(path)
    if not year:
        return 0

    total = 0
    try:
        xl = pd.ExcelFile(path)
    except Exception:
        return 0

    for sheet in xl.sheet_names:
        month_num = _MES_SHEET.get(sheet.lower().strip())
        if not month_num:
            continue

        try:
            df = pd.read_excel(path, sheet_name=sheet, header=8)
        except Exception:
            continue

        if df.empty or len(df.columns) < 3:
            continue

        col_empresa = col_primas = col_siniestros = None
        col_comisiones = col_gastos_admin = None

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

        # Fallbacks básicos si no se detectan por texto
        if not col_empresa and len(df.columns) > 2:
            col_empresa = df.columns[2]
        if not col_primas and len(df.columns) > 3:
            col_primas = df.columns[3]

        if not col_empresa or col_primas not in df.columns:
            continue

        periodo_str = f"{year}-{month_num:02d}-01"
        rows: list[dict] = []

        for _, row in df.iterrows():
            emp = row.get(col_empresa)
            if pd.isna(emp) or not str(emp).strip():
                continue
            emp_str = str(emp).strip()
            if "total" in emp_str.lower():
                continue

            # Primas Netas
            try:
                val_primas = float(row.get(col_primas, 0) or 0)
            except (TypeError, ValueError):
                continue
            if pd.isna(val_primas):
                continue
            primas_ves = val_primas * 1000 if val_primas < 1e9 else val_primas
            if pd.isna(primas_ves):
                primas_ves = 0.0

            # Siniestros Pagados
            siniestros_ves = None
            if col_siniestros and col_siniestros in df.columns:
                try:
                    v_sin = float(row.get(col_siniestros, 0) or 0)
                    if not pd.isna(v_sin):
                        siniestros_ves = v_sin * 1000 if v_sin < 1e9 else v_sin
                except (TypeError, ValueError):
                    siniestros_ves = None

            # Gastos Operativos = Comisiones y Gastos de Adquisición + Gastos de Administración
            gastos_ves = None
            for col_g in (col_comisiones, col_gastos_admin):
                if col_g and col_g in df.columns:
                    try:
                        v_g = float(row.get(col_g, 0) or 0)
                    except (TypeError, ValueError):
                        continue
                    if pd.isna(v_g):
                        continue
                    if gastos_ves is None:
                        gastos_ves = 0.0
                    gastos_ves += v_g * 1000 if v_g < 1e9 else v_g

            def _safe_float(x):
                """None si es None o NaN, sino round(x, 2) para JSON."""
                if x is None or (isinstance(x, float) and pd.isna(x)):
                    return None
                return round(float(x), 2)

            norm = normalize_entity_name(emp_str)
            entity_id = get_or_create_entity_id(sb, norm, emp_str)
            if not entity_id:
                continue

            r = {
                "entity_id": entity_id,
                "periodo": periodo_str,
                "primas_netas_ves": _safe_float(primas_ves),
                "primas_netas_usd": None,
                "siniestros_pagados_ves": _safe_float(siniestros_ves),
                "siniestros_pagados_usd": None,
                "gastos_operativos_ves": _safe_float(gastos_ves),
                "gastos_operativos_usd": None,
            }
            rows.append(r)

        if not rows:
            continue

        try:
            sb.table("primas_mensuales").upsert(rows, on_conflict="entity_id,periodo").execute()
            total += len(rows)
        except Exception as e:
            err_msg = str(e)
            code = getattr(e, "code", None) or (e.args[0].get("code") if e.args and isinstance(e.args[0], dict) else None)
            if "23505" in err_msg or "duplicate" in err_msg.lower():
                total += len(rows)
            elif "42501" in err_msg or (code == "42501"):  # RLS: upsert no permitido, intentar UPDATE fila a fila
                for r in rows:
                    try:
                        payload = {k: v for k, v in r.items() if k in ("siniestros_pagados_ves", "gastos_operativos_ves", "primas_netas_ves") and v is not None}
                        if not payload:
                            continue
                        sb.table("primas_mensuales").update(payload).eq("entity_id", r["entity_id"]).eq("periodo", r["periodo"]).execute()
                        total += 1
                    except Exception:
                        pass
            else:
                try:
                    sb.table("primas_mensuales").insert(rows).execute()
                    total += len(rows)
                except Exception as e2:
                    print(f"[load_resumen_por_empresa] {path.name} hoja {sheet}: upsert {e} | insert {e2}")

    return total


def load_seguro_en_cifras_anual(path: Path, sb: Any) -> int:
    """Carga 'Seguro en Cifras' / cuadros descargables: datos anuales por empresa (periodo YYYY-01-01)."""
    name = path.name.lower()
    year_match = re.search(r"20\d{2}", name)
    year = int(year_match.group(0)) if year_match else 2024
    total = 0
    try:
        xl = pd.ExcelFile(path)
    except Exception:
        return 0
    periodo_str = f"{year}-01-01"
    for sheet_name in xl.sheet_names:
        if sheet_name == "Resumen":
            continue
        for header_row in (5, 8, 10):
            try:
                df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
            except Exception:
                continue
            if df.empty or len(df.columns) < 3:
                continue
            col_empresa = col_primas = None
            for c in df.columns:
                s = str(c).lower()
                if "empresa" in s or "seguros" in s:
                    col_empresa = c
                if "primas" in s:
                    col_primas = c
            if not col_empresa or not col_primas:
                continue
            for _, row in df.iterrows():
                emp = row.get(col_empresa)
                if pd.isna(emp) or not str(emp).strip() or "total" in str(emp).lower():
                    continue
                try:
                    val = float(row.get(col_primas, 0) or 0)
                except (TypeError, ValueError):
                    continue
                primas_ves = val * 1000 if val < 1e9 else val
                norm = normalize_entity_name(str(emp).strip())
                entity_id = get_or_create_entity_id(sb, norm, str(emp).strip())
                if not entity_id:
                    continue
                try:
                    sb.table("primas_mensuales").upsert([{
                        "entity_id": entity_id,
                        "periodo": periodo_str,
                        "primas_netas_ves": round(primas_ves, 2),
                        "primas_netas_usd": None,
                        "siniestros_pagados_ves": None,
                        "siniestros_pagados_usd": None,
                        "gastos_operativos_ves": None,
                        "gastos_operativos_usd": None,
                    }], on_conflict="entity_id,periodo").execute()
                    total += 1
                except Exception:
                    pass
            break
    return total


def load_primas_netas_por_empresa_excel(path: Path, sb: Any) -> int:
    """
    Carga archivos tipo 'primas-netas-cobradas-por-empresa-YYYY.xlsx' de SUDEASEG.
    Varias hojas (una por mes), cabecera en fila 9, columnas: Empresas de Seguros, Primas Netas Cobradas.
    """
    import re
    name = path.name.lower()
    year_match = re.search(r"20\d{2}", name)
    if not year_match:
        return 0
    year = int(year_match.group(0))
    total = 0
    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        print(f"  [primas_netas] Error abriendo {path.name}: {e}")
        return 0
    for sheet in xl.sheet_names:
        sheet_lower = sheet.lower().strip()
        month_num = _MES_SHEET.get(sheet_lower)
        if not month_num:
            continue
        try:
            df = pd.read_excel(path, sheet_name=sheet, header=9)
        except Exception:
            continue
        if df.empty or len(df.columns) < 3:
            continue
        # Columnas típicas: Ranking, Empresas de Seguros, Primas Netas Cobradas (En Miles de Bs.), ...
        col_empresa = None
        col_primas = None
        for c in df.columns:
            s = str(c).lower()
            if "empresa" in s or "seguros" in s:
                col_empresa = c
            if "primas" in s and "netas" in s:
                col_primas = c
        if col_empresa is None:
            col_empresa = df.columns[2] if len(df.columns) > 2 else None
        if col_primas is None:
            col_primas = df.columns[3] if len(df.columns) > 3 else None
        if col_empresa is None or col_primas is None:
            continue
        periodo_str = f"{year}-{month_num:02d}-01"
        rows = []
        for _, row in df.iterrows():
            emp = row.get(col_empresa)
            if pd.isna(emp) or not str(emp).strip():
                continue
            emp_str = str(emp).strip()
            if "total" in emp_str.lower():
                continue
            try:
                val = float(row.get(col_primas, 0) or 0)
            except (TypeError, ValueError):
                continue
            # Valor en miles de Bs. -> guardamos en VES (miles * 1000)
            primas_ves = val * 1000 if val < 1e9 else val
            norm = normalize_entity_name(emp_str)
            entity_id = get_or_create_entity_id(sb, norm, emp_str)
            if not entity_id:
                continue
            rows.append({
                "entity_id": entity_id,
                "periodo": periodo_str,
                "primas_netas_ves": round(primas_ves, 2),
                "primas_netas_usd": None,
                "siniestros_pagados_ves": None,
                "siniestros_pagados_usd": None,
                "gastos_operativos_ves": None,
                "gastos_operativos_usd": None,
            })
        if rows:
            try:
                sb.table("primas_mensuales").upsert(rows, on_conflict="entity_id,periodo").execute()
                total += len(rows)
            except Exception as e:
                err_msg = str(e) if hasattr(e, "__str__") else ""
                if "23505" in err_msg or "duplicate key" in err_msg.lower():
                    total += len(rows)
                else:
                    try:
                        sb.table("primas_mensuales").insert(rows).execute()
                        total += len(rows)
                    except Exception as e2:
                        err2 = str(e2)
                        if "23505" not in err2 and "duplicate" not in err2.lower():
                            print(f"  [primas_netas] {path.name} {sheet}: {e2}")
                        else:
                            total += len(rows)
    return total


def load_excel_to_supabase(path: Path, sb: Any, sheet_name: str | int = 0) -> int:
    """Carga un Excel SUDEASEG: normaliza, mapea y sube a entities + primas_mensuales."""
    raw = load_sudeaseg_excel(path, sheet_name=sheet_name)
    if isinstance(raw, dict):
        raw = raw.get(list(raw.keys())[0], pd.DataFrame())
    df = flatten_multiindex_headers(raw)
    df = impute_nulls_financial(df)
    df = map_columns_to_schema(df)
    if df.empty or "entity_name" not in df.columns:
        return 0
    rows = df_to_primas_rows(df, sb)
    if not rows:
        return 0
    try:
        sb.table("primas_mensuales").upsert(rows, on_conflict="entity_id,periodo").execute()
        return len(rows)
    except Exception as e:
        print(f"[load_excel_to_supabase] upsert error: {e}")
        try:
            sb.table("primas_mensuales").insert(rows).execute()
            return len(rows)
        except Exception as e2:
            print(f"[load_excel_to_supabase] insert error: {e2}")
            return 0


def load_pdf_tables_to_supabase(path: Path, sb: Any) -> int:
    """Extrae tablas de un PDF SUDEASEG y sube las que tengan forma entity + periodo + métricas."""
    extractor = PDFTableExtractor(flavor="lattice")
    tables = extractor.extract_with_camelot(path)
    total = 0
    for t in tables:
        t = flatten_multiindex_headers(t)
        t = impute_nulls_financial(t)
        t = map_columns_to_schema(t)
        if "entity_name" in t.columns and "periodo" in t.columns:
            rows = df_to_primas_rows(t, sb)
            if rows:
                try:
                    sb.table("primas_mensuales").upsert(rows, on_conflict="entity_id,periodo").execute()
                    total += len(rows)
                except Exception:
                    try:
                        sb.table("primas_mensuales").insert(rows).execute()
                        total += len(rows)
                    except Exception as e:
                        print(f"[load_pdf_tables_to_supabase] {e}")
    return total


def _excel_loader_name(path: Path) -> str:
    """Devuelve el nombre del loader que se usará para este Excel (solo para debug)."""
    name_lower = path.name.lower()
    if "primas" in name_lower and ("cobradas" in name_lower or "netas" in name_lower) and "empresa" in name_lower:
        return "primas_netas_por_empresa"
    if "cuadro" in name_lower and "resultados" in name_lower:
        return "cuadro_resultados"
    if "resumen" in name_lower and "empresa" in name_lower:
        return "resumen_por_empresa"
    if ("seguro" in name_lower and "cifras" in name_lower) or ("cuadros" in name_lower and "descargables" in name_lower):
        return "seguro_en_cifras_anual"
    return "excel_generico"


def list_files_for_year(raw_dir: Path, year: int) -> tuple[list[Path], list[Path]]:
    """Lista archivos Excel y PDF cuyo año (del nombre) coincide con year. Útil para dry-run."""
    excel_files = [p for p in list(raw_dir.rglob("*.xlsx")) + list(raw_dir.rglob("*.xls")) if _year_from_path(p) == year]
    pdf_files = [p for p in raw_dir.rglob("*.pdf") if _year_from_path(p) == year]
    return excel_files, pdf_files


def run_full_pipeline(
    raw_dir: Path | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    target_year: int | None = None,
    debug: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Recorre data/raw (incl. subcarpetas como xlsx/): Excel y PDF, carga a Supabase.
    - target_year: si se indica, solo procesa ese año (equivalente a year_min=year_max=target_year).
    - year_min/year_max: rango de años (ignorado si target_year está definido).
    - debug: listado verbose (archivos, año detectado, loader, filas por archivo).
    - dry_run: solo lista archivos que se procesarían, sin conectar a Supabase ni cargar.
    Devuelve {"excel": n, "pdf": m, "primas_rows": total, "detalle": [...] si debug}.
    """
    raw_dir = raw_dir or DATA_RAW
    if target_year is not None:
        year_min, year_max = target_year, target_year
    stats: dict[str, Any] = {"excel": 0, "pdf": 0, "primas_rows": 0}
    if debug:
        stats["detalle"] = []

    excel_files = list(raw_dir.rglob("*.xlsx")) + list(raw_dir.rglob("*.xls"))
    if year_min is not None and year_max is not None:
        skipped = [p for p in excel_files if not _year_from_path(p) or not (year_min <= _year_from_path(p) <= year_max)]
        excel_files = [p for p in excel_files if _year_from_path(p) and year_min <= _year_from_path(p) <= year_max]
        if debug and skipped:
            for p in skipped[:20]:
                stats.setdefault("detalle", []).append({"tipo": "excel_omitido", "archivo": p.name, "año": _year_from_path(p)})
            if len(skipped) > 20:
                stats.setdefault("detalle", []).append({"tipo": "excel_omitido", "archivo": f"... y {len(skipped) - 20} más", "año": None})
        if excel_files:
            print(f"  [ETL] Año objetivo: {year_min}-{year_max}. Excel a procesar: {len(excel_files)}")

    if dry_run:
        print("  [DRY-RUN] Archivos que se procesarían (sin cargar a Supabase):")
        for p in sorted(excel_files):
            print(f"    Excel: {p.relative_to(raw_dir)} (año {_year_from_path(p)}) -> {_excel_loader_name(p)}")
        pdf_files = list(raw_dir.rglob("*.pdf"))
        if year_min is not None and year_max is not None:
            pdf_files = [p for p in pdf_files if _year_from_path(p) and year_min <= _year_from_path(p) <= year_max]
        for p in sorted(pdf_files):
            print(f"    PDF:  {p.relative_to(raw_dir)} (año {_year_from_path(p)})")
        print(f"  Total: {len(excel_files)} Excel, {len(pdf_files)} PDF")
        return stats

    sb = get_supabase_client()
    if not sb:
        print("Supabase no configurado. Configura .env (o ejecuta con --dry-run para solo listar archivos).")
        return {"excel": 0, "pdf": 0, "primas_rows": 0}
    if target_year is not None:
        year_min, year_max = target_year, target_year
    stats: dict[str, Any] = {"excel": 0, "pdf": 0, "primas_rows": 0}
    if debug:
        stats["detalle"] = []

    excel_files = list(raw_dir.rglob("*.xlsx")) + list(raw_dir.rglob("*.xls"))
    if year_min is not None and year_max is not None:
        skipped = [p for p in excel_files if not _year_from_path(p) or not (year_min <= _year_from_path(p) <= year_max)]
        excel_files = [p for p in excel_files if _year_from_path(p) and year_min <= _year_from_path(p) <= year_max]
        if debug and skipped:
            for p in skipped[:20]:
                y = _year_from_path(p)
                stats.setdefault("detalle", []).append({"tipo": "excel_omitido", "archivo": p.name, "año": y})
            if len(skipped) > 20:
                stats.setdefault("detalle", []).append({"tipo": "excel_omitido", "archivo": f"... y {len(skipped) - 20} más", "año": None})
        if excel_files:
            print(f"  [ETL] Año objetivo: {year_min}-{year_max}. Excel a procesar: {len(excel_files)}")
    for i, path in enumerate(excel_files):
        if not debug and ((i + 1) % 10 == 0 or i == 0):
            print(f"  Excel {i+1}/{len(excel_files)}...", flush=True)
        name_lower = path.name.lower()
        loader = _excel_loader_name(path)
        if "primas" in name_lower and ("cobradas" in name_lower or "netas" in name_lower) and "empresa" in name_lower:
            n = load_primas_netas_por_empresa_excel(path, sb)
        elif "cuadro" in name_lower and "resultados" in name_lower:
            n = load_cuadro_resultados_excel(path, sb)
        elif "resumen" in name_lower and "empresa" in name_lower:
            n = load_resumen_por_empresa_excel(path, sb)
        elif ("seguro" in name_lower and "cifras" in name_lower) or ("cuadros" in name_lower and "descargables" in name_lower):
            n = load_seguro_en_cifras_anual(path, sb)
        else:
            n = load_excel_to_supabase(path, sb)
        if n:
            stats["excel"] += 1
            stats["primas_rows"] += n
            if debug:
                stats.setdefault("detalle", []).append({"tipo": "excel", "archivo": path.name, "loader": loader, "filas": n, "año": _year_from_path(path)})
                print(f"  [OK] {path.name} (año {_year_from_path(path)}) -> {loader}: {n} filas")
            else:
                print(f"  {path.name}: {n} filas -> Supabase")
        elif debug:
            stats.setdefault("detalle", []).append({"tipo": "excel", "archivo": path.name, "loader": loader, "filas": 0, "año": _year_from_path(path)})
            print(f"  [--] {path.name} (año {_year_from_path(path)}) -> {loader}: 0 filas")

    pdf_files = list(raw_dir.rglob("*.pdf"))
    if year_min is not None and year_max is not None:
        skipped_pdf = [p for p in pdf_files if not _year_from_path(p) or not (year_min <= _year_from_path(p) <= year_max)]
        pdf_files = [p for p in pdf_files if _year_from_path(p) and year_min <= _year_from_path(p) <= year_max]
        if debug and skipped_pdf:
            for p in skipped_pdf[:10]:
                stats.setdefault("detalle", []).append({"tipo": "pdf_omitido", "archivo": p.name, "año": _year_from_path(p)})
        if pdf_files:
            print(f"  [ETL] PDF a procesar: {len(pdf_files)}")
    for path in pdf_files:
        n = load_pdf_tables_to_supabase(path, sb)
        if n:
            stats["pdf"] += 1
            stats["primas_rows"] += n
            if debug:
                stats.setdefault("detalle", []).append({"tipo": "pdf", "archivo": path.name, "filas": n, "año": _year_from_path(path)})
                print(f"  [OK] {path.name} (año {_year_from_path(path)}) -> PDF tablas: {n} filas")
            else:
                print(f"  {path.name}: {n} filas -> Supabase")
        elif debug:
            stats.setdefault("detalle", []).append({"tipo": "pdf", "archivo": path.name, "filas": 0, "año": _year_from_path(path)})
            print(f"  [--] {path.name} (año {_year_from_path(path)}): 0 filas")
    return stats
