"""
Construye la base madre para la ventana 2014-2024:
- Aplica normalizacion propuesta (nombre_normalizado_madre) para unificar variantes.
- Filtra entidades y matriz al periodo 2014-2024 (ventana de 10+1 años).
- Genera: catalogo base madre, mapeo de normalizacion, matriz filtrada.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.anuarios_paths import (
    ensure_anuarios_dirs,
    SEGURO_EN_CIFRAS_ENTIDADES,
    SEGURO_EN_CIFRAS_VACIADO,
    VACIADO_ENTIDADES_CSV,
)
from src.etl.normalizacion_base_madre import normalize_para_base_madre

# Ventana base madre: desde 2014, 10 años (2014 a 2024 inclusive = 11 años)
ANO_INICIO_BASE_MADRE = 2014
ANO_FIN_BASE_MADRE = 2024

CATALOGO_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "catalogo_entidades_base.csv"
BASE_MADRE_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "base_madre_entidades_2014_2024.csv"
NORMALIZACION_MADRE_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "normalizacion_base_madre_2014_2024.csv"
MATRIZ_CSV = SEGURO_EN_CIFRAS_VACIADO / "matriz_empresa_anio_campos.csv"
MATRIZ_BASE_MADRE_CSV = SEGURO_EN_CIFRAS_VACIADO / "matriz_base_madre_2014_2024.csv"


def main():
    ensure_anuarios_dirs()
    SEGURO_EN_CIFRAS_ENTIDADES.mkdir(parents=True, exist_ok=True)

    if not VACIADO_ENTIDADES_CSV.exists():
        print("No existe vaciado de entidades:", VACIADO_ENTIDADES_CSV)
        sys.exit(1)

    df_ent = pd.read_csv(VACIADO_ENTIDADES_CSV)
    catalogo = pd.read_csv(CATALOGO_CSV) if CATALOGO_CSV.exists() else None

    # Filtrar entidades que aparecen en la ventana 2014-2024
    ventana = df_ent[
        (df_ent["anio"] >= ANO_INICIO_BASE_MADRE) & (df_ent["anio"] <= ANO_FIN_BASE_MADRE)
    ]
    entidades_ventana = ventana["entity_normalized_name"].unique()

    print("Base madre - Seguro en Cifras")
    print("Ventana:", ANO_INICIO_BASE_MADRE, "-", ANO_FIN_BASE_MADRE)
    print("=" * 60)

    # Estadisticas por entidad en la ventana (siempre desde datos)
    g_ventana = ventana.groupby("entity_normalized_name", as_index=False).agg(
        primer_anio_ventana=("anio", "min"),
        ultimo_anio_ventana=("anio", "max"),
        total_anios_ventana=("anio", "nunique"),
    )
    ultimo_ventana = ventana.loc[ventana.groupby("entity_normalized_name")["anio"].idxmax()]
    g_ventana = g_ventana.merge(
        ultimo_ventana[["entity_normalized_name", "entity_name"]].rename(
            columns={"entity_name": "nombre_ultimo_anio_ventana"}
        ),
        on="entity_normalized_name",
        how="left",
    )

    # 1) Aplicar normalizacion para base madre: entity_normalized_name -> nombre_normalizado_madre
    # Usamos el nombre canonico cuando exista para unificar mejor; si no, el entity_normalized_name
    if catalogo is not None:
        cat_ventana = catalogo[catalogo["entity_normalized_name"].isin(entidades_ventana)].copy()
        cat_ventana["nombre_normalizado_madre"] = cat_ventana["canonical_name"].fillna(
            cat_ventana["entity_normalized_name"]
        ).map(normalize_para_base_madre)
        cat_ventana = cat_ventana.merge(
            g_ventana,
            on="entity_normalized_name",
            how="left",
        )
        cat_ventana["canonical_name"] = cat_ventana["canonical_name"].fillna(
            cat_ventana.get("nombre_ultimo_anio_ventana", "")
        )
    else:
        cat_ventana = pd.DataFrame({"entity_normalized_name": entidades_ventana})
        cat_ventana["nombre_normalizado_madre"] = cat_ventana["entity_normalized_name"].map(
            normalize_para_base_madre
        )
        cat_ventana = cat_ventana.merge(g_ventana, on="entity_normalized_name", how="left")
        cat_ventana["canonical_name"] = cat_ventana.get("nombre_ultimo_anio_ventana", "")
        cat_ventana["es_empresa_probable"] = True

    # 2) Mapeo normalizacion: entity_normalized_name -> nombre_normalizado_madre (solo ventana)
    mapeo = cat_ventana[["entity_normalized_name", "nombre_normalizado_madre"]].drop_duplicates()
    if "canonical_name" in cat_ventana.columns:
        mapeo = mapeo.merge(
            cat_ventana[["entity_normalized_name", "canonical_name"]].drop_duplicates(),
            on="entity_normalized_name",
            how="left",
        )
    mapeo.to_csv(NORMALIZACION_MADRE_CSV, index=False, encoding="utf-8-sig")
    print("\n1. Mapeo normalizacion (entity -> nombre_normalizado_madre)")
    print("   Registros:", len(mapeo))
    print("   Guardado:", NORMALIZACION_MADRE_CSV)

    # 3) Catalogo base madre: una fila por nombre_normalizado_madre (puede agrupar varias entity_normalized_name)
    # Nombre canonico: el mas reciente en la ventana; si hay varias entidades fusionadas, el primero por orden
    agg_base = (
        cat_ventana.groupby("nombre_normalizado_madre", as_index=False)
        .agg(
            entity_normalized_name_originales=("entity_normalized_name", lambda x: "|".join(sorted(set(x)))),
            cantidad_variantes=("entity_normalized_name", "nunique"),
            primer_anio_ventana=("primer_anio_ventana", "min"),
            ultimo_anio_ventana=("ultimo_anio_ventana", "max"),
            total_anios_ventana=("total_anios_ventana", "max"),
        )
    )
    # Nombre canonico representativo: el canonical_name de la entidad con ultimo_anio_ventana max
    idx_repr = cat_ventana.groupby("nombre_normalizado_madre")["ultimo_anio_ventana"].idxmax()
    canonico_repr = cat_ventana.loc[idx_repr, ["nombre_normalizado_madre", "canonical_name"]]
    if "canonical_name" not in canonico_repr.columns:
        canonico_repr["canonical_name"] = canonico_repr["nombre_normalizado_madre"]
    agg_base = agg_base.merge(
        canonico_repr.rename(columns={"canonical_name": "canonical_name_representativo"}),
        on="nombre_normalizado_madre",
        how="left",
    )
    if "es_empresa_probable" in cat_ventana.columns:
        # Si al menos una variante es empresa probable, la base madre lo es
        es_emp = cat_ventana.groupby("nombre_normalizado_madre")["es_empresa_probable"].any().reset_index()
        agg_base = agg_base.merge(es_emp, on="nombre_normalizado_madre", how="left")
    else:
        agg_base["es_empresa_probable"] = True

    # Orden: empresas probables primero, luego por total_anios_ventana
    agg_base = agg_base.sort_values(
        ["es_empresa_probable", "total_anios_ventana"],
        ascending=[False, False],
    )
    agg_base.to_csv(BASE_MADRE_CSV, index=False, encoding="utf-8-sig")
    n_total = len(agg_base)
    n_empresas = agg_base["es_empresa_probable"].sum() if "es_empresa_probable" in agg_base.columns else 0
    n_unificadas = (agg_base["cantidad_variantes"] > 1).sum()
    print("\n2. Catalogo base madre (una fila por nombre_normalizado_madre)")
    print("   Claves unicas (nombre_normalizado_madre):", n_total)
    print("   Marcadas como empresa probable:", int(n_empresas))
    print("   Unificadas (varias entity_normalized_name -> 1 madre):", int(n_unificadas))
    print("   Guardado:", BASE_MADRE_CSV)

    # 4) Matriz filtrada 2014-2024 con columna nombre_normalizado_madre
    if not MATRIZ_CSV.exists():
        print("\n3. Matriz base madre: no existe", MATRIZ_CSV)

    else:
        matriz = pd.read_csv(MATRIZ_CSV, low_memory=False)
        matriz = matriz[
            (matriz["anio"] >= ANO_INICIO_BASE_MADRE) & (matriz["anio"] <= ANO_FIN_BASE_MADRE)
        ]
        matriz = matriz.merge(
            mapeo[["entity_normalized_name", "nombre_normalizado_madre"]],
            on="entity_normalized_name",
            how="left",
        )
        # Reordenar columnas: nombre_normalizado_madre despues de entity_normalized_name
        cols = list(matriz.columns)
        if "nombre_normalizado_madre" in cols:
            cols.remove("nombre_normalizado_madre")
            idx = cols.index("entity_normalized_name") + 1
            cols = cols[:idx] + ["nombre_normalizado_madre"] + cols[idx:]
            matriz = matriz[cols]
        matriz.to_csv(MATRIZ_BASE_MADRE_CSV, index=False, encoding="utf-8-sig")
        print("\n3. Matriz base madre (ventana 2014-2024)")
        print("   Filas (entity, anio):", len(matriz))
        print("   Guardado:", MATRIZ_BASE_MADRE_CSV)

    print("\nResumen ventana 2014-2024:")
    print("  - Entidades (entity_normalized_name) en ventana:", len(entidades_ventana))
    print("  - Claves base madre (nombre_normalizado_madre):", n_total)
    print("  - Unificaciones (variantes -> 1 madre):", int(n_unificadas))
    sys.exit(0)


if __name__ == "__main__":
    main()
