"""
Verifica inclusion de companias por anuario (ventana 2014-2024).
- Lista que companias aparecen en cada ano (inclucion por anuario).
- Solo empresas probables (es_empresa_probable=True) para consistencia.
- Genera: inclusion_companias_por_anuario, companias_activas_ventana.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.anuarios_paths import (
    ensure_anuarios_dirs,
    SEGURO_EN_CIFRAS_INDICE,
    SEGURO_EN_CIFRAS_ENTIDADES,
    SEGURO_EN_CIFRAS_VACIADO,
)
from config.anuarios_paths import VACIADO_ENTIDADES_CSV

ANO_INICIO = 2014
ANO_FIN = 2024

CATALOGO_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "catalogo_entidades_base.csv"
INCLUSION_CSV = SEGURO_EN_CIFRAS_INDICE / "inclusion_companias_por_anuario_2014_2024.csv"
ACTIVAS_CSV = SEGURO_EN_CIFRAS_INDICE / "companias_activas_ventana_2014_2024.csv"


def main():
    ensure_anuarios_dirs()
    SEGURO_EN_CIFRAS_INDICE.mkdir(parents=True, exist_ok=True)

    if not VACIADO_ENTIDADES_CSV.exists():
        print("No existe vaciado de entidades:", VACIADO_ENTIDADES_CSV)
        sys.exit(1)

    df_ent = pd.read_csv(VACIADO_ENTIDADES_CSV)
    df_ent = df_ent[(df_ent["anio"] >= ANO_INICIO) & (df_ent["anio"] <= ANO_FIN)]

    catalogo = pd.read_csv(CATALOGO_CSV) if CATALOGO_CSV.exists() else None
    if catalogo is None:
        print("No existe catalogo:", CATALOGO_CSV)
        print("Ejecutar primero: python scripts/anuarios_construir_entidades_y_matriz.py")
        sys.exit(1)

    # Inclusion: una fila por (anio, entity_normalized_name) con datos del catalogo
    inclusion = df_ent[["anio", "entity_normalized_name", "entity_name"]].drop_duplicates()
    inclusion = inclusion.merge(
        catalogo[["entity_normalized_name", "canonical_name", "es_empresa_probable"]],
        on="entity_normalized_name",
        how="left",
    )
    inclusion["es_empresa_probable"] = inclusion["es_empresa_probable"].fillna(False).astype(bool)
    inclusion.to_csv(INCLUSION_CSV, index=False, encoding="utf-8-sig")
    print("Inclusion por anuario guardada:", INCLUSION_CSV)
    print("  Total registros (anio, entidad):", len(inclusion))

    # Solo empresas probables
    inclusion_emp = inclusion[inclusion["es_empresa_probable"]]
    print("  Solo empresas probables:", len(inclusion_emp))

    # Por ano: cuantas empresas probables activas
    por_anio = inclusion_emp.groupby("anio").agg(
        n_companias=("entity_normalized_name", "nunique"),
    ).reset_index()
    print("\nCompanias probables por ano:")
    print(por_anio.to_string(index=False))

    # Companias activas en ventana: una fila por empresa (solo probables) con anios en que aparece
    activas = inclusion_emp.groupby("entity_normalized_name", as_index=False).agg(
        canonical_name=("canonical_name", "first"),
        anios_lista=("anio", lambda x: ",".join(str(a) for a in sorted(x.unique()))),
        n_anios=("anio", "nunique"),
        primer_anio_ventana=("anio", "min"),
        ultimo_anio_ventana=("anio", "max"),
    )
    activas = activas.sort_values("n_anios", ascending=False)
    activas.to_csv(ACTIVAS_CSV, index=False, encoding="utf-8-sig")
    print("\nCompanias activas (solo probables) guardadas:", ACTIVAS_CSV)
    print("  Total empresas probables en ventana:", len(activas))
    print("  Con al menos 5 anos:", (activas["n_anios"] >= 5).sum())
    print("  Con 11 anos (todo el periodo):", (activas["n_anios"] >= 11).sum())

    sys.exit(0)


if __name__ == "__main__":
    main()
