# scripts/pipeline_anuario_2023.py
"""
Pipeline del anuario 2023 (Seguro en Cifras): extracción -> by_source -> vaciado -> staged.

Flujo:
  1. Lista fuentes de anuario 2023 (PDF y/o XLSX en data/raw).
  2. Si hay PDF y no existe by_source/*_tables.csv, extrae el PDF a audit/by_source.
  3. Ejecuta vaciado para 2023 (prefiere XLSX si existe; si no, usa PDF desde by_source).
  4. Escribe staged/2023/anuario_2023_entidades.csv y anuario_2023_metricas.csv.
  5. Genera reporte reporte_anuario_2023.txt para auditoría.

Ejecutar desde la raíz: python scripts/pipeline_anuario_2023.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE, DATA_STAGED
from config.anuarios_paths import ensure_anuarios_dirs, INDICE_FUENTES_CSV
from src.etl.anuarios_seguro_en_cifras import (
    build_indice_fuentes,
    list_anuario_sources,
    vaciar_anuario_por_anio,
    _nombre_archivo_to_tables_csv,
)
from src.etl.audit_local import extract_tables_from_pdf_local


ANIO = 2023
STAGED_2023 = DATA_STAGED / "2023"
REPORTE_2023 = STAGED_2023 / "reporte_anuario_2023.txt"


def extraer_pdf_a_by_source(pdf_path: Path) -> Path | None:
    """Extrae tablas de un PDF y escribe audit/by_source/{stem}_tables.csv. Devuelve ruta del CSV o None."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        return None
    DATA_AUDIT_BY_SOURCE.mkdir(parents=True, exist_ok=True)
    out_name = re.sub(r"[^\w\-\.]", "_", pdf_path.stem) + "_tables.csv"
    out_path = DATA_AUDIT_BY_SOURCE / out_name
    try:
        tables = extract_tables_from_pdf_local(pdf_path)
        if tables:
            pd.concat(tables, ignore_index=True).to_csv(out_path, index=False, encoding="utf-8-sig")
            return out_path
    except Exception as e:
        print(f"  [AVISO] Error extrayendo PDF {pdf_path.name}: {e}")
    return None


def fuentes_anuario_2023() -> list[dict]:
    """Lista de fuentes (PDF/XLSX) de anuario para el año 2023."""
    ensure_anuarios_dirs()
    if not INDICE_FUENTES_CSV.exists():
        build_indice_fuentes()
    sources = list_anuario_sources()
    return [s for s in sources if s.get("anio") == ANIO]


def run_pipeline() -> dict:
    """Ejecuta el pipeline completo para anuario 2023. Devuelve resumen."""
    STAGED_2023.mkdir(parents=True, exist_ok=True)
    report_lines = [
        f"Reporte pipeline anuario {ANIO}",
        f"Generado: {datetime.now().isoformat()}",
        "",
    ]

    # 1) Fuentes
    fuentes = fuentes_anuario_2023()
    if not fuentes:
        report_lines.append("No se encontraron fuentes de anuario 2023 en data/raw.")
        REPORTE_2023.parent.mkdir(parents=True, exist_ok=True)
        REPORTE_2023.write_text("\n".join(report_lines), encoding="utf-8")
        return {"entidades": 0, "metricas": 0, "fuentes": 0, "error": "sin fuentes"}

    report_lines.append(f"Fuentes encontradas: {len(fuentes)}")
    for f in fuentes:
        report_lines.append(f"  - {f['nombre_archivo']} ({f['tipo']}) -> {f['ruta_relativa']}")
    report_lines.append("")

    # 2) Asegurar by_source para PDF
    for f in fuentes:
        if f["tipo"] == "pdf":
            csv_name = _nombre_archivo_to_tables_csv(f["nombre_archivo"])
            csv_path = DATA_AUDIT_BY_SOURCE / csv_name
            if not csv_path.exists():
                raw_path = DATA_RAW / f["ruta_relativa"].replace("/", "\\")
                if raw_path.exists():
                    print(f"  Extrayendo PDF a by_source: {f['nombre_archivo']}")
                    out = extraer_pdf_a_by_source(raw_path)
                    if out:
                        report_lines.append(f"  PDF extraido -> {out.name}")
                    else:
                        report_lines.append(f"  [AVISO] No se pudieron extraer tablas de {f['nombre_archivo']}")
            else:
                report_lines.append(f"  by_source ya tiene {csv_name}")
    report_lines.append("")

    # 3) Preferir XLSX sobre PDF para vaciado
    fuentes_orden = sorted(fuentes, key=lambda x: (0 if x["tipo"] == "xlsx" else 1, x["nombre_archivo"]))
    entidades_total = []
    metricas_total = []
    fuente_usada = None

    for f in fuentes_orden:
        ent, met, info = vaciar_anuario_por_anio(
            ANIO,
            f["nombre_archivo"],
            f["tipo"],
            f["ruta_relativa"],
        )
        if ent or met:
            entidades_total = ent
            metricas_total = met
            fuente_usada = f["nombre_archivo"]
            report_lines.append(f"Vaciado desde: {fuente_usada} ({info.get('origen', '')})")
            report_lines.append(f"  Entidades: {len(ent)}, Metricas: {len(met)}")
            break

    if not fuente_usada:
        report_lines.append("No se pudo vaciar ninguna fuente (revisar by_source para PDF o ruta Excel).")
        REPORTE_2023.write_text("\n".join(report_lines), encoding="utf-8")
        return {"entidades": 0, "metricas": 0, "fuentes": len(fuentes), "error": "vaciado vacio"}

    # 4) Escribir staged
    entidades_path = STAGED_2023 / "anuario_2023_entidades.csv"
    metricas_path = STAGED_2023 / "anuario_2023_metricas.csv"
    pd.DataFrame(entidades_total).to_csv(entidades_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(metricas_total).to_csv(metricas_path, index=False, encoding="utf-8-sig")
    report_lines.append("")
    report_lines.append(f"Staged escrito: {entidades_path.name}, {metricas_path.name}")

    # Resumen para auditoría
    report_lines.append("")
    report_lines.append("--- Resumen para auditoria ---")
    report_lines.append(f"  Entidades unicas: {len(entidades_total)}")
    report_lines.append(f"  Filas de metricas: {len(metricas_total)}")
    if metricas_total:
        df_met = pd.DataFrame(metricas_total)
        if "metric_name" in df_met.columns:
            report_lines.append(f"  Metricas distintas: {df_met['metric_name'].nunique()}")
        if "entity_name" in df_met.columns:
            report_lines.append(f"  Entidades en metricas: {df_met['entity_name'].nunique()}")

    REPORTE_2023.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nReporte: {REPORTE_2023}")
    return {
        "entidades": len(entidades_total),
        "metricas": len(metricas_total),
        "fuentes": len(fuentes),
        "fuente_usada": fuente_usada,
    }


def main():
    print("=== Pipeline Anuario 2023 (Seguro en Cifras) ===\n")
    res = run_pipeline()
    print(f"  Entidades: {res.get('entidades', 0)}")
    print(f"  Metricas:  {res.get('metricas', 0)}")
    print(f"  Fuente usada: {res.get('fuente_usada', '—')}")
    if res.get("error"):
        print(f"  Error: {res['error']}")
    print("\n  Revisar staged/2023/ y reporte_anuario_2023.txt antes de pasar a clean/replica.")


if __name__ == "__main__":
    main()
