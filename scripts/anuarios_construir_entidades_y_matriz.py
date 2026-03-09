"""
Construye la estructura centrada en la entidad base:
1. Catalogo de entidades: nombres normalizados unicos con nombre canonico y rango de anos.
2. Variantes por ano: como se llama cada compania en cada ano (para verificar normalizacion).
3. Matriz empresa x ano x campos: una fila por (entity_normalized_name, anio) con columnas por metrica.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from config.anuarios_paths import (
    ensure_anuarios_dirs,
    SEGURO_EN_CIFRAS_ENTIDADES,
    SEGURO_EN_CIFRAS_VACIADO,
    SEGURO_EN_CIFRAS_VARIABLES,
    VACIADO_ENTIDADES_CSV,
    METRICAS_CSV,
    CANONICO_CSV,
)

# Rutas de salida
CATALOGO_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "catalogo_entidades_base.csv"
VARIANTES_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "variantes_nombre_por_anio.csv"
MATRIZ_CSV = SEGURO_EN_CIFRAS_VACIADO / "matriz_empresa_anio_campos.csv"

# Nombres normalizados que no son empresas (ruido de extraccion)
EXCLUIR_NORMALIZED = {
    "", "seguros", "empresa", "total", "nombre empresa", "razon social",
    "miles de bolivares", "miles de bolivares ", "fuente:", "superintendencia",
    "republica", "ministerio", "cuadro", "indice", "pagina", "titulo",
}
# Patrones que sugieren que es una empresa (C.A., S.A., Seguros, etc.)
PATRON_EMPRESA = re.compile(
    r"(c\.?\s*a\.?|s\.?\s*a\.?|seguros?|aseguradora|reaseguro)",
    re.I
)


def _es_empresa_probable(norm: str, entity_name: str) -> bool:
    """Heuristica: parece nombre de compania y no cabecera/ruido."""
    if not norm or len(norm) < 6:
        return False
    if norm in EXCLUIR_NORMALIZED:
        return False
    if norm.isdigit() or (len(norm) <= 4 and norm.replace(".", "").isdigit()):
        return False
    if "reservas" in norm and "tecnica" in norm:
        return False
    if "prima" in norm or "siniestro" in norm or "gasto" in norm:
        if "empresa" not in norm and "compania" not in norm:
            return False
    return bool(PATRON_EMPRESA.search(norm) or PATRON_EMPRESA.search(entity_name or ""))


def build_catalogo(df_ent: pd.DataFrame) -> pd.DataFrame:
    """Catalogo: entity_normalized_name, canonical_name, primer_anio, ultimo_anio, total_anios, variantes_nombre, es_empresa_probable."""
    g = df_ent.groupby("entity_normalized_name", as_index=False).agg(
        primer_anio=("anio", "min"),
        ultimo_anio=("anio", "max"),
        total_anios=("anio", "nunique"),
        variantes_nombre=("entity_name", "nunique"),
    )
    # Nombre canonico: el mas reciente por ultimo_anio (o el mas frecuente)
    canonico = []
    for norm in g["entity_normalized_name"]:
        sub = df_ent[df_ent["entity_normalized_name"] == norm]
        # Preferir el nombre del ultimo ano en que aparece
        ultimo = sub["anio"].max()
        nombres_ultimo = sub[sub["anio"] == ultimo]["entity_name"].dropna().unique()
        name = nombres_ultimo[0] if len(nombres_ultimo) > 0 else sub["entity_name"].mode().iloc[0] if len(sub["entity_name"].mode()) else norm
        canonico.append(name)
    g["canonical_name"] = canonico
    g["es_empresa_probable"] = g.apply(
        lambda r: _es_empresa_probable(r["entity_normalized_name"], r["canonical_name"]),
        axis=1,
    )
    return g


def build_variantes(df_ent: pd.DataFrame) -> pd.DataFrame:
    """Tabla entity_normalized_name, anio, entity_name (nombre tal cual en ese ano)."""
    return df_ent[["entity_normalized_name", "anio", "entity_name"]].drop_duplicates()


def build_matriz(
    df_ent: pd.DataFrame,
    df_met: pd.DataFrame,
    catalogo: pd.DataFrame,
    metricas_columna: list[str] | None = None,
) -> pd.DataFrame:
    """
    Matriz: una fila por (entity_normalized_name, anio) con columnas:
    entity_normalized_name, anio, canonical_name, entity_name_en_anio, [metric_name_1, ...]
    Incluye todos los (entidad, ano) aunque no tengan metricas (columnas vacias).
    """
    # Base: todos los (entity_normalized_name, anio) que aparecen en entidades
    ent_anos = df_ent[["entity_normalized_name", "anio"]].drop_duplicates()
    cat = catalogo[["entity_normalized_name", "canonical_name"]]
    variantes = df_ent[["entity_normalized_name", "anio", "entity_name"]].drop_duplicates()
    variantes = variantes.rename(columns={"entity_name": "entity_name_en_anio"})
    matriz = ent_anos.merge(cat, on="entity_normalized_name", how="left")
    matriz = matriz.merge(variantes, on=["entity_normalized_name", "anio"], how="left")

    if df_met.empty:
        return matriz

    # Unir metricas con entidades para tener entity_normalized_name
    df_met = df_met.merge(
        df_ent[["anio", "entity_name", "entity_normalized_name"]].drop_duplicates(),
        on=["anio", "entity_name"],
        how="left",
    )
    df_met = df_met[df_met["entity_normalized_name"].notna()]

    pivot = df_met.pivot_table(
        index=["entity_normalized_name", "anio"],
        columns="metric_name",
        values="value",
        aggfunc="first",
    ).reset_index()
    pivot.columns = [str(c).strip().replace(" ", "_") for c in pivot.columns]

    # Left join: mantener todas las filas de matriz y rellenar metricas donde existan
    matriz = matriz.merge(
        pivot,
        on=["entity_normalized_name", "anio"],
        how="left",
    )
    # Incluir todas las columnas canonicas (rellenar faltantes con NaN) para verificacion de 20+ campos
    cols_id = ["entity_normalized_name", "anio", "canonical_name", "entity_name_en_anio"]
    if CANONICO_CSV.exists():
        try:
            canon = pd.read_csv(str(CANONICO_CSV))
            metricas_canon = canon["metric_name"].dropna().unique().tolist()
            for m in metricas_canon:
                if m not in matriz.columns:
                    matriz[m] = np.nan
        except Exception:
            pass
    cols_resto = [c for c in matriz.columns if c not in cols_id]
    return matriz[cols_id + cols_resto]


def main():
    ensure_anuarios_dirs()
    SEGURO_EN_CIFRAS_ENTIDADES.mkdir(parents=True, exist_ok=True)

    if not VACIADO_ENTIDADES_CSV.exists():
        print("No existe vaciado de entidades:", VACIADO_ENTIDADES_CSV)
        sys.exit(1)

    df_ent = pd.read_csv(VACIADO_ENTIDADES_CSV)
    df_met = pd.read_csv(METRICAS_CSV) if METRICAS_CSV.exists() else pd.DataFrame()

    print("Estructura centrada en entidad base - Seguro en Cifras")
    print("=" * 60)

    # 1) Catalogo de entidades base
    catalogo = build_catalogo(df_ent)
    catalogo.to_csv(CATALOGO_CSV, index=False, encoding="utf-8-sig")
    n_total = len(catalogo)
    n_probables = catalogo["es_empresa_probable"].sum()
    print("\n1. Catalogo de entidades base")
    print("   Total nombres normalizados unicos:", n_total)
    print("   Con heuristica 'es_empresa_probable':", n_probables)
    print("   Guardado:", CATALOGO_CSV)

    # 2) Variantes nombre por ano
    variantes = build_variantes(df_ent)
    variantes.to_csv(VARIANTES_CSV, index=False, encoding="utf-8-sig")
    print("\n2. Variantes de nombre por ano (verificar normalizacion)")
    print("   Registros:", len(variantes))
    print("   Guardado:", VARIANTES_CSV)

    # 3) Matriz empresa x ano x campos
    matriz = build_matriz(df_ent, df_met, catalogo)
    matriz.to_csv(MATRIZ_CSV, index=False, encoding="utf-8-sig")
    print("\n3. Matriz empresa x ano x campos")
    print("   Filas (entity_normalized_name, anio):", len(matriz))
    print("   Columnas:", list(matriz.columns[:6]), "...", len(matriz.columns), "total")
    print("   Guardado:", MATRIZ_CSV)

    # Resumen: entidades con mas anos (trayectoria larga)
    print("\n4. Ejemplo: entidades con mas anos en la serie")
    top = catalogo.nlargest(10, "total_anios")[["entity_normalized_name", "canonical_name", "primer_anio", "ultimo_anio", "total_anios", "variantes_nombre"]]
    print(top.to_string(index=False))

    print("\n5. Verificacion de normalizacion")
    print("   Variantes con mas de un nombre distinto (cambio de razon social):")
    multi = catalogo[catalogo["variantes_nombre"] > 1].sort_values("variantes_nombre", ascending=False)
    print("   Entidades con variantes_nombre > 1:", len(multi))
    if len(multi) > 0:
        print(multi.head(8).to_string(index=False))

    # 6) Reporte verificacion: para cada entidad con variantes, ejemplos de nombres por ano
    verif = variantes.merge(
        catalogo[["entity_normalized_name", "variantes_nombre", "es_empresa_probable"]],
        on="entity_normalized_name",
        how="left",
    )
    verif = verif[verif["variantes_nombre"] > 1].sort_values(["variantes_nombre", "entity_normalized_name", "anio"], ascending=[False, True, True])
    path_verif = SEGURO_EN_CIFRAS_ENTIDADES / "verificacion_normalizacion_variantes.csv"
    verif.to_csv(path_verif, index=False, encoding="utf-8-sig")
    print("\n6. Reporte verificacion normalizacion (entidades con mas de un nombre)")
    print("   Guardado:", path_verif)

    # 7) Resumen matriz: cuantos (entidad, ano) tienen al menos un campo de metrica
    cols_met = [c for c in matriz.columns if c not in ("entity_normalized_name", "anio", "canonical_name", "entity_name_en_anio")]
    con_algun_valor = matriz[cols_met].notna().any(axis=1).sum()
    print("\n7. Matriz: filas con al menos una metrica rellenada:", int(con_algun_valor), "/", len(matriz))

    sys.exit(0)


if __name__ == "__main__":
    main()
