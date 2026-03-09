"""
Verifica consistencia de datos por compañía y año en la ventana 2014-2024.
- Tabla por compañía y año: cuántos de los 20 campos objetivo tienen valor.
- Detecta inconsistencias (duplicados, valores contradictorios).
- Genera reportes para repetir normalizado/vaciado hasta lograr data consistente.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from config.anuarios_paths import (
    SEGURO_EN_CIFRAS_INDICE,
    SEGURO_EN_CIFRAS_VARIABLES,
    SEGURO_EN_CIFRAS_VACIADO,
    SEGURO_EN_CIFRAS_ENTIDADES,
)
from config.anuarios_paths import ensure_anuarios_dirs

# Ventana
ANO_INICIO = 2014
ANO_FIN = 2024

# Mínimo de campos con serie histórica consistente por compañía
MIN_CAMPOS_OBJETIVO = 20

CANONICO_CSV = SEGURO_EN_CIFRAS_VARIABLES / "canonico.csv"
MATRIZ_BASE_MADRE_CSV = SEGURO_EN_CIFRAS_VACIADO / "matriz_base_madre_2014_2024.csv"
METRICAS_CSV = SEGURO_EN_CIFRAS_VACIADO / "anuario_metricas.csv"
BASE_MADRE_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "base_madre_entidades_2014_2024.csv"

# Salidas
TABLA_CONSISTENCIA_CSV = SEGURO_EN_CIFRAS_INDICE / "verificacion_tabla_compania_anio_campos.csv"
RESUMEN_CONSISTENCIA_CSV = SEGURO_EN_CIFRAS_INDICE / "verificacion_resumen_consistencia_ventana.csv"
INCONSISTENCIAS_CSV = SEGURO_EN_CIFRAS_INDICE / "verificacion_inconsistencias_ventana.csv"
README_CONSISTENCIA = SEGURO_EN_CIFRAS_INDICE / "README_CONSISTENCIA_VENTANA.md"


def get_campos_objetivo() -> list[str]:
    """Lista de hasta 20+ metric_name canónicos para verificar consistencia."""
    if not CANONICO_CSV.exists():
        return [
            "primas_netas_cobradas", "primas_netas_por_ramo", "siniestros_pagados",
            "reservas_tecnicas", "reservas_primas", "reservas_siniestros_pendientes",
            "gastos_administracion", "gastos_produccion", "capital_garantia", "capital_pagado",
            "garantia_deposito", "resultados_economicos", "inversiones_reservas",
            "comisiones_gastos_adquisicion", "empresas_autorizadas", "patrimonio_suficiencia",
            "ingresos_netos", "gastos_operativos", "balance_condensado", "activo_total", "pasivo_total",
        ]
    df = pd.read_csv(CANONICO_CSV)
    return df["metric_name"].dropna().unique().tolist()[:25]


def run_verificacion() -> dict:
    """Ejecuta verificación por compañía y año; devuelve resumen."""
    ensure_anuarios_dirs()
    SEGURO_EN_CIFRAS_INDICE.mkdir(parents=True, exist_ok=True)

    campos_objetivo = get_campos_objetivo()
    # Limitar a los primeros 20 para el criterio "al menos 20 campos"
    campos_20 = campos_objetivo[:MIN_CAMPOS_OBJETIVO]

    resultado = {
        "campos_objetivo": len(campos_20),
        "campos_con_datos_en_matriz": 0,
        "filas_ok_20_campos": 0,
        "filas_totales": 0,
        "companias_ok": 0,
        "companias_con_inconsistencias": 0,
        "duplicados_metricas": 0,
    }

    if not MATRIZ_BASE_MADRE_CSV.exists():
        print("No existe matriz base madre:", MATRIZ_BASE_MADRE_CSV)
        print("Ejecutar primero: python scripts/anuarios_base_madre_2014_2024.py")
        _write_readme_consistencia(campos_20, resultado, [])
        return resultado

    matriz = pd.read_csv(MATRIZ_BASE_MADRE_CSV, low_memory=False)
    # Filtrar ventana
    matriz = matriz[(matriz["anio"] >= ANO_INICIO) & (matriz["anio"] <= ANO_FIN)]

    id_cols = ["nombre_normalizado_madre", "anio", "canonical_name", "entity_name_en_anio"]
    metric_cols = [c for c in matriz.columns if c not in id_cols and c != "entity_normalized_name"]
    # Campos objetivo que existen en la matriz
    campos_en_matriz = [c for c in campos_20 if c in matriz.columns]
    resultado["campos_con_datos_en_matriz"] = len(campos_en_matriz)

    # Tabla por compañía y año: para cada campo objetivo, 1 si tiene valor, 0 si no
    tabla = matriz[["nombre_normalizado_madre", "anio"]].copy()
    if "canonical_name" in matriz.columns:
        tabla["canonical_name"] = matriz["canonical_name"]
    for c in campos_20:
        if c in matriz.columns:
            tabla[f"_{c}"] = matriz[c].notna().astype(int)
        else:
            tabla[f"_{c}"] = 0
    cols_indicador = [f"_{c}" for c in campos_20 if f"_{c}" in tabla.columns]
    tabla["n_campos_llenos"] = tabla[cols_indicador].sum(axis=1)
    tabla["ok_20_campos"] = (tabla["n_campos_llenos"] >= MIN_CAMPOS_OBJETIVO).astype(int)
    tabla["ok_10_campos"] = (tabla["n_campos_llenos"] >= 10).astype(int)
    tabla["ok_8_campos"] = (tabla["n_campos_llenos"] >= 8).astype(int)
    def _faltantes(row):
        return ", ".join(c for c in campos_20 if (f"_{c}" in row.index and row.get(f"_{c}", 0) == 0))
    tabla["campos_faltantes"] = tabla.apply(_faltantes, axis=1)
    resultado["filas_totales"] = len(tabla)
    resultado["filas_ok_20_campos"] = int(tabla["ok_20_campos"].sum())
    resultado["filas_ok_10_campos"] = int(tabla["ok_10_campos"].sum())
    resultado["filas_ok_8_campos"] = int(tabla["ok_8_campos"].sum())

    # Filtrar solo empresas probables para metricas de consistencia
    madres_empresa = None
    if BASE_MADRE_CSV.exists():
        bm = pd.read_csv(BASE_MADRE_CSV)
        if "es_empresa_probable" in bm.columns:
            madres_empresa = set(bm[bm["es_empresa_probable"]]["nombre_normalizado_madre"].dropna().unique())
    tabla_emp = tabla[tabla["nombre_normalizado_madre"].isin(madres_empresa)] if madres_empresa else pd.DataFrame()
    if tabla_emp.empty and madres_empresa is None:
        tabla_emp = tabla
    elif tabla_emp.empty:
        tabla_emp = tabla

    resultado["filas_empresas_probables"] = len(tabla_emp)
    resultado["filas_ok_20_campos_empresas_probables"] = int(tabla_emp["ok_20_campos"].sum()) if not tabla_emp.empty else 0
    resultado["filas_ok_10_campos_empresas_probables"] = int(tabla_emp["ok_10_campos"].sum()) if not tabla_emp.empty else 0
    resultado["filas_ok_8_campos_empresas_probables"] = int(tabla_emp["ok_8_campos"].sum()) if not tabla_emp.empty else 0

    companias_por_madre = tabla.groupby("nombre_normalizado_madre").agg(
        n_anios=("anio", "nunique"),
        n_filas_ok=("ok_20_campos", "sum"),
    ).reset_index()
    companias_por_madre["todos_anios_ok"] = companias_por_madre["n_filas_ok"] == companias_por_madre["n_anios"]
    resultado["companias_ok"] = int(companias_por_madre["todos_anios_ok"].sum())
    resultado["companias_con_inconsistencias"] = int((~companias_por_madre["todos_anios_ok"]).sum())

    if not tabla_emp.empty and madres_empresa:
        comp_emp = tabla_emp.groupby("nombre_normalizado_madre").agg(
            n_anios=("anio", "nunique"),
            n_filas_ok=("ok_20_campos", "sum"),
        ).reset_index()
        comp_emp["todos_anios_ok"] = comp_emp["n_filas_ok"] == comp_emp["n_anios"]
        resultado["companias_ok_empresas_probables"] = int(comp_emp["todos_anios_ok"].sum())
    else:
        resultado["companias_ok_empresas_probables"] = resultado["companias_ok"]

    # Guardar tabla compañía x año x indicador de campos (todas y solo empresas probables)
    tabla.to_csv(TABLA_CONSISTENCIA_CSV, index=False, encoding="utf-8-sig")
    print("Tabla compania x ano x campos guardada:", TABLA_CONSISTENCIA_CSV)
    if not tabla_emp.empty and len(tabla_emp) < len(tabla):
        path_emp = SEGURO_EN_CIFRAS_INDICE / "verificacion_tabla_compania_anio_campos_empresas_probables.csv"
        tabla_emp.to_csv(path_emp, index=False, encoding="utf-8-sig")
        print("Tabla solo empresas probables:", path_emp)

    # Resumen por compañía
    resumen = companias_por_madre.merge(
        tabla.groupby("nombre_normalizado_madre")["n_campos_llenos"].mean().reset_index().rename(
            columns={"n_campos_llenos": "promedio_campos_llenos"}
        ),
        on="nombre_normalizado_madre",
        how="left",
    )
    if BASE_MADRE_CSV.exists():
        bm = pd.read_csv(BASE_MADRE_CSV)
        if "canonical_name_representativo" in bm.columns:
            bm = bm[["nombre_normalizado_madre", "canonical_name_representativo", "es_empresa_probable"]]
            resumen = resumen.merge(bm, on="nombre_normalizado_madre", how="left")
    resumen.to_csv(RESUMEN_CONSISTENCIA_CSV, index=False, encoding="utf-8-sig")
    print("Resumen consistencia guardado:", RESUMEN_CONSISTENCIA_CSV)

    # Inconsistencias: duplicados en anuario_metricas (mismo entity, año, metric_name con distinto value)
    filas_inconsistencia = []
    if METRICAS_CSV.exists():
        met = pd.read_csv(METRICAS_CSV, low_memory=False)
        met = met[(met["anio"] >= ANO_INICIO) & (met["anio"] <= ANO_FIN)]
        dup = met.groupby(["anio", "entity_name", "metric_name"])["value"].agg(["count", "nunique"]).reset_index()
        dup = dup[(dup["count"] > 1) & (dup["nunique"] > 1)]
        resultado["duplicados_metricas"] = len(dup)
        for _, r in dup.iterrows():
            sub = met[(met["anio"] == r["anio"]) & (met["entity_name"] == r["entity_name"]) & (met["metric_name"] == r["metric_name"])]
            filas_inconsistencia.append({
                "anio": r["anio"],
                "entity_name": r["entity_name"],
                "metric_name": r["metric_name"],
                "cantidad_registros": int(r["count"]),
                "valores_distintos": int(r["nunique"]),
                "ejemplo_valores": sub["value"].dropna().head(3).tolist(),
            })
    if filas_inconsistencia:
        pd.DataFrame(filas_inconsistencia).to_csv(INCONSISTENCIAS_CSV, index=False, encoding="utf-8-sig")
        print("Inconsistencias (duplicados con valores distintos) guardadas:", INCONSISTENCIAS_CSV)

    _write_readme_consistencia(campos_20, resultado, filas_inconsistencia)
    _print_resumen(campos_20, resultado)
    return resultado


def _write_readme_consistencia(campos_20: list, resultado: dict, inconsistencias: list) -> None:
    with open(README_CONSISTENCIA, "w", encoding="utf-8") as f:
        f.write("# Verificación de consistencia – ventana 2014-2024\n\n")
        f.write("Objetivo: **al menos 20 campos** con serie histórica consistente por compañía.\n\n")
        f.write("## Campos objetivo (20)\n\n")
        for c in campos_20:
            f.write(f"- `{c}`\n")
        f.write("\n## Resultado último chequeo\n\n")
        f.write(f"- Filas (companía, año) en matriz: **{resultado.get('filas_totales', 0)}**\n")
        f.write(f"- Filas con ≥20 campos llenos: **{resultado.get('filas_ok_20_campos', 0)}**\n")
        f.write(f"- Campos objetivo presentes en matriz: **{resultado.get('campos_con_datos_en_matriz', 0)}**\n")
        f.write(f"- Duplicados con valores distintos: **{resultado.get('duplicados_metricas', 0)}**\n\n")
        f.write("## Si la data no es consistente\n\n")
        f.write("1. Revisar extracción en `by_source`: que cada anuario PDF/Excel tenga tablas alineadas con **variables/indice_cuadros.csv**.\n")
        f.write("2. Re-ejecutar vaciado: `python scripts/anuarios_vaciado_secuencial.py` (o el script que llame a `run_vaciado_secuencial()`).\n")
        f.write("3. Re-ejecutar base madre: `python scripts/anuarios_base_madre_2014_2024.py`.\n")
        f.write("4. Volver a ejecutar esta verificación: `python scripts/anuarios_verificar_consistencia_ventana.py`.\n")
        f.write("5. Repetir hasta que el número de filas con ≥20 campos y el de inconsistencias sea aceptable.\n")


def _print_resumen(campos_20: list, resultado: dict) -> None:
    print("\n" + "=" * 60)
    print("VERIFICACIÓN CONSISTENCIA VENTANA 2014-2024")
    print("=" * 60)
    print("Campos objetivo (primeros 20):", campos_20[:10], "...")
    print("Campos objetivo con datos en matriz:", resultado.get("campos_con_datos_en_matriz", 0), "/", len(campos_20))
    print("Filas (compania, ano) totales:", resultado.get("filas_totales", 0))
    print("Filas con >=20 campos llenos:", resultado.get("filas_ok_20_campos", 0))
    print("Filas con >=10 campos:", resultado.get("filas_ok_10_campos", 0))
    print("Filas con >=8 campos:", resultado.get("filas_ok_8_campos", 0))
    if resultado.get("filas_empresas_probables"):
        print("Filas solo empresas probables:", resultado.get("filas_empresas_probables", 0))
        print("Filas ok (>=20 campos) solo empresas probables:", resultado.get("filas_ok_20_campos_empresas_probables", 0))
        print("Filas ok (>=10 campos) solo empresas probables:", resultado.get("filas_ok_10_campos_empresas_probables", 0))
    print("Companias con todos los anos ok:", resultado.get("companias_ok", 0))
    if resultado.get("companias_ok_empresas_probables") is not None:
        print("Companias ok (solo empresas probables):", resultado.get("companias_ok_empresas_probables", 0))
    print("Duplicados (entity/ano/metrica distintos):", resultado.get("duplicados_metricas", 0))
    if resultado.get("filas_ok_20_campos", 0) < resultado.get("filas_totales", 1) or resultado.get("campos_con_datos_en_matriz", 0) < 20:
        print("\n>>> Recomendacion: alinear extraccion con variables/indice_cuadros.csv y repetir vaciado y normalizacion.")
    print("=" * 60)


def main():
    run_verificacion()
    sys.exit(0)


if __name__ == "__main__":
    main()
