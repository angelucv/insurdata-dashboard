"""
Corrida: por entidad, todos los campos y su historico para verificar consistencia.
Genera:
  1. historico_entidad_campo_anio.csv (long: entidad, campo, anio, value)
  2. vista_entidad_campo_por_anio.csv (wide: entidad, campo, 2014, 2015, ..., 2024)
  3. resumen_consistencia_por_entidad.csv (por entidad: n_anios, n_campos con dato, detalle por campo)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from config.anuarios_paths import (
    ensure_anuarios_dirs,
    SEGURO_EN_CIFRAS_INDICE,
    SEGURO_EN_CIFRAS_VACIADO,
    SEGURO_EN_CIFRAS_ENTIDADES,
    SEGURO_EN_CIFRAS_VARIABLES,
)
from config.anuarios_paths import CANONICO_CSV

ANO_INICIO = 2014
ANO_FIN = 2024

MATRIZ_BASE_MADRE_CSV = SEGURO_EN_CIFRAS_VACIADO / "matriz_base_madre_2014_2024.csv"
MATRIZ_FULL_CSV = SEGURO_EN_CIFRAS_VACIADO / "matriz_empresa_anio_campos.csv"
BASE_MADRE_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "base_madre_entidades_2014_2024.csv"

OUT_HISTORICO_LONG = SEGURO_EN_CIFRAS_INDICE / "historico_entidad_campo_anio.csv"
OUT_VISTA_WIDE = SEGURO_EN_CIFRAS_INDICE / "vista_entidad_campo_por_anio.csv"
OUT_RESUMEN = SEGURO_EN_CIFRAS_INDICE / "resumen_consistencia_por_entidad.csv"


def get_campos_canonico() -> list[str]:
    if CANONICO_CSV.exists():
        df = pd.read_csv(CANONICO_CSV)
        return df["metric_name"].dropna().unique().tolist()
    return []


def main():
    ensure_anuarios_dirs()
    SEGURO_EN_CIFRAS_INDICE.mkdir(parents=True, exist_ok=True)

    # Usar matriz base madre (ventana 2014-2024) para consistencia en ventana
    if not MATRIZ_BASE_MADRE_CSV.exists():
        print("No existe matriz base madre:", MATRIZ_BASE_MADRE_CSV)
        print("Ejecutar: python scripts/anuarios_base_madre_2014_2024.py")
        sys.exit(1)

    df = pd.read_csv(MATRIZ_BASE_MADRE_CSV, low_memory=False)
    id_cols = ["nombre_normalizado_madre", "anio", "canonical_name", "entity_name_en_anio", "entity_normalized_name"]
    metric_cols = [c for c in df.columns if c not in id_cols]

    campos_canon = get_campos_canonico()
    metric_cols = [c for c in metric_cols if c in df.columns]

    anios = sorted(df["anio"].dropna().unique().astype(int).tolist())
    if not anios:
        anios = list(range(ANO_INICIO, ANO_FIN + 1))

    print("Historico por entidad - campos y consistencia")
    print("=" * 60)
    print("Entidades (nombre_normalizado_madre):", df["nombre_normalizado_madre"].nunique())
    print("Anios en matriz:", anios)
    print("Campos (metricas):", len(metric_cols))

    # 1) Long: entidad, canonical_name, campo, anio, value (solo con valor)
    long_rows = []
    for _, row in df.iterrows():
        ent = row.get("nombre_normalizado_madre") or row.get("entity_normalized_name")
        canon = row.get("canonical_name", "")
        anio = row.get("anio")
        if pd.isna(ent) or pd.isna(anio):
            continue
        for camp in metric_cols:
            val = row.get(camp)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                continue
            try:
                v = float(val)
            except (TypeError, ValueError):
                continue
            long_rows.append({
                "nombre_normalizado_madre": ent,
                "canonical_name": canon,
                "campo": camp,
                "anio": int(anio),
                "value": round(v, 4),
            })
    long_df = pd.DataFrame(long_rows)
    long_df.to_csv(OUT_HISTORICO_LONG, index=False, encoding="utf-8-sig")
    print("\n1. Historico long guardado:", OUT_HISTORICO_LONG, "->", len(long_df), "registros")

    # 2) Vista wide: una fila por (entidad, campo), columnas 2014..2024
    wide_rows = []
    for (ent, canon), g in df.groupby(["nombre_normalizado_madre", "canonical_name"], dropna=False):
        canon = canon if pd.notna(canon) else ent
        for camp in metric_cols:
            vals = g.set_index("anio")[camp]
            row = {"nombre_normalizado_madre": ent, "canonical_name": canon, "campo": camp}
            for a in anios:
                v = vals.get(a)
                if v is not None and not (isinstance(v, float) and np.isnan(v)):
                    try:
                        row[str(a)] = round(float(v), 4)
                    except (TypeError, ValueError):
                        row[str(a)] = v
                else:
                    row[str(a)] = ""
            wide_rows.append(row)
    wide_df = pd.DataFrame(wide_rows)
    # Solo filas donde al menos un ano tiene valor
    has_val = wide_df[[str(a) for a in anios]].apply(
        lambda x: x.astype(str).str.strip().ne("").any(), axis=1
    )
    wide_df = wide_df[has_val]
    wide_df.to_csv(OUT_VISTA_WIDE, index=False, encoding="utf-8-sig")
    print("2. Vista wide (entidad x campo x anos) guardada:", OUT_VISTA_WIDE, "->", len(wide_df), "filas")

    # 3) Resumen consistencia por entidad
    # Por entidad: n_anios presente, por cada campo: n_anios con dato, pct
    ent_anios = df.groupby("nombre_normalizado_madre").agg(
        canonical_name=("canonical_name", "first"),
        n_anios_presente=("anio", "nunique"),
        anios_lista=("anio", lambda x: ",".join(str(int(a)) for a in sorted(x.dropna().unique()))),
    ).reset_index()

    resumen_rows = []
    for _, row_ent in ent_anios.iterrows():
        ent = row_ent["nombre_normalizado_madre"]
        canon = row_ent["canonical_name"]
        n_anios = int(row_ent["n_anios_presente"])
        sub = df[df["nombre_normalizado_madre"] == ent]
        n_campos_con_dato = 0
        detalle = []
        campos_ok = []
        for camp in metric_cols:
            n = sub[camp].notna().sum()
            if n > 0:
                n_campos_con_dato += 1
                pct = round(100 * n / n_anios, 1) if n_anios else 0
                detalle.append(f"{camp}:{n}/{n_anios}({pct}%)")
                if pct >= 90:
                    campos_ok.append(camp)
        resumen_rows.append({
            "nombre_normalizado_madre": ent,
            "canonical_name": canon,
            "n_anios_presente": n_anios,
            "anios_lista": row_ent["anios_lista"],
            "n_campos_con_algun_dato": n_campos_con_dato,
            "n_campos_objetivo": len(metric_cols),
            "campos_consistentes_90pct": ";".join(campos_ok) if campos_ok else "",
            "n_campos_consistentes_90pct": len(campos_ok),
            "detalle_campos": " | ".join(detalle[:15]) + (" ..." if len(detalle) > 15 else ""),
        })
    resumen_df = pd.DataFrame(resumen_rows)
    resumen_df = resumen_df.sort_values(["n_campos_con_algun_dato", "n_anios_presente"], ascending=[False, False])
    resumen_df.to_csv(OUT_RESUMEN, index=False, encoding="utf-8-sig")
    print("3. Resumen consistencia por entidad guardado:", OUT_RESUMEN, "->", len(resumen_df), "entidades")

    # Resumen por consola
    con_dato = resumen_df[resumen_df["n_campos_con_algun_dato"] > 0]
    print("\nResumen consistencia:")
    print("  Entidades con al menos 1 campo con dato:", len(con_dato))
    print("  Entidades con al menos 5 campos:", (resumen_df["n_campos_con_algun_dato"] >= 5).sum())
    print("  Entidades con al menos 1 campo consistente (90%+ anos):", (resumen_df["n_campos_consistentes_90pct"] >= 1).sum())
    if len(con_dato) > 0:
        print("  Top 5 entidades por cantidad de campos con dato:")
        for _, r in resumen_df.head(5).iterrows():
            print("   ", r["nombre_normalizado_madre"][:45], "->", r["n_campos_con_algun_dato"], "campos,", r["n_anios_presente"], "anos")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
