"""
Paso 1 — Diagnóstico de la estructura base de vaciado.
Verifica que cada entidad (compañía de seguros) tenga 12 meses de datos por cada
campo (primas_netas_ves, siniestros_pagados_ves, gastos_operativos_ves).
Si no es así, indica qué meses faltan (compañía nueva o dejó de reportar).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_STAGED, DATA_AUDIT_BY_SOURCE
from src.etl.staged_resumen import (
    CAMPOS_EXCEL,
    COLUMNAS_BASE,
    ESPERADO_COMPANIAS_POR_MES,
    build_staged_resumen_2023,
    load_resumen_extract_csv,
    resumen_companias_por_mes,
)

STAGED_2023 = DATA_STAGED / "2023"
BASE_CSV = STAGED_2023 / "resumen_por_empresa_2023_base.csv"
REPORTE_ENTIDAD = STAGED_2023 / "diagnostico_entidad_12_meses.csv"
REPORTE_MESES_FALTANTES = STAGED_2023 / "diagnostico_meses_faltantes_por_entidad.csv"
MESES_ESPERADOS = list(range(1, 13))  # 1..12


def load_base_table(rebuild: bool = False) -> pd.DataFrame:
    """Carga la tabla base (staged). Si no existe o rebuild=True, la construye desde el extract."""
    if not rebuild and BASE_CSV.exists():
        return pd.read_csv(BASE_CSV, encoding="utf-8-sig")
    STAGED_2023.mkdir(parents=True, exist_ok=True)
    return build_staged_resumen_2023()


def diagnosticar_12_meses(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Para cada entidad y cada campo base, cuenta cuántos meses tienen dato (max 12).
    Devuelve:
    - reporte_entidad: una fila por entidad con columnas n_meses, primas_ok, siniestros_ok, gastos_ok, meses_faltantes, estado.
    - reporte_meses_faltantes: detalle entidad x mes para cada campo (1=tiene dato, 0=falta).
    """
    if df.empty or "entity_normalized" not in df.columns or "periodo" not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    df = df.copy()
    df["mes"] = pd.to_numeric(df["periodo"].str.slice(5, 7), errors="coerce")
    entidades = df["entity_normalized"].dropna().unique().tolist()

    # Por entidad: cuántos meses distintos hay y cuántos meses con valor no nulo por campo
    filas_entidad = []
    filas_detalle = []  # entidad, mes, primas_ok, siniestros_ok, gastos_ok

    for ent in entidades:
        sub = df[df["entity_normalized"] == ent]
        meses_presentes = sub["mes"].dropna().astype(int).unique().tolist()
        n_meses = len(meses_presentes)
        meses_faltantes = [m for m in MESES_ESPERADOS if m not in meses_presentes]

        counts = {}
        for col in COLUMNAS_BASE:
            if col not in sub.columns:
                counts[col] = 0
            else:
                counts[col] = sub[col].notna().sum()

        # Estado: completo (12 meses y los 3 campos con 12), incompleto, o "nueva" si tiene pocos meses
        if n_meses == 12 and all(counts.get(c, 0) == 12 for c in COLUMNAS_BASE):
            estado = "completo"
        elif n_meses < 12 and n_meses > 0:
            estado = "incompleto (menos de 12 meses)"
        else:
            estado = "incompleto"

        filas_entidad.append({
            "entity_normalized": ent,
            "entity_canonical": sub["entity_canonical"].iloc[0] if "entity_canonical" in sub.columns else ent,
            "n_meses_con_registro": n_meses,
            "primas_meses_ok": counts.get("primas_netas_ves", 0),
            "siniestros_meses_ok": counts.get("siniestros_pagados_ves", 0),
            "gastos_meses_ok": counts.get("gastos_operativos_ves", 0),
            "meses_faltantes": ",".join(str(m) for m in sorted(meses_faltantes)) if meses_faltantes else "",
            "estado": estado,
        })

        # Detalle mes a mes para esta entidad
        for mes in MESES_ESPERADOS:
            row_mes = sub[sub["mes"] == mes]
            p_ok = 1 if row_mes["primas_netas_ves"].notna().any() else 0
            s_ok = 1 if row_mes["siniestros_pagados_ves"].notna().any() else 0
            g_ok = 1 if row_mes["gastos_operativos_ves"].notna().any() else 0
            filas_detalle.append({
                "entity_normalized": ent,
                "mes": mes,
                "primas_ok": p_ok,
                "siniestros_ok": s_ok,
                "gastos_ok": g_ok,
            })

    reporte_entidad = pd.DataFrame(filas_entidad)
    reporte_detalle = pd.DataFrame(filas_detalle)
    return reporte_entidad, reporte_detalle


def main():
    print("=" * 70)
    print("Diagnóstico paso 1 — Estructura base de vaciado (12 meses por entidad)")
    print("=" * 70)

    # 1) Cargar o construir tabla base (con los 8 campos del Excel)
    print("\n1) Cargando tabla base (entidad, periodo, 8 campos financieros)...")
    try:
        df = load_base_table(rebuild=True)  # Rebuild para tener los 8 campos
    except FileNotFoundError as e:
        print(f"   Error: {e}")
        return
    campos_presentes = [c for c in CAMPOS_EXCEL + ["gastos_operativos_ves"] if c in df.columns]
    print(f"   Filas: {len(df)} | Entidades: {df['entity_normalized'].nunique()} | Periodos: {df['periodo'].nunique()}")
    print(f"   Campos (8 del Excel + gastos_operativos): {len(campos_presentes)} -> {campos_presentes}")

    # 1b) Validación de dimensión: compañías por mes (esperado 51, p. ej. diciembre)
    resumen_mes = resumen_companias_por_mes(df)
    print("\n   Companias por mes (esperado {} por hoja):".format(ESPERADO_COMPANIAS_POR_MES))
    for _, r in resumen_mes.iterrows():
        mes = int(r["mes"])
        n = int(r["n_companias"])
        flag = " [OK]" if n == ESPERADO_COMPANIAS_POR_MES else " (esperado {})".format(ESPERADO_COMPANIAS_POR_MES)
        print("     Mes {:2d}: {:2d} companias{}".format(mes, n, flag))
    dif = resumen_mes["n_companias"] != ESPERADO_COMPANIAS_POR_MES
    if dif.any():
        print("   Nota: Si hay diferencia, puede deberse a filas TOTAL no excluidas o a mas de 51 entidades en el extract.")

    # 2) Diagnóstico
    print("\n2) Verificando 12 meses por entidad, campo a campo...")
    reporte_entidad, reporte_detalle = diagnosticar_12_meses(df)
    if reporte_entidad.empty:
        print("   No se pudo generar el diagnóstico.")
        return

    # 3) Guardar reportes
    STAGED_2023.mkdir(parents=True, exist_ok=True)
    reporte_entidad.to_csv(REPORTE_ENTIDAD, index=False, encoding="utf-8-sig")
    reporte_detalle.to_csv(REPORTE_MESES_FALTANTES, index=False, encoding="utf-8-sig")
    print(f"   Reporte por entidad guardado: {REPORTE_ENTIDAD}")
    print(f"   Detalle mes a mes guardado:   {REPORTE_MESES_FALTANTES}")

    # 4) Resumen en consola
    n_completo = (reporte_entidad["estado"] == "completo").sum()
    n_incompleto = len(reporte_entidad) - n_completo
    n_12_meses_registro = (reporte_entidad["n_meses_con_registro"] == 12).sum()
    n_12_primas = (reporte_entidad["primas_meses_ok"] == 12).sum()
    n_12_siniestros = (reporte_entidad["siniestros_meses_ok"] == 12).sum()
    n_12_gastos = (reporte_entidad["gastos_meses_ok"] == 12).sum()
    print("\n3) Resumen")
    print("   " + "-" * 50)
    print(f"   Total entidades:                                     {len(reporte_entidad)}")
    print(f"   Entidades con 12 meses de registro:                  {n_12_meses_registro}")
    print(f"   Entidades con 12 meses en primas_netas_ves:          {n_12_primas}")
    print(f"   Entidades con 12 meses en siniestros_pagados_ves:    {n_12_siniestros}")
    print(f"   Entidades con 12 meses en gastos_operativos_ves:     {n_12_gastos}")
    print(f"   Entidades con 12/12 en los 3 campos (completo):      {n_completo}")
    print(f"   Entidades con datos incompletos:                     {n_incompleto}")

    if n_incompleto > 0:
        print("\n4) Entidades con datos incompletos (primeras 20)")
        print("   " + "-" * 50)
        inc = reporte_entidad[reporte_entidad["estado"] != "completo"].head(20)
        for _, r in inc.iterrows():
            print(f"   {r['entity_canonical'][:50]:50} | meses: {r['n_meses_con_registro']:2} | "
                  f"primas: {r['primas_meses_ok']:2} siniestros: {r['siniestros_meses_ok']:2} gastos: {r['gastos_meses_ok']:2} | "
                  f"faltan: {r['meses_faltantes'] or '-'}")

    print("\n5) Conclusión")
    print("   Si todas las entidades tienen 12/12 meses en los tres campos, la estructura base es consistente.")
    print("   Si hay entidades con menos de 12 meses, puede deberse a compañía nueva o que dejó de reportar.")
    print()


if __name__ == "__main__":
    main()
