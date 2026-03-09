"""
Pruebas por empresa: a partir de la base staged (empresa, mes, 8 campos)
genera resumen anual por empresa y permite inspeccionar la serie mes a mes
de una o varias compañías. Útil para validar antes de pasar a CLEAN/Supabase.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_STAGED
from src.etl.staged_resumen import CAMPOS_EXCEL

STAGED_2023 = Path(DATA_STAGED) / "2023"
BASE_CSV = STAGED_2023 / "resumen_por_empresa_2023_base.csv"
RESUMEN_ANUAL_CSV = STAGED_2023 / "resumen_anual_por_empresa_2023.csv"

# Para totales anuales usamos el último mes con dato (acumulado YTD en dic = año)
CAMPOS_FLUJO = [
    "primas_netas_ves",
    "siniestros_pagados_ves",
    "comisiones_ves",
    "gastos_adquisicion_ves",
    "gastos_administracion_ves",
    "gastos_operativos_ves",
]
CAMPOS_RESERVA = ["reservas_brutas_ves", "reservas_netas_ves", "siniestros_totales_ves"]


def load_base() -> pd.DataFrame:
    if not BASE_CSV.exists():
        raise FileNotFoundError("Ejecuta antes la compilación: verificar_compilado_8_campos.py")
    df = pd.read_csv(BASE_CSV, encoding="utf-8-sig")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
    return df


def resumen_anual_por_empresa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Una fila por empresa con: n_meses, último mes con dato, valor dic (YTD) para
    primas/siniestros/gastos, promedios de reservas (son saldos mes a mes).
    """
    entidades = df["entity_normalized"].dropna().unique()
    filas = []
    for ent in entidades:
        sub = df[df["entity_normalized"] == ent].sort_values("mes")
        canon = sub["entity_canonical"].iloc[0] if "entity_canonical" in sub.columns else ent
        n_meses = sub["mes"].nunique()
        # Valores de diciembre (acumulado año) para flujos
        dic = sub[sub["mes"] == 12]
        row = {
            "entity_normalized": ent,
            "entity_canonical": canon,
            "n_meses_con_dato": n_meses,
            "primas_netas_anual_ves": dic["primas_netas_ves"].sum() if not dic.empty and "primas_netas_ves" in dic.columns else None,
            "siniestros_pagados_anual_ves": dic["siniestros_pagados_ves"].sum() if not dic.empty else None,
            "gastos_operativos_anual_ves": dic["gastos_operativos_ves"].sum() if not dic.empty else None,
        }
        # Reservas: promedio del año (son saldos constituidos/liberados mes a mes)
        for c in CAMPOS_RESERVA:
            if c in sub.columns:
                row[c + "_promedio"] = sub[c].mean()
        filas.append(row)
    return pd.DataFrame(filas)


def serie_mensual_empresa(df: pd.DataFrame, entity_normalized: str) -> pd.DataFrame:
    """Devuelve la tabla mes a mes (1-12) para una empresa con los 8 campos."""
    sub = df[df["entity_normalized"] == entity_normalized].sort_values("mes")
    cols = ["mes", "periodo"] + [c for c in CAMPOS_EXCEL + ["gastos_operativos_ves"] if c in sub.columns]
    return sub[[c for c in cols if c in sub.columns]].copy()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pruebas por empresa sobre base 2023")
    parser.add_argument("--empresa", type=str, default=None, help="Nombre normalizado de empresa para ver serie mensual (ej. caracas c a seguros)")
    parser.add_argument("--listar", action="store_true", help="Listar primeras 20 empresas (entity_normalized)")
    parser.add_argument("--resumen", action="store_true", help="Generar y guardar resumen anual por empresa")
    parser.add_argument("--muestra", type=int, default=3, help="Número de empresas de muestra para imprimir serie (por defecto 3)")
    args = parser.parse_args()

    print("=" * 70)
    print("Pruebas por empresa — base 2023 (empresa, mes, 8 campos)")
    print("=" * 70)

    df = load_base()
    print("\nBase cargada: {} filas | {} entidades | 12 meses".format(
        len(df), df["entity_normalized"].nunique()))

    # Resumen anual siempre lo generamos en memoria para estadísticas
    resumen = resumen_anual_por_empresa(df)
    if args.resumen or not args.empresa and not args.listar:
        STAGED_2023.mkdir(parents=True, exist_ok=True)
        resumen.to_csv(RESUMEN_ANUAL_CSV, index=False, encoding="utf-8-sig")
        print("\n1) Resumen anual guardado: {}".format(RESUMEN_ANUAL_CSV))
        print("   Columnas: entity, n_meses, primas_netas_anual_ves, siniestros_pagados_anual_ves, gastos_operativos_anual_ves, reservas_*_promedio")
        # Totales mercado
        p = resumen["primas_netas_anual_ves"].sum()
        s = resumen["siniestros_pagados_anual_ves"].sum()
        g = resumen["gastos_operativos_anual_ves"].sum()
        print("   Total mercado (suma dic): primas={:.0f} | siniestros={:.0f} | gastos_operativos={:.0f}".format(p or 0, s or 0, g or 0))

    if args.listar:
        print("\n2) Primeras 20 empresas (entity_normalized):")
        for i, ent in enumerate(resumen["entity_normalized"].head(20).tolist(), 1):
            canon = resumen[resumen["entity_normalized"] == ent]["entity_canonical"].iloc[0]
            print("   {:2d}. {}  ->  {}".format(i, ent, canon[:50]))

    if args.empresa:
        ent = args.empresa.strip().lower()
        match = df[df["entity_normalized"].str.lower() == ent]
        if match.empty:
            # Buscar parcial
            match = df[df["entity_normalized"].str.contains(ent, case=False, na=False)]
        if match.empty:
            print("\nEmpresa no encontrada. Usa --listar para ver nombres.")
            return
        ent = match["entity_normalized"].iloc[0]
        tab = serie_mensual_empresa(df, ent)
        print("\n3) Serie mensual — {}".format(match["entity_canonical"].iloc[0]))
        print(tab.to_string(index=False))
        return

    # Por defecto: mostrar serie de N empresas de muestra (las de mayor primas anuales)
    if not args.listar and args.muestra > 0:
        top = resumen.nlargest(args.muestra, "primas_netas_anual_ves")
        print("\n2) Muestra: {} empresas (mayor primas anuales) — serie primas_netas_ves por mes".format(args.muestra))
        for _, r in top.iterrows():
            ent = r["entity_normalized"]
            tab = serie_mensual_empresa(df, ent)
            primas = tab[["mes", "primas_netas_ves"]] if "primas_netas_ves" in tab.columns else tab[["mes"]]
            print("\n   --- {} ---".format(r["entity_canonical"][:50]))
            print(primas.to_string(index=False))

    print("\n" + "=" * 70)
    print("Siguiente paso sugerido:")
    print("  1) Revisar resumen_anual_por_empresa_2023.csv y serie de muestra.")
    print("  2) Pasar base a capa CLEAN (data/clean/2023/) con esquema fijo para carga a Supabase.")
    print("  3) Cargar entidades y primas/métricas 2023 a Supabase.")
    print("  4) Conectar dashboard para visualizar 2023.")
    print("=" * 70)


if __name__ == "__main__":
    main()
