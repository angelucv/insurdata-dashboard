"""
Seguro en Cifras: índice de fuentes, entidades y vaciado coherente en disco.
Solo anuarios (Seguro en Cifras / Seguros en Cifras / seguros-en-cifra).
Estructura en data/audit/seguro_en_cifras/ para luego cargar a base de datos.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from config.anuarios_paths import (
    ensure_anuarios_dirs,
    SEGURO_EN_CIFRAS_INDICE,
    SEGURO_EN_CIFRAS_ENTIDADES,
    SEGURO_EN_CIFRAS_VARIABLES,
    SEGURO_EN_CIFRAS_VACIADO,
    INDICE_FUENTES_CSV,
    ENTIDADES_CSV,
    METRICAS_CSV,
    VACIADO_ENTIDADES_CSV,
    INDICE_CUADROS_CSV,
)
from src.etl.transformers import normalize_entity_name


# Patrones para reconocer archivos de anuario "Seguro en Cifras"
ANUARIO_PATTERNS = [
    re.compile(r"Seguros?-en-Cifras?-(\d{4})", re.I),
    re.compile(r"Seguros?-en-Cifras?-(\d{4})-(\d{4})", re.I),
    re.compile(r"seguros?-en-cifra-(\d{4})", re.I),
    re.compile(r"seguro-en-cifras-(\d{4})", re.I),
    re.compile(r"Seguro\s*en\s*Cifras\s*(\d{4})", re.I),
    re.compile(r"1\.Seguro-en-Cifras-(\d{4})", re.I),
    re.compile(r"cuadros\s*descargables.*[Ss]eguro\s*en\s*cifras\s*(\d{4})", re.I),
]


def _year_from_anuario_path(path: Path) -> tuple[int | None, str | None]:
    """Extrae año (y segundo año si es rango) del nombre de archivo de anuario."""
    name = path.name
    for pat in ANUARIO_PATTERNS:
        m = pat.search(name)
        if m:
            y1 = int(m.group(1))
            y2 = int(m.group(2)) if m.lastindex and m.lastindex >= 2 else None
            return y1, (str(y2) if y2 else None)
    return None, None


def _is_anuario_file(path: Path) -> bool:
    """True si el archivo es un anuario Seguro en Cifras (no boletín mensual)."""
    name = path.name.lower()
    if "boletin" in name or "bolet" in name:
        return False
    if "cifras" not in name and "cifra" not in name:
        return False
    if "seguro" in name or "seguros" in name:
        return True
    if "cuadros descargables" in name and "cifras" in name:
        return True
    return False


def list_anuario_sources() -> list[dict[str, Any]]:
    """Lista todas las fuentes de anuarios en data/raw (PDF y Excel)."""
    sources = []
    for ext in ("*.pdf", "*.xlsx"):
        for path in DATA_RAW.rglob(ext):
            if not _is_anuario_file(path):
                continue
            y1, y2 = _year_from_anuario_path(path)
            if y1 is None:
                continue
            try:
                rel = path.relative_to(DATA_RAW)
            except ValueError:
                rel = path.name
            sources.append({
                "anio": y1,
                "anio_fin": y2,
                "nombre_archivo": path.name,
                "tipo": path.suffix.lower().replace(".", ""),
                "ruta_relativa": str(rel).replace("\\", "/"),
                "tiene_entidades": None,
                "tiene_primas": None,
                "tiene_siniestros": None,
                "observaciones": "",
            })
    sources.sort(key=lambda x: (x["anio"], x["nombre_archivo"]))
    return sources


def build_indice_fuentes() -> Path:
    """Construye indice/anuario_fuentes.csv con todas las fuentes de anuarios."""
    ensure_anuarios_dirs()
    sources = list_anuario_sources()
    df = pd.DataFrame(sources)
    INDICE_FUENTES_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(INDICE_FUENTES_CSV, index=False, encoding="utf-8-sig")
    return INDICE_FUENTES_CSV


def _detect_entity_column_and_header(df: pd.DataFrame) -> tuple[int, int]:
    """En un DataFrame de cuadro anuario, detecta columna de entidad y fila de cabecera."""
    for row_idx in range(min(15, len(df))):
        row = df.iloc[row_idx]
        for col_idx in range(min(10, len(row))):
            val = row.iloc[col_idx]
            if pd.isna(val):
                continue
            s = str(val).lower().strip()
            # Evitar titulos de seccion (ej. "EMPRESAS DE SEGUROS")
            if "empresas de seguros" in s or s.startswith("empresas de seguros"):
                continue
            if "nombre" in s and "empresa" in s:
                return col_idx, row_idx
            if s == "empresa" or (s.startswith("empresa") and len(s) < 25 and "empresas" not in s):
                return col_idx, row_idx
            if "empresa" in s and ("seguro" in s or "aseguradora" in s) and "nombre" in s:
                return col_idx, row_idx
    return 0, 0


def _column_to_metric_name(col_label: str, cuadro: str) -> tuple[str, str | None]:
    """Mapea etiqueta de columna a metric_name canónico y opcional ramo."""
    s = (col_label or "").strip().lower()
    if not s or s in ("%", "nan"):
        return "porcentaje", None
    # TOTAL según cuadro: primas (4, 5A-C), siniestros (7, 8A-C), reservas (12, 13...)
    if s == "total" or (s.startswith("total") and len(s) < 10):
        c = cuadro.upper()
        if "4" in c or "5A" in c or "5B" in c or "5C" in c:
            return "primas_netas_cobradas", None
        if "7" in c or "8A" in c or "8B" in c or "8C" in c:
            return "siniestros_pagados", None
        if "12" in c or "13" in c or "14" in c or "15" in c or "16" in c or "17" in c or "18" in c or "19" in c:
            return "reservas_primas", None
        if "35" in c:
            return "capital_garantia", None
        if "34" in c:
            return "primas_netas_cobradas", None
        return "resultados_economicos", None
    if "total" in s and ("prima" in s or "cobrada" in s):
        return "primas_netas_cobradas", None
    if "prima" in s and "neta" in s:
        if "hospitaliz" in s or "autom" in s or "vida" in s or "incendio" in s or "colectivo" in s or "casco" in s or "ramos" in s:
            return "primas_netas_por_ramo", s[:50]
        return "primas_netas_por_ramo", None
    # Cuadros 4, 5A-C: columnas por ramo sin palabra 'prima' en cabecera
    c = cuadro.upper()
    if "4" in c or "5A" in c or "5B" in c or "5C" in c:
        if "hospitaliz" in s or "autom" in s or "colectivo" in s or "casco" in s or "ramos" in s or "vida" in s or "resto" in s:
            return "primas_netas_por_ramo", s[:50]
    # Cuadros 7, 8A-C: prestaciones/siniestros por ramo
    if "7" in c or "8A" in c or "8B" in c or "8C" in c:
        if "hospitaliz" in s or "autom" in s or "colectivo" in s or "casco" in s or "ramos" in s or "resto" in s:
            return "siniestros_pagados", s[:50]
    if "prima" in s and ("bruta" in s or "directo" in s or "reaseguro" in s):
        return "primas_netas_cobradas", None
    if "siniestro" in s or "prestacion" in s:
        return "siniestros_pagados", None
    if "reserva" in s:
        if "retencion" in s or "propia" in s or "empresa" in s:
            return "reservas_tecnicas", None
        if "reasegurador" in s or "cargo" in s:
            return "reservas_primas", None
        return "reservas_primas", None
    if "gasto" in s and "administr" in s:
        return "gastos_administracion", None
    if "gasto" in s and ("operativo" in s or "produccion" in s):
        return "gastos_produccion", None
    if "capital" in s or "garantia" in s or "deposito" in s:
        if "pagado" in s:
            return "capital_pagado", None
        return "capital_garantia", None
    if "comision" in s or "adquisicion" in s:
        return "comisiones_gastos_adquisicion", None
    if "resultado" in s or "ganancia" in s or "perdida" in s or "ingreso" in s:
        return "resultados_economicos", None
    if "inversion" in s:
        return "inversiones_reservas", None
    # Cuadros 23: comisiones y gastos por ramo
    if "23" in c and len(s) > 2:
        return "comisiones_gastos_adquisicion", s[:50]
    # Cuadros 34/35: seguro directo, reaseguro, total
    if "34" in c or "35" in c:
        if "directo" in s or "reaseguro" in s:
            return "primas_netas_cobradas", None
    return "otro", s[:50] if len(s) > 3 else None


# Mapeo de etiquetas de cabecera (tablas PDF) a metric_name canónico
_HEADER_TO_METRIC = [
    (["capital suscrito", "capital suscrito"], "capital_garantia"),
    (["capital pagado", "capital pagado"], "capital_pagado"),
    (["garantía", "garantia", "depósito", "deposito"], "garantia_deposito"),
    (["primas netas", "primas cobradas"], "primas_netas_cobradas"),
    (["siniestros pagados", "prestaciones"], "siniestros_pagados"),
    (["reservas técnicas", "reservas tecnicas"], "reservas_tecnicas"),
    (["reserva", "reservas"], "reservas_primas"),
    (["gastos administración", "gastos administracion"], "gastos_administracion"),
    (["gastos producción", "gastos produccion"], "gastos_produccion"),
    (["comisiones", "adquisición", "adquisicion"], "comisiones_gastos_adquisicion"),
    (["resultado", "ganancias", "pérdidas", "perdidas"], "resultados_economicos"),
]


def _parse_numeric_cell(val: Any) -> float | None:
    """
    Convierte celda a número. Acepta formato europeo (1.265.377 = miles, 0,17 = decimal).
    Retorna None si no es un número válido.
    """
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val) if not (isinstance(val, float) and (val != val)) else None
    s = str(val).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    # Formato europeo: 1.265.377 (miles) y 0,17 (decimal)
    s_clean = s.replace(".", "").replace(",", ".")
    try:
        return float(s_clean)
    except ValueError:
        return None


def _header_text_to_metric(header: str) -> str:
    s = (header or "").lower().strip()
    if not s or len(s) < 2:
        return "otro"
    for keywords, metric in _HEADER_TO_METRIC:
        if any(kw in s for kw in keywords):
            return metric
    if "prima" in s:
        return "primas_netas_por_ramo"
    if "siniestro" in s or "prestacion" in s:
        return "siniestros_pagados"
    return "otro"


def _metric_from_header_or_subheaders(
    df: pd.DataFrame, header_row_idx: int, col_idx: int, main_header: str
) -> str:
    """Usa cabecera principal; si da 'otro', prueba 1-2 filas siguientes (subcabeceras)."""
    m = _header_text_to_metric(main_header)
    if m != "otro":
        return m
    for offset in (1, 2):
        r = header_row_idx + offset
        if r >= len(df) or col_idx >= len(df.columns):
            break
        sub = df.iloc[r].iloc[col_idx]
        if pd.notna(sub) and str(sub).strip():
            m = _header_text_to_metric(str(sub).strip())
            if m != "otro":
                return m
    return "otro"


def _normalize_cuadro_titulo_to_id(titulo: str) -> str:
    """
    Normaliza titulo de cuadro en PDF (ej. 'Cuadro No. 5-A  EMPRESAS...') a id alineado con indice_cuadros (ej. 'Cuadro 5A').
    """
    if not titulo or not isinstance(titulo, str):
        return titulo or "Cuadro PDF"
    s = titulo.strip()
    # Buscar patron No. N o N-A o N-A o Nº N
    m = re.search(r"(?:no\.?|nro\.?|n[uº°])\s*(\d+)\s*[-]?\s*([a-f])?", s, re.I)
    if m:
        num = m.group(1)
        letra = (m.group(2) or "").upper()
        return f"Cuadro {num}{letra}".strip()
    m = re.search(r"cuadro\s+(\d+)\s*([a-f])?", s, re.I)
    if m:
        return f"Cuadro {m.group(1)}{(m.group(2) or '').upper()}".strip()
    return s[:50]


def _load_indice_cuadros_metricas() -> dict[str, list[str]]:
    """Carga indice_cuadros.csv y devuelve dict cuadro_id -> lista de metric_name esperados."""
    out = {}
    if not INDICE_CUADROS_CSV.exists():
        return out
    try:
        df = pd.read_csv(INDICE_CUADROS_CSV)
        if "cuadro_id" not in df.columns or "metricas_esperadas" not in df.columns:
            return out
        for _, row in df.iterrows():
            cid = str(row["cuadro_id"]).strip()
            me = str(row.get("metricas_esperadas", "")).strip()
            if me:
                out[cid] = [x.strip() for x in me.split(",") if x.strip()]
    except Exception:
        pass
    return out


def _nombre_archivo_to_tables_csv(nombre_archivo: str) -> str:
    """De nombre de archivo fuente (ej. Seguro-en-Cifras-1970.pdf) a nombre en by_source (Seguro-en-Cifras-1970_tables.csv)."""
    base = nombre_archivo
    for ext in (".pdf", ".xlsx"):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
            break
    return base.strip() + "_tables.csv"


def _procesar_bloque_tabla_pdf(
    df: pd.DataFrame,
    header_row_idx: int,
    entity_col: int,
    anio: int,
    source_file: str,
    cuadro_actual: str,
    max_filas: int = 400,
) -> tuple[list[dict], list[dict], int]:
    """Procesa un bloque de tabla (desde header_row_idx). Retorna (entidades, metricas, filas_consumidas)."""
    rows_ent = []
    rows_met = []
    headers = df.iloc[header_row_idx].astype(str).tolist()
    data_start = header_row_idx + 1
    end_row = min(data_start + max_filas, len(df))
    skip_patterns = (
        "indice", "cuadro", "página", "pagina", "titulo",
        "resumen", "resultados", "empresas de seguros", "inscripción", "nro.",
    )
    filas_consumidas = 0

    for row_idx in range(data_start, end_row):
        row = df.iloc[row_idx]
        entity_name = row.iloc[entity_col] if entity_col < len(row) else None
        if pd.isna(entity_name) or not str(entity_name).strip():
            filas_consumidas += 1
            continue
        entity_str = str(entity_name).strip()
        if any(p in entity_str.lower() for p in skip_patterns):
            filas_consumidas += 1
            continue
        if "fuente:" in entity_str.lower() or "superintendencia" in entity_str.lower():
            break
        if "total" in entity_str.lower() and row_idx > data_start + 3:
            break
        # Celda con varias entidades (una por linea): anadir entidades y, si hay columnas con valores multilinea, metricas
        if "\n" in entity_str:
            entity_lines = [
                line.strip() for line in entity_str.split("\n")
                if line.strip() and not any(p in line.lower() for p in skip_patterns)
            ]
            for line in entity_lines:
                norm = normalize_entity_name(line)
                if norm and len(norm) >= 3:
                    rows_ent.append({
                        "anio": anio,
                        "source_file": source_file,
                        "entity_name": line,
                        "entity_normalized_name": norm,
                    })
            # Misma fila: columnas con valores multilinea (uno por entidad, mismo orden)
            for col_idx in range(entity_col + 1, min(entity_col + 20, len(row))):
                if col_idx >= len(headers):
                    break
                header = (headers[col_idx] if col_idx < len(headers) else "").strip()
                val = row.iloc[col_idx]
                if pd.isna(val):
                    continue
                cell_str = str(val).strip()
                if "\n" not in cell_str:
                    v = _parse_numeric_cell(val)
                    if v is not None and len(entity_lines) == 1:
                        metric_name = _metric_from_header_or_subheaders(df, header_row_idx, col_idx, header)
                        if metric_name == "otro" and not header:
                            metric_name = "valor_numerico"
                        rows_met.append({
                            "anio": anio,
                            "source_file": source_file,
                            "cuadro_or_seccion": cuadro_actual,
                            "entity_name": entity_lines[0] if entity_lines else "",
                            "metric_name": metric_name,
                            "value": round(v, 4),
                            "unit": "miles_Bs",
                            "ramo_opcional": "",
                        })
                    continue
                value_lines = [x.strip() for x in cell_str.split("\n") if x.strip()]
                nums = []
                for part in value_lines:
                    n = _parse_numeric_cell(part)
                    if n is not None:
                        nums.append(n)
                if not nums:
                    continue
                n_pairs = min(len(entity_lines), len(nums))
                metric_name = _metric_from_header_or_subheaders(df, header_row_idx, col_idx, header)
                if metric_name == "otro" and not header:
                    metric_name = "valor_numerico"
                for i in range(n_pairs):
                    ent_line = entity_lines[i]
                    num_val = nums[i]
                    norm = normalize_entity_name(ent_line)
                    if not norm or len(norm) < 3:
                        continue
                    rows_met.append({
                        "anio": anio,
                        "source_file": source_file,
                        "cuadro_or_seccion": cuadro_actual,
                        "entity_name": ent_line,
                        "metric_name": metric_name,
                        "value": round(num_val, 4),
                        "unit": "miles_Bs",
                        "ramo_opcional": "",
                    })
            filas_consumidas += 1
            continue
        norm = normalize_entity_name(entity_str)
        if not norm or len(norm) < 3:
            filas_consumidas += 1
            continue

        rows_ent.append({
            "anio": anio,
            "source_file": source_file,
            "entity_name": entity_str,
            "entity_normalized_name": norm,
        })
        for col_idx in range(entity_col + 1, min(entity_col + 20, len(row))):
            if col_idx >= len(headers):
                break
            val = row.iloc[col_idx]
            v = _parse_numeric_cell(val)
            if v is None:
                continue
            header = headers[col_idx] if col_idx < len(headers) else ""
            metric_name = _header_text_to_metric(header)
            if metric_name == "otro" and not header.strip():
                metric_name = "valor_numerico"
            rows_met.append({
                "anio": anio,
                "source_file": source_file,
                "cuadro_or_seccion": cuadro_actual,
                "entity_name": entity_str,
                "metric_name": metric_name,
                "value": round(v, 4),
                "unit": "miles_Bs",
                "ramo_opcional": "",
            })
        filas_consumidas += 1
    return rows_ent, rows_met, filas_consumidas


def vaciar_from_pdf_tables_csv(
    csv_path: Path, anio: int, source_file: str
) -> tuple[list[dict], list[dict]]:
    """
    Vacía un CSV de tablas extraídas de PDF (by_source/*_tables.csv).
    Busca todos los bloques con cabecera 'Nombre (de la) Empresa' y columnas numéricas.
    Retorna (rows_entidades, rows_metricas).
    """
    rows_entidades = []
    rows_metricas = []
    try:
        df = pd.read_csv(csv_path, header=None, encoding="utf-8", on_bad_lines="skip", low_memory=False)
    except Exception:
        return rows_entidades, rows_metricas
    if df.empty or df.shape[0] < 5:
        return rows_entidades, rows_metricas

    cuadro_actual = "Cuadro PDF"
    seen_entities_anio = set()
    idx = 0
    while idx < len(df):
        row = df.iloc[idx]
        row_str = " ".join(str(c) for c in row.dropna().astype(str))
        if "cuadro" in row_str.lower() and ("no" in row_str.lower() or "nro" in row_str.lower() or "n°" in row_str or "nº" in row_str):
            raw_titulo = row_str[:80].replace("\n", " ").strip()
            cuadro_actual = _normalize_cuadro_titulo_to_id(raw_titulo) or raw_titulo
        entity_col = None
        for col_idx in range(min(15, len(row))):
            val = row.iloc[col_idx]
            if pd.isna(val):
                continue
            s = str(val).lower().strip()
            if "nombre" in s and "empresa" in s and "inscripción" not in s and "nro" not in s:
                entity_col = col_idx
                break
            if s.strip() == "empresa" or (s.startswith("empresa") and len(s) < 50 and "empresas de seguros" not in s):
                entity_col = col_idx
                break
        if entity_col is not None:
            ent, met, filas_consumidas = _procesar_bloque_tabla_pdf(
                df, idx, entity_col, anio, source_file, cuadro_actual
            )
            for r in ent:
                k = (r["anio"], r["entity_normalized_name"])
                if k not in seen_entities_anio:
                    seen_entities_anio.add(k)
                    rows_entidades.append(r)
            rows_metricas.extend(met)
            idx += 1 + filas_consumidas
            continue
        idx += 1

    return rows_entidades, rows_metricas


def get_by_source_tables_path(anio: int, nombre_archivo: str) -> Path | None:
    """Ruta al CSV de tablas extraídas en by_source para este año/archivo, si existe."""
    name = _nombre_archivo_to_tables_csv(nombre_archivo)
    path = Path(DATA_AUDIT_BY_SOURCE) / name
    return path if path.exists() else None


def vaciar_anuario_por_anio(
    anio: int, nombre_archivo: str, tipo: str, ruta_relativa: str
) -> tuple[list[dict], list[dict], dict[str, Any]]:
    """
    Vacía un único año. Si es xlsx: 2024 cuadros descargables -> Excel 2024; resto -> Excel Adobe.
    Si es pdf usa by_source *_tables.csv si existe.
    Retorna (rows_entidades, rows_metricas, info_extra).
    """
    source_file = nombre_archivo
    if tipo == "xlsx":
        excel_path = DATA_RAW / ruta_relativa.replace("/", "\\")
        if not excel_path.exists():
            return [], [], {"origen": "excel", "error": "archivo no encontrado"}
        if anio == 2024 and "cuadros descargables" in nombre_archivo.lower():
            ent, met = vaciar_excel_anuario_2024(excel_path)
            return ent, met, {"origen": "excel_2024", "entidades": len(ent), "metricas": len(met)}
        ent, met = vaciar_excel_adobe_anuario(excel_path, anio)
        return ent, met, {"origen": "excel_adobe", "entidades": len(ent), "metricas": len(met)}

    tables_path = get_by_source_tables_path(anio, nombre_archivo)
    if tables_path and tables_path.exists():
        ent, met = vaciar_from_pdf_tables_csv(tables_path, anio, source_file)
        return ent, met, {"origen": "pdf_tables_csv", "entidades": len(ent), "metricas": len(met)}
    return [], [], {"origen": "pdf", "tables_csv": str(tables_path) if tables_path else "no existe", "entidades": 0, "metricas": 0}


def run_vaciado_secuencial() -> tuple[list[dict], list[dict], list[dict]]:
    """
    Ejecuta vaciado por cada año en orden ascendente (del más antiguo al más reciente).
    Usa indice/anuario_fuentes.csv. Retorna (all_entidades, all_metricas, resumen_por_anio).
    """
    ensure_anuarios_dirs()
    build_indice_fuentes()
    if not INDICE_FUENTES_CSV.exists():
        return [], [], []

    fuentes = pd.read_csv(INDICE_FUENTES_CSV)
    # Preferir XLSX (Adobe) sobre PDF cuando existan ambos para el mismo año
    fuentes["_prefer"] = (fuentes["tipo"] == "xlsx").astype(int)
    fuentes_por_anio = (
        fuentes.sort_values(["anio", "_prefer"], ascending=[True, False])
        .groupby("anio")
        .first()
        .reset_index()
    )
    fuentes_por_anio = fuentes_por_anio.drop(columns=["_prefer"], errors="ignore").sort_values("anio", ascending=True)

    all_entidades = []
    all_metricas = []
    resumen_por_anio = []

    for _, row in fuentes_por_anio.iterrows():
        anio = int(row["anio"])
        nombre_archivo = row["nombre_archivo"]
        tipo = row["tipo"]
        ruta = row.get("ruta_relativa", "")

        ent, met, info = vaciar_anuario_por_anio(anio, nombre_archivo, tipo, ruta)
        all_entidades.extend(ent)
        all_metricas.extend(met)
        resumen_por_anio.append({
            "anio": anio,
            "nombre_archivo": nombre_archivo,
            "tipo": tipo,
            "entidades": len(ent),
            "metricas": len(met),
            "origen": info.get("origen", ""),
            "observacion": info.get("error", info.get("tables_csv", "")),
        })

    # Deduplicar entidades por (anio, entity_normalized_name)
    seen = set()
    unique_ent = []
    for r in all_entidades:
        k = (r["anio"], r["entity_normalized_name"])
        if k not in seen:
            seen.add(k)
            unique_ent.append(r)

    # Consolidar metricas: mismo (anio, entity_name, metric_name) -> sumar value para no perder datos de varios bloques
    if all_metricas:
        df_met = pd.DataFrame(all_metricas)
        if "value" in df_met.columns and "anio" in df_met.columns and "entity_name" in df_met.columns and "metric_name" in df_met.columns:
            key = ["anio", "entity_name", "metric_name"]
            df_met["value"] = pd.to_numeric(df_met["value"], errors="coerce")
            agg_dict = {"value": ("value", "sum")}
            for c in ["source_file", "cuadro_or_seccion", "unit", "ramo_opcional"]:
                if c in df_met.columns:
                    agg_dict[c] = (c, "first")
            agg = df_met.groupby(key, as_index=False).agg(**agg_dict)
            all_metricas = agg.to_dict("records")

    # Escribir vaciado consolidado
    VACIADO_ENTIDADES_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(unique_ent).to_csv(VACIADO_ENTIDADES_CSV, index=False, encoding="utf-8-sig")
    pd.DataFrame(all_metricas).to_csv(METRICAS_CSV, index=False, encoding="utf-8-sig")

    return unique_ent, all_metricas, resumen_por_anio


def vaciar_excel_adobe_anuario(excel_path: Path, anio: int) -> tuple[list[dict], list[dict]]:
    """
    Vacía un Excel convertido con Adobe (una hoja 'Table 1', rejilla tipo PDF).
    Busca bloques con cabecera 'Empresa' y extrae entidades + columnas numéricas.
    Retorna (rows_entidades, rows_metricas).
    """
    excel_path = Path(excel_path)
    rows_entidades = []
    rows_metricas = []
    source_file = excel_path.name
    try:
        xl = pd.ExcelFile(excel_path)
    except Exception:
        return rows_entidades, rows_metricas
    sheet = "Table 1" if "Table 1" in xl.sheet_names else (xl.sheet_names[0] if xl.sheet_names else None)
    if not sheet:
        return rows_entidades, rows_metricas
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet, header=None)
    except Exception:
        return rows_entidades, rows_metricas
    if df.empty or df.shape[0] < 10:
        return rows_entidades, rows_metricas

    skip_patterns = (
        "indice", "cuadro", "página", "pagina", "titulo", "resumen", "resultados",
        "empresas de seguros", "inscripción", "nro.", "total empresas", "fuente:",
    )

    # Encontrar todas las celdas "Empresa" (inicio de bloque)
    bloques = []
    for i in range(len(df)):
        for j in range(min(25, len(df.columns))):
            if pd.isna(df.iloc[i].iloc[j]):
                continue
            s = str(df.iloc[i].iloc[j]).strip().lower()
            if s == "empresa" or (s.startswith("empresa") and len(s) < 30 and "empresas de seguros" not in s):
                bloques.append((i, j))

    seen_ent = set()
    for header_row, entity_col in bloques:
        data_start = header_row + 1
        if data_start + 1 < len(df):
            next_row = df.iloc[header_row + 1]
            cell0 = str(next_row.iloc[entity_col]).strip().lower() if entity_col < len(next_row) else ""
            c1 = str(next_row.iloc[entity_col + 1]).strip().lower() if entity_col + 1 < len(next_row) else ""
            if (not cell0 or cell0 == "nan") and ("total" in c1 or "prima" in c1 or "siniestro" in c1 or "directo" in c1):
                data_start = header_row + 2
        headers_main = df.iloc[header_row].astype(str).tolist()
        headers_sub = df.iloc[header_row + 1].astype(str).tolist() if header_row + 1 < len(df) else []

        for row_idx in range(data_start, min(data_start + 250, len(df))):
            row = df.iloc[row_idx]
            entity_name = row.iloc[entity_col] if entity_col < len(row) else None
            if pd.isna(entity_name) or not str(entity_name).strip():
                continue
            entity_str = str(entity_name).strip()
            if any(p in entity_str.lower() for p in skip_patterns):
                continue
            if "total" in entity_str.lower() and row_idx > data_start + 2:
                break
            if "fuente:" in entity_str.lower() or "superintendencia" in entity_str.lower():
                break
            norm = normalize_entity_name(entity_str)
            if not norm or len(norm) < 3:
                continue

            if (anio, norm) not in seen_ent:
                seen_ent.add((anio, norm))
                rows_entidades.append({
                    "anio": anio,
                    "source_file": source_file,
                    "entity_name": entity_str,
                    "entity_normalized_name": norm,
                })

            for col_idx in range(entity_col + 1, min(entity_col + 65, len(row))):
                val = row.iloc[col_idx]
                v = _parse_numeric_cell(val)
                if v is None:
                    continue
                header = ""
                if col_idx < len(headers_sub) and headers_sub[col_idx] and str(headers_sub[col_idx]).strip().lower() not in ("nan", ""):
                    header = str(headers_sub[col_idx]).strip()
                if not header and col_idx < len(headers_main):
                    header = str(headers_main[col_idx]).strip()
                metric_name = _header_text_to_metric(header)
                if metric_name == "otro" and not header:
                    metric_name = "valor_numerico"
                rows_metricas.append({
                    "anio": anio,
                    "source_file": source_file,
                    "cuadro_or_seccion": "Adobe Table 1",
                    "entity_name": entity_str,
                    "metric_name": metric_name,
                    "value": round(v, 4),
                    "unit": "miles_Bs",
                    "ramo_opcional": "",
                })

    return rows_entidades, rows_metricas


def vaciar_excel_anuario_2024(excel_path: Path) -> tuple[list[dict], list[dict]]:
    """
    Vacía el Excel 'cuadros descargables_Seguro en cifras 2024.xlsx'.
    Retorna (rows_entidades, rows_metricas) para anuario_entidades y anuario_metricas.
    """
    excel_path = Path(excel_path)
    rows_entidades = []
    rows_metricas = []
    anio = 2024
    source_file = excel_path.name

    try:
        xl = pd.ExcelFile(excel_path)
    except Exception as e:
        return rows_entidades, rows_metricas

    # Hojas que son cuadros de datos (empresa x variables)
    cuadro_sheets = [s for s in xl.sheet_names if s.startswith("Cuadro ") or s == "Resumen"]
    if not cuadro_sheets:
        return rows_entidades, rows_metricas

    for sheet in cuadro_sheets:
        if sheet == "Resumen":
            continue
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet, header=None)
        except Exception:
            continue
        if df.empty or df.shape[0] < 5:
            continue

        col_ent, header_row = _detect_entity_column_and_header(df)
        if header_row >= df.shape[0] - 1:
            continue

        headers = df.iloc[header_row].astype(str).tolist()
        data_start = header_row + 1
        # Cabecera doble (ej. Cuadro 34/35): fila siguiente tiene subcabeceras (Seguro Directo, Total)
        if header_row + 1 < len(df):
            next_row = df.iloc[header_row + 1]
            cell0 = str(next_row.iloc[col_ent]).strip().lower() if col_ent < len(next_row) else ""
            subhead = str(next_row.iloc[col_ent + 1]).strip().lower() if col_ent + 1 < len(next_row) else ""
            if (not cell0 or cell0 == "nan") and (
                "total" in subhead or "directo" in subhead or "reaseguro" in subhead
            ):
                headers = next_row.astype(str).tolist()
                data_start = header_row + 2

        # Palabras que indican fila de cabecera, no entidad
        skip_patterns = (
            "nombre empresa", "primas netas", "al 31/12", "miles de bol", "hospitalizaci",
            "automóvil", "resto de ramos", "cuadro n", "republica", "ministerio",
            "superintendencia", "direccion", "actuarial",
        )
        for row_idx in range(data_start, len(df)):
            row = df.iloc[row_idx]
            entity_name = row.iloc[col_ent]
            if pd.isna(entity_name) or not str(entity_name).strip():
                continue
            entity_str = str(entity_name).strip()
            if any(p in entity_str.lower() for p in skip_patterns):
                continue
            if "total" in entity_str.lower() and row_idx > data_start + 2:
                break
            norm = normalize_entity_name(entity_str)
            if not norm or norm == "_empty" or len(norm) < 4:
                continue

            rows_entidades.append({
                "anio": anio,
                "source_file": source_file,
                "entity_name": entity_str,
                "entity_normalized_name": norm,
            })

            for col_idx in range(col_ent + 1, len(row)):
                if col_idx >= len(headers):
                    break
                val = row.iloc[col_idx]
                if pd.isna(val):
                    continue
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    continue
                if pd.isna(v):
                    continue
                col_label = headers[col_idx] if col_idx < len(headers) else ""
                metric_name, ramo = _column_to_metric_name(col_label, sheet)
                if metric_name == "porcentaje" and col_idx % 2 == 1:
                    metric_name = "porcentaje_ramo"
                rows_metricas.append({
                    "anio": anio,
                    "source_file": source_file,
                    "cuadro_or_seccion": sheet,
                    "entity_name": entity_str,
                    "metric_name": metric_name,
                    "value": round(float(v), 4),
                    "unit": "miles_Bs" if "prima" in metric_name or "siniestro" in metric_name else ("%" if "porcentaje" in metric_name else "miles_Bs"),
                    "ramo_opcional": ramo or "",
                })

    # Deduplicar entidades por (anio, entity_normalized_name)
    seen = set()
    unique_ent = []
    for r in rows_entidades:
        k = (r["anio"], r["entity_normalized_name"])
        if k not in seen:
            seen.add(k)
            unique_ent.append(r)
    return unique_ent, rows_metricas


def run_vaciado_inicial(raw_excel_path: Path | None = None) -> dict[str, Any]:
    """
    Construye índice de fuentes y vacía las fuentes que podamos (por ahora Excel 2024).
    Escribe indice/anuario_fuentes.csv, vaciado/anuario_entidades.csv, vaciado/anuario_metricas.csv.
    """
    ensure_anuarios_dirs()
    build_indice_fuentes()

    if raw_excel_path is None:
        raw_excel_path = DATA_RAW / "xlsx" / "cuadros descargables_Seguro en cifras 2024.xlsx"
    if not raw_excel_path.exists():
        return {"indice": str(INDICE_FUENTES_CSV), "entidades": 0, "metricas": 0, "message": "Excel 2024 no encontrado"}

    rows_ent, rows_met = vaciar_excel_anuario_2024(raw_excel_path)

    all_entidades = []
    all_metricas = []
    anio_vaciado = 2024  # año que estamos vaciando ahora

    # Cargar entidades/metricas existentes y quitar las del año que vamos a reemplazar
    if VACIADO_ENTIDADES_CSV.exists():
        try:
            prev = pd.read_csv(VACIADO_ENTIDADES_CSV)
            all_entidades = [r for r in prev.to_dict("records") if r.get("anio") != anio_vaciado]
        except Exception:
            pass
    if METRICAS_CSV.exists():
        try:
            prev = pd.read_csv(METRICAS_CSV)
            all_metricas = [r for r in prev.to_dict("records") if r.get("anio") != anio_vaciado]
        except Exception:
            pass

    all_entidades.extend(rows_ent)
    all_metricas.extend(rows_met)

    pd.DataFrame(all_entidades).drop_duplicates(subset=["anio", "entity_normalized_name"], keep="first").to_csv(
        VACIADO_ENTIDADES_CSV, index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(all_metricas).to_csv(METRICAS_CSV, index=False, encoding="utf-8-sig")

    return {
        "indice": str(INDICE_FUENTES_CSV),
        "entidades_csv": str(VACIADO_ENTIDADES_CSV),
        "metricas_csv": str(METRICAS_CSV),
        "entidades": len(rows_ent),
        "metricas": len(rows_met),
    }
