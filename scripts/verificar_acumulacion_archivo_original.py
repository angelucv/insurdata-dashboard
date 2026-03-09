"""
Verifica en el ARCHIVO ORIGINAL (extract by_source) que los campos acumulados
(primas, siniestros pagados, comisiones, gastos) no disminuyan al avanzar el año.
La información en cada pestaña es ACUMULADA; las bajas pueden deberse a empresas
que no envían en un mes o a ajustes a la baja. Solo las reservas (3),(4),(5) se
constituyen y liberan mes a mes, por tanto no se verifican aquí.
Valores en miles de Bs. como en el Excel.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_AUDIT_BY_SOURCE, DATA_STAGED
from src.etl.transformers import normalize_entity_name

MES_SHEET_TO_NUM = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

# Campos que deben incrementar mes a mes (nombres para reporte; columnas por número en Excel)
CAMPOS_ACUMULABLES = [
    ("primas_netas", 1),
    ("siniestros_pagados", 2),
    ("comisiones", 6),
    ("gastos_adquisicion", 7),
    ("gastos_administracion", 8),
]
# Gastos totales = (6)+(7)+(8) se verifica aparte

EXTRACT_PATH = Path(DATA_AUDIT_BY_SOURCE) / "resumen-por-empresa-2023_extract.csv"
STAGED_2023 = Path(DATA_STAGED) / "2023"
REPORTE_BAJAS = STAGED_2023 / "verificacion_original_acumulacion_bajas.csv"
REPORTE_RESUMEN = STAGED_2023 / "verificacion_original_acumulacion_resumen.txt"
TOLERANCIA = 0.001  # en miles: tolerancia por redondeo


def _find_column(df: pd.DataFrame, *keywords: str) -> str | None:
    for c in df.columns:
        if any(kw in str(c).lower() for kw in keywords):
            return c
    return None


def _find_column_by_num(df: pd.DataFrame, num: int) -> str | None:
    needle = f"({num})"
    for c in df.columns:
        if needle in str(c):
            return c
    return None


def load_extract_original(path: Path) -> pd.DataFrame:
    """
    Carga el extract tal cual (valores en miles de Bs., sin multiplicar por 1000).
    Una fila por (entidad, mes) con columnas: empresa, mes, y los campos (1),(2),(6),(7),(8).
    """
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if "_sheet" not in df.columns:
        raise ValueError("Falta columna _sheet en el extract.")
    col_empresa = _find_column(df, "empresa", "seguros")
    if not col_empresa:
        col_empresa = df.columns[2] if len(df.columns) > 2 else None
    cols_num = {}
    for i in (1, 2, 6, 7, 8):
        c = _find_column_by_num(df, i)
        if c:
            cols_num[i] = c
    if 1 not in cols_num:
        cols_num[1] = _find_column(df, "primas", "netas", "cobradas")
    if not col_empresa or 1 not in cols_num:
        raise ValueError("No se encontraron columnas empresa o (1) Primas.")

    col_num = _find_column(df, "#") or (df.columns[0] if len(df.columns) else None)

    rows = []
    for _, row in df.iterrows():
        if col_num and col_num in row.index:
            try:
                n = int(float(row.get(col_num)))
                if n < 1 or n > 100:
                    continue
            except (TypeError, ValueError):
                continue
        emp = row.get(col_empresa)
        if pd.isna(emp) or not str(emp).strip():
            continue
        emp_str = str(emp).strip()
        if "total" in emp_str.lower():
            continue
        sheet = row.get("_sheet")
        if pd.isna(sheet):
            continue
        mes = MES_SHEET_TO_NUM.get(str(sheet).strip().lower())
        if not mes:
            continue
        out = {"empresa": emp_str, "mes": mes}
        for nom, num in CAMPOS_ACUMULABLES:
            c = cols_num.get(num)
            if not c or c not in row.index:
                out[nom] = None
                continue
            try:
                v = float(row.get(c) or 0)
            except (TypeError, ValueError):
                out[nom] = None
                continue
            out[nom] = round(v, 4)
        # Gastos totales = comisiones + gastos_adquisicion + gastos_administracion
        c6 = out.get("comisiones")
        c7 = out.get("gastos_adquisicion")
        c8 = out.get("gastos_administracion")
        if c6 is not None or c7 is not None or c8 is not None:
            out["gastos_totales"] = round((c6 or 0) + (c7 or 0) + (c8 or 0), 4)
        else:
            out["gastos_totales"] = None
        out["empresa_norm"] = normalize_entity_name(emp_str) or emp_str
        rows.append(out)
    return pd.DataFrame(rows)


def main():
    print("=" * 70)
    print("Verificacion en ARCHIVO ORIGINAL: primas, siniestros pagados, comisiones, gastos")
    print("Deben incrementarse mes a mes (valores en miles de Bs. como en el Excel)")
    print("=" * 70)

    if not EXTRACT_PATH.exists():
        print("No existe:", EXTRACT_PATH)
        return

    df = load_extract_original(EXTRACT_PATH)
    # Agrupar por empresa normalizada (misma compania con distinta puntuacion en Excel = 1 entidad)
    if "empresa_norm" not in df.columns:
        df["empresa_norm"] = df["empresa"].apply(lambda x: normalize_entity_name(str(x)) if pd.notna(x) else "")
    df = df[df["empresa_norm"].str.len() > 0].copy()
    campos_verificar = [c[0] for c in CAMPOS_ACUMULABLES] + ["gastos_totales"]
    print("\n1) Extract cargado. Campos a verificar: {}".format(campos_verificar))
    print("   Filas: {} | Entidades (normalizadas): {} | Meses: {}".format(
        len(df), df["empresa_norm"].nunique(), sorted(df["mes"].unique())))

    # Ordenar por empresa normalizada y mes
    df = df.sort_values(["empresa_norm", "mes"])
    filas_baja = []
    resumen_por_campo = {c: set() for c in campos_verificar}

    for empresa_norm in df["empresa_norm"].dropna().unique():
        sub = df[df["empresa_norm"] == empresa_norm].sort_values("mes")
        for col in campos_verificar:
            if col not in sub.columns:
                continue
            prev_mes = None
            prev_val = None
            for _, row in sub.iterrows():
                mes = int(row["mes"])
                val = row.get(col)
                if pd.isna(val):
                    prev_mes, prev_val = mes, None
                    continue
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    prev_mes, prev_val = mes, None
                    continue
                if prev_val is not None and prev_mes is not None and mes > prev_mes:
                    if v < prev_val - TOLERANCIA:
                        resumen_por_campo[col].add(empresa_norm)
                        emp_canon = sub["empresa"].iloc[0] if "empresa" in sub.columns else empresa_norm
                        filas_baja.append({
                            "empresa": emp_canon,
                            "empresa_norm": empresa_norm,
                            "campo": col,
                            "mes_anterior": prev_mes,
                            "mes_actual": mes,
                            "valor_anterior_miles": round(prev_val, 4),
                            "valor_actual_miles": round(v, 4),
                            "diferencia_miles": round(v - prev_val, 4),
                        })
                prev_mes, prev_val = mes, v

    # Resumen
    print("\n2) Resultado: campos que DEBERIAN incrementar mes a mes")
    print("   " + "-" * 55)
    for col in campos_verificar:
        n_entes = len(resumen_por_campo[col])
        total_entes = df["empresa_norm"].nunique()
        estado = "OK (nunca bajan)" if n_entes == 0 else "HAY BAJAS"
        print("   {:25s} {:3d} entidades con al menos 1 baja / {}  [{}]".format(
            col, n_entes, total_entes, estado))

    n_bajas = len(filas_baja)
    print("\n3) Total violaciones (valor mes N < valor mes N-1): {}".format(n_bajas))
    if n_bajas == 0:
        print("   En el archivo original, primas/siniestros/comisiones/gastos SI incrementan mes a mes.")
    else:
        print("   Las bajas detectadas pueden deberse a empresas que no enviaron en un mes o a ajustes a la baja (la info es acumulada).")

    # Guardar detalle (valores en miles para cotejar con Excel)
    STAGED_2023.mkdir(parents=True, exist_ok=True)
    if filas_baja:
        pd.DataFrame(filas_baja).to_csv(REPORTE_BAJAS, index=False, encoding="utf-8-sig")
        print("\n4) Detalle guardado (valores en miles de Bs.): {}".format(REPORTE_BAJAS))
        print("   Muestra (10 primeras):")
        for r in filas_baja[:10]:
            print("   {} | {} | mes {}-{} | {} -> {} (diff: {} miles)".format(
                r["empresa"][:35].ljust(35),
                r["campo"],
                r["mes_anterior"], r["mes_actual"],
                r["valor_anterior_miles"], r["valor_actual_miles"],
                r["diferencia_miles"]))
    else:
        print("\n4) No hay bajas; no se genera archivo de detalle.")

    with open(REPORTE_RESUMEN, "w", encoding="utf-8") as f:
        f.write("Verificacion acumulacion ARCHIVO ORIGINAL (extract 2023)\n")
        f.write("Campos: primas, siniestros_pagados, comisiones, gastos (adquisicion, administracion, totales)\n")
        f.write("Valores en miles de Bs. como en el Excel.\n")
        for col in campos_verificar:
            f.write("  {}: {} entidades con al menos 1 baja\n".format(col, len(resumen_por_campo[col])))
        f.write("Total violaciones: {}\n".format(n_bajas))
    print("\n5) Resumen: {}".format(REPORTE_RESUMEN))
    print("=" * 70)


if __name__ == "__main__":
    main()
