"""
Ejecuta la compilación (tabla base desde resumen-por-empresa) y verifica:
- 50 o 51 compañías por mes.
- Los 8 campos registro a registro: numéricos, consistentes (5)=(2)+(3), sin anomalías.
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
    ESPERADO_COMPANIAS_POR_MES,
    build_staged_resumen_2023,
    resumen_companias_por_mes,
)

STAGED_2023 = DATA_STAGED / "2023"
BASE_CSV = STAGED_2023 / "resumen_por_empresa_2023_base.csv"
REPORTE_CONSISTENCIA = STAGED_2023 / "verificacion_8_campos_consistencia.csv"
REPORTE_RESUMEN = STAGED_2023 / "verificacion_8_campos_resumen.txt"

# Tolerancia para (5) = (2)+(3): absoluta (Bs.) y relativa (ej. 1%) por redondeo en origen
TOLERANCIA_ABS = 2000.0   # Bs.
TOLERANCIA_REL = 0.02     # 2%


def ejecutar_compilacion() -> pd.DataFrame:
    """Compila la tabla base desde el extract y la guarda en staged/2023."""
    STAGED_2023.mkdir(parents=True, exist_ok=True)
    return build_staged_resumen_2023()


def verificar_companias_por_mes(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Verifica que cada mes tenga 50 o 51 compañías. Devuelve resumen y mensajes."""
    resumen = resumen_companias_por_mes(df)
    mensajes = []
    for _, r in resumen.iterrows():
        mes = int(r["mes"])
        n = int(r["n_companias"])
        if n not in (50, 51):
            mensajes.append("Mes {}: {} companias (esperado 50 o 51)".format(mes, n))
        elif n != ESPERADO_COMPANIAS_POR_MES:
            mensajes.append("Mes {}: {} companias [OK, distinto de 51]".format(mes, n))
    return resumen, mensajes


def verificar_registro_a_registro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Por cada fila verifica:
    - Los 8 campos son numéricos (o NaN).
    - (5) Siniestros Totales ≈ (2) + (3) dentro de tolerancia.
    - Valores negativos (se reportan; pueden ser válidos).
    Añade columnas: _todos_numericos, _s5_igual_2_mas_3, _tiene_negativos, _inconsistencias.
    """
    if df.empty:
        return df.copy()
    out = df.copy()
    campos = [c for c in CAMPOS_EXCEL if c in out.columns]
    # Todos numéricos por fila
    def _fila_numerica(row):
        for c in campos:
            v = row.get(c)
            if pd.isna(v):
                continue
            try:
                float(v)
            except (TypeError, ValueError):
                return False
        return True
    out["_todos_numericos"] = out.apply(_fila_numerica, axis=1)
    # (5) ≈ (2)+(3)
    c2 = "siniestros_pagados_ves"
    c3 = "reservas_brutas_ves"
    c5 = "siniestros_totales_ves"
    def _s5_ok(row):
        if c5 not in row or c2 not in row or c3 not in row:
            return pd.NA
        s2 = row.get(c2)
        s3 = row.get(c3)
        s5 = row.get(c5)
        if pd.isna(s2) and pd.isna(s3) and pd.isna(s5):
            return True
        try:
            v2 = 0.0 if pd.isna(s2) else float(s2)
            v3 = 0.0 if pd.isna(s3) else float(s3)
            v5 = float(s5) if not pd.isna(s5) else None
            if v5 is None:
                return pd.NA
            suma = v2 + v3
            diff = abs(v5 - suma)
            if diff <= TOLERANCIA_ABS:
                return True
            ref = max(abs(v5), abs(suma), 1.0)
            return (diff / ref) <= TOLERANCIA_REL
        except (TypeError, ValueError):
            return False
    out["_s5_igual_2_mas_3"] = out.apply(_s5_ok, axis=1)
    # Negativos
    def _tiene_negativos(row):
        for c in campos:
            v = row.get(c)
            if pd.isna(v):
                continue
            try:
                if float(v) < 0:
                    return True
            except (TypeError, ValueError):
                pass
        return False
    out["_tiene_negativos"] = out.apply(_tiene_negativos, axis=1)
    # Resumen de inconsistencias
    def _inconsistencias(row):
        parts = []
        if not row.get("_todos_numericos", True):
            parts.append("no_numerico")
        s5 = row.get("_s5_igual_2_mas_3")
        if s5 is False:
            parts.append("s5_ne_2+3")
        if row.get("_tiene_negativos", False):
            parts.append("negativo")
        return ";".join(parts) if parts else ""
    out["_inconsistencias"] = out.apply(_inconsistencias, axis=1)
    return out


def main():
    print("=" * 70)
    print("Compilacion y verificacion: 50/51 companias por mes, 8 campos registro a registro")
    print("=" * 70)

    # 1) Compilacion
    print("\n1) Ejecutando compilacion (resumen-por-empresa-2023 -> staged/2023)...")
    try:
        df = ejecutar_compilacion()
    except FileNotFoundError as e:
        print("   Error:", e)
        return
    print("   Filas: {} | Entidades: {} | Periodos: {}".format(
        len(df), df["entity_normalized"].nunique(), df["periodo"].nunique()))
    print("   Guardado: {}".format(BASE_CSV))

    # 2) Verificacion: companias por mes (50 o 51)
    print("\n2) Verificacion: companias por mes (esperado 50 o 51)")
    resumen_mes, msg_mes = verificar_companias_por_mes(df)
    for _, r in resumen_mes.iterrows():
        mes = int(r["mes"])
        n = int(r["n_companias"])
        ok = " [OK]" if n in (50, 51) else " ***"
        print("   Mes {:2d}: {:2d} companias{}".format(mes, n, ok))
    if msg_mes:
        for m in msg_mes:
            print("   Nota:", m)

    # 3) Verificacion registro a registro (8 campos)
    print("\n3) Verificacion registro a registro (8 campos)")
    df_check = verificar_registro_a_registro(df)
    n_ok_num = df_check["_todos_numericos"].sum()
    n_total = len(df_check)
    n_s5_ok = df_check["_s5_igual_2_mas_3"].dropna()
    n_s5_ok = (n_s5_ok == True).sum()
    n_s5_na = df_check["_s5_igual_2_mas_3"].isna().sum()
    n_s5_fail = n_total - n_s5_ok - n_s5_na
    n_neg = df_check["_tiene_negativos"].sum()
    inconsistentes = df_check[df_check["_inconsistencias"] != ""]

    print("   Filas totales: {}".format(n_total))
    print("   Filas con 8 campos numericos (o NaN): {} / {} [{}]".format(
        int(n_ok_num), n_total, "OK" if n_ok_num == n_total else "REVISAR"))
    print("   (5)=(2)+(3) dentro de tolerancia: {} | NA: {} | No cumple: {}".format(
        int(n_s5_ok), int(n_s5_na), int(n_s5_fail)))
    print("   Filas con algun valor negativo: {} (pueden ser validos)".format(int(n_neg)))
    print("   Filas con alguna inconsistencia: {}".format(len(inconsistentes)))

    # 4) Guardar reportes
    STAGED_2023.mkdir(parents=True, exist_ok=True)
    # CSV con columnas de verificacion (para inspeccion)
    cols_export = ["entity_normalized", "entity_canonical", "periodo", "mes"] + [
        c for c in CAMPOS_EXCEL if c in df_check.columns
    ] + ["gastos_operativos_ves"] + ["_todos_numericos", "_s5_igual_2_mas_3", "_tiene_negativos", "_inconsistencias"]
    cols_export = [c for c in cols_export if c in df_check.columns]
    df_check[cols_export].to_csv(REPORTE_CONSISTENCIA, index=False, encoding="utf-8-sig")
    print("\n4) Reporte detalle guardado: {}".format(REPORTE_CONSISTENCIA))

    # Resumen en texto
    with open(REPORTE_RESUMEN, "w", encoding="utf-8") as f:
        f.write("Verificacion compilado 2023 - 8 campos\n")
        f.write("Filas: {} | Entidades: {} | Meses: 12\n".format(
            len(df), df["entity_normalized"].nunique()))
        f.write("Companias por mes: 50 o 51 esperado\n")
        f.write("Registro a registro: todos numericos {} / {} | (5)=(2)+(3) ok: {} | con negativos: {}\n".format(
            int(n_ok_num), n_total, int(n_s5_ok), int(n_neg)))
        f.write("Filas inconsistentes: {}\n".format(len(inconsistentes)))
        if len(inconsistentes) > 0:
            f.write("\nPrimeras 20 filas con _inconsistencias:\n")
            inconsistentes[cols_export].head(20).to_string(f, index=False)
    print("   Resumen: {}".format(REPORTE_RESUMEN))

    # 5) Muestra de filas inconsistentes
    if len(inconsistentes) > 0:
        print("\n5) Muestra de filas con inconsistencias (max 10)")
        for _, row in inconsistentes.head(10).iterrows():
            print("   {} | {} | {}".format(
                row.get("entity_canonical", "")[:40],
                row.get("periodo", ""),
                row.get("_inconsistencias", "")))
        meses_inc = inconsistentes["mes"].value_counts()
        if len(meses_inc) == 1:
            print("   Nota: Todas las inconsistencias son del mes {} (revisar hoja en Excel si aplica).".format(meses_inc.index[0]))
    else:
        print("\n5) Todas las filas pasaron la verificacion de consistencia.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
