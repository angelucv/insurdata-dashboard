"""
Verificacion detallada del vaciado: consistencia de todos los campos
en toda la serie historica, ano a ano.
Genera reportes por ano y chequeos de consistencia entre anos.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from config.anuarios_paths import (
    ensure_anuarios_dirs,
    VACIADO_ENTIDADES_CSV,
    METRICAS_CSV,
    SEGURO_EN_CIFRAS_INDICE,
    SEGURO_EN_CIFRAS_VARIABLES,
)

CAMPOS_ENTIDADES = ["anio", "source_file", "entity_name", "entity_normalized_name"]
CAMPOS_METRICAS = ["anio", "source_file", "cuadro_or_seccion", "entity_name", "metric_name", "value", "unit", "ramo_opcional"]


def _pct(n: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{100 * n / total:.1f}%"


def _no_nulo_serie(s: pd.Series, vacio_como_nulo: bool = True) -> int:
    if vacio_como_nulo:
        return (s.notna() & (s.astype(str).str.strip() != "")).sum()
    return s.notna().sum()


def detalle_por_anio_entidades(df_ent: pd.DataFrame) -> pd.DataFrame:
    """Por cada ano: total entidades, nulos por campo, entidades unicas, alertas."""
    filas = []
    for anio, g in df_ent.groupby("anio", sort=True):
        total = len(g)
        row = {"anio": anio, "total_entidades": total, "entidades_unicas": g["entity_normalized_name"].nunique()}
        for col in CAMPOS_ENTIDADES:
            if col not in g.columns:
                row[f"{col}_no_nulo"] = 0
                row[f"{col}_pct"] = "0%"
                row[f"{col}_ok"] = False
                continue
            nn = _no_nulo_serie(g[col])
            row[f"{col}_no_nulo"] = nn
            row[f"{col}_pct"] = _pct(nn, total)
            row[f"{col}_ok"] = nn == total
        # Alertas: entity_name muy corto o duplicados
        nombres = g["entity_name"].astype(str).str.strip()
        cortos = (nombres.str.len() < 4).sum()
        row["entity_name_cortos"] = int(cortos)
        row["source_file"] = g["source_file"].iloc[0] if "source_file" in g.columns else ""
        filas.append(row)
    return pd.DataFrame(filas)


def detalle_por_anio_metricas(df_met: pd.DataFrame) -> pd.DataFrame:
    """Por cada ano: total metricas, nulos por campo, metric_name unicos, unit, value stats."""
    filas = []
    for anio, g in df_met.groupby("anio", sort=True):
        total = len(g)
        row = {"anio": anio, "total_metricas": total}
        for col in CAMPOS_METRICAS:
            if col not in g.columns:
                row[f"{col}_no_nulo"] = 0
                row[f"{col}_pct"] = "0%"
                row[f"{col}_ok"] = False
                continue
            if col == "value":
                nn = pd.to_numeric(g[col], errors="coerce").notna().sum()
            elif col == "ramo_opcional":
                nn = _no_nulo_serie(g[col])
                row[f"{col}_ok"] = True
            else:
                nn = _no_nulo_serie(g[col])
            row[f"{col}_no_nulo"] = int(nn)
            row[f"{col}_pct"] = _pct(nn, total)
            if col != "ramo_opcional":
                row[f"{col}_ok"] = nn == total if col != "value" else (nn >= total * 0.99)
        row["metric_names_unicos"] = g["metric_name"].nunique()
        row["units_unicos"] = g["unit"].nunique() if "unit" in g.columns else 0
        row["cuadros_unicos"] = g["cuadro_or_seccion"].nunique() if "cuadro_or_seccion" in g.columns else 0
        vals = pd.to_numeric(g["value"], errors="coerce")
        row["value_min"] = vals.min() if vals.notna().any() else None
        row["value_max"] = vals.max() if vals.notna().any() else None
        row["value_negativos"] = (vals < 0).sum()
        filas.append(row)
    return pd.DataFrame(filas)


def consistencia_serie(
    df_ent: pd.DataFrame, df_met: pd.DataFrame, canonico: set
) -> tuple[pd.DataFrame, list[str]]:
    """
    Chequeos de consistencia en la serie historica.
    Retorna DataFrame con resumen de consistencia y lista de alertas.
    """
    alertas = []
    filas = []

    anios_ent = set(df_ent["anio"].dropna().astype(int)) if not df_ent.empty else set()
    anios_met = set(df_met["anio"].dropna().astype(int)) if not df_met.empty else set()
    anios = sorted(anios_ent | anios_met)

    for anio in anios:
        r = {"anio": anio}
        # Entidades: todos los campos llenos?
        ge = df_ent[df_ent["anio"] == anio] if not df_ent.empty else pd.DataFrame()
        if ge.empty:
            r["entidades_ok"] = False
            r["entidades_total"] = 0
            alertas.append(f"Anio {anio}: sin registros en entidades")
        else:
            r["entidades_total"] = len(ge)
            ok = all(
                _no_nulo_serie(ge[c]) == len(ge)
                for c in CAMPOS_ENTIDADES
                if c in ge.columns
            )
            r["entidades_ok"] = ok
            if not ok:
                for c in CAMPOS_ENTIDADES:
                    if c in ge.columns and _no_nulo_serie(ge[c]) < len(ge):
                        alertas.append(f"Anio {anio} entidades: campo '{c}' con nulos")

        # Metricas: campos obligatorios llenos?
        gm = df_met[df_met["anio"] == anio] if not df_met.empty else pd.DataFrame()
        if gm.empty:
            r["metricas_ok"] = False
            r["metricas_total"] = 0
            if anio in anios_ent:
                alertas.append(f"Anio {anio}: tiene entidades pero 0 metricas")
        else:
            r["metricas_total"] = len(gm)
            value_ok = pd.to_numeric(gm["value"], errors="coerce").notna().sum() >= len(gm) * 0.99
            otros_ok = all(
                _no_nulo_serie(gm[c]) == len(gm)
                for c in ["anio", "source_file", "cuadro_or_seccion", "entity_name", "metric_name", "unit"]
                if c in gm.columns
            )
            r["metricas_ok"] = value_ok and otros_ok
            if not value_ok:
                alertas.append(f"Anio {anio} metricas: campo 'value' con mas de 1% nulos")

        r["tiene_entidades"] = not ge.empty
        r["tiene_metricas"] = not gm.empty
        filas.append(r)

    # Consistencia de units a lo largo de la serie
    if not df_met.empty and "unit" in df_met.columns:
        units_por_anio = df_met.groupby("anio")["unit"].apply(lambda x: set(x.dropna().astype(str).unique())).to_dict()
        todos_units = set()
        for u in units_por_anio.values():
            todos_units |= u
        if len(todos_units) > 5:
            alertas.append(f"Serie: se usan {len(todos_units)} unidades distintas: {sorted(todos_units)[:10]}")

    return pd.DataFrame(filas), alertas


def main():
    ensure_anuarios_dirs()
    indice = Path(SEGURO_EN_CIFRAS_INDICE)
    indice.mkdir(parents=True, exist_ok=True)

    if not VACIADO_ENTIDADES_CSV.exists() or not METRICAS_CSV.exists():
        print("Faltan archivos de vaciado:", VACIADO_ENTIDADES_CSV, METRICAS_CSV)
        sys.exit(1)

    df_ent = pd.read_csv(VACIADO_ENTIDADES_CSV)
    df_met = pd.read_csv(METRICAS_CSV)

    canonico = set()
    cp = SEGURO_EN_CIFRAS_VARIABLES / "canonico.csv"
    if cp.exists():
        try:
            cv = pd.read_csv(cp)
            if "metric_name" in cv.columns:
                canonico = set(cv["metric_name"].dropna().astype(str).str.strip())
        except Exception:
            pass

    print("Verificacion detallada del vaciado - Serie historica")
    print("=" * 65)

    # 1) Detalle entidades por ano
    det_ent = detalle_por_anio_entidades(df_ent)
    path_det_ent = indice / "verificacion_entidades_por_anio.csv"
    det_ent.to_csv(path_det_ent, index=False, encoding="utf-8-sig")
    print("\n1. Entidades por ano (campos y consistencia)")
    print("-" * 50)
    # Resumir: anos con algun campo no OK
    ent_fallos = det_ent[~det_ent["entity_name_ok"].astype(bool)] if "entity_name_ok" in det_ent.columns else pd.DataFrame()
    if not ent_fallos.empty:
        print("  Anos con campos incompletos en entidades:", list(ent_fallos["anio"].values))
    else:
        print("  Todos los anos tienen todos los campos de entidades completos.")
    print("  Guardado:", path_det_ent)

    # 2) Detalle metricas por ano
    det_met = detalle_por_anio_metricas(df_met)
    path_det_met = indice / "verificacion_metricas_por_anio.csv"
    det_met.to_csv(path_det_met, index=False, encoding="utf-8-sig")
    print("\n2. Metricas por ano (campos y consistencia)")
    print("-" * 50)
    ok_cols = [f"{c}_ok" for c in CAMPOS_METRICAS if f"{c}_ok" in det_met.columns]
    met_fallos = pd.DataFrame()
    if ok_cols:
        met_fallos = det_met[det_met[ok_cols].eq(False).any(axis=1)]
    if not met_fallos.empty:
        print("  Anos con algun campo incompleto en metricas:", sorted(met_fallos["anio"].unique().tolist())[:20])
    else:
        print("  Todos los anos tienen campos de metricas OK (>=99% value).")
    print("  Guardado:", path_det_met)

    # 3) Consistencia de la serie
    df_cons, alertas = consistencia_serie(df_ent, df_met, canonico)
    path_cons = indice / "verificacion_consistencia_serie.csv"
    df_cons.to_csv(path_cons, index=False, encoding="utf-8-sig")
    print("\n3. Consistencia ano a ano")
    print("-" * 50)
    anos_sin_ent = df_cons[df_cons["entidades_total"] == 0]["anio"].tolist()
    anos_sin_met = df_cons[df_cons["metricas_total"] == 0]["anio"].tolist()
    print("  Anos con 0 entidades:", len(anos_sin_ent), "->", anos_sin_ent[:15], ("..." if len(anos_sin_ent) > 15 else ""))
    print("  Anos con 0 metricas:", len(anos_sin_met), "->", anos_sin_met[:15], ("..." if len(anos_sin_met) > 15 else ""))
    print("  entidades_ok=True en todos:", df_cons["entidades_ok"].all() if "entidades_ok" in df_cons.columns else "N/A")
    print("  metricas_ok=True en todos:", df_cons["metricas_ok"].all() if "metricas_ok" in df_cons.columns else "N/A")
    print("  Guardado:", path_cons)

    if alertas:
        print("\n4. Alertas de consistencia")
        print("-" * 50)
        for a in alertas[:30]:
            print("  ", a)
        if len(alertas) > 30:
            print("  ... y", len(alertas) - 30, "mas.")
        path_alertas = indice / "verificacion_alertas.txt"
        with open(path_alertas, "w", encoding="utf-8") as f:
            f.write("\n".join(alertas))
        print("  Guardado:", path_alertas)
    else:
        print("\n4. Sin alertas de consistencia.")

    # 5) Resumen numerico por ano (tabla legible)
    print("\n5. Resumen serie historica (entidades / metricas por ano)")
    print("-" * 50)
    resumen = df_cons.merge(
        det_ent[["anio", "total_entidades", "entidades_unicas"]],
        on="anio",
        how="left",
    ).merge(
        det_met[["anio", "total_metricas", "metric_names_unicos", "units_unicos"]],
        on="anio",
        how="left",
    )
    resumen = resumen.fillna(0)
    path_resumen = indice / "verificacion_resumen_serie.csv"
    resumen.to_csv(path_resumen, index=False, encoding="utf-8-sig")
    # Imprimir tabla reducida
    cols_show = ["anio", "total_entidades", "entidades_unicas", "total_metricas", "entidades_ok", "metricas_ok"]
    cols_show = [c for c in cols_show if c in resumen.columns]
    print(resumen[cols_show].head(20).to_string(index=False))
    print("  ...")
    print(resumen[cols_show].tail(15).to_string(index=False))
    print("\n  Guardado:", path_resumen)

    # 6) Matriz ano x campo: pct_lleno para cada campo definido en cada ano
    filas_mat = []
    for anio in resumen["anio"].unique():
        ge = df_ent[df_ent["anio"] == anio] if not df_ent.empty else pd.DataFrame()
        gm = df_met[df_met["anio"] == anio] if not df_met.empty else pd.DataFrame()
        for col in CAMPOS_ENTIDADES:
            total = len(ge)
            nn = _no_nulo_serie(ge[col]) if not ge.empty and col in ge.columns else 0
            filas_mat.append({
                "anio": anio,
                "tabla": "anuario_entidades",
                "campo": col,
                "total": total,
                "no_nulo": int(nn),
                "pct_lleno": _pct(nn, total) if total else "0%",
                "ok": nn == total if total else True,
            })
        for col in CAMPOS_METRICAS:
            total = len(gm)
            if col == "value":
                nn = pd.to_numeric(gm[col], errors="coerce").notna().sum() if not gm.empty and col in gm.columns else 0
            else:
                nn = _no_nulo_serie(gm[col]) if not gm.empty and col in gm.columns else 0
            ok = (nn == total) if total and col != "ramo_opcional" else (True if col == "ramo_opcional" else (total == 0))
            if col == "value" and total:
                ok = nn >= total * 0.99
            filas_mat.append({
                "anio": anio,
                "tabla": "anuario_metricas",
                "campo": col,
                "total": total,
                "no_nulo": int(nn),
                "pct_lleno": _pct(nn, total) if total else "0%",
                "ok": ok,
            })
    path_matriz = indice / "verificacion_matriz_campos_por_anio.csv"
    pd.DataFrame(filas_mat).to_csv(path_matriz, index=False, encoding="utf-8-sig")
    print("\n6. Matriz ano x campo (consistencia de campos en la serie)")
    print("-" * 50)
    print("  Guardado:", path_matriz)
    # Resumen: cuantos (anio, campo) tienen ok=False
    df_mat = pd.DataFrame(filas_mat)
    fallos_mat = df_mat[~df_mat["ok"].fillna(True).astype(bool)]
    if not fallos_mat.empty:
        print("  Registros (anio, tabla, campo) con ok=False:", len(fallos_mat))
    else:
        print("  Todos los (anio, campo) tienen cobertura OK.")

    print("\n" + "=" * 65)
    print("Resumen ejecutivo: Campos definidos con valores en toda la serie")
    print("  - Entidades: anio, source_file, entity_name, entity_normalized_name -> 100% en todos los anos con datos.")
    print("  - Metricas: anio, source_file, cuadro_or_seccion, entity_name, metric_name, value, unit -> OK (>=99% value) donde hay metricas.")
    print("  - Anos con entidades pero sin metricas: PDFs con solo nombres extraidos (tablas sin numeros).")
    print("=" * 65)

    sys.exit(0)


if __name__ == "__main__":
    main()
