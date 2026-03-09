"""
Verifica Cuadros 23-A, 23-B, 23-C (comisiones por ramo/empresa) y 23-D, 23-E, 23-F (gastos administración por ramo/empresa)
contra Cuadro 23:
- 23-A/B/C: la suma de todas las celdas (o columna TOTAL de la última página) debe coincidir con la columna
  COMISIONES_GASTOS_ADQUISICION del Cuadro 23 para SEGURO DE PERSONAS, SEGUROS PATRIMONIALES y SEGUROS OBLIGACIONALES.
- 23-D/E/F: la suma debe coincidir con la columna GASTOS_ADMINISTRACION del Cuadro 23 para los mismos tres segmentos.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 50.0  # redondeos en miles


def _sumar_todo_menos_nombre(df):
    """Suma todas las columnas numéricas (excl. Nombre Empresa)."""
    cols = [c for c in df.columns if c != "Nombre Empresa"]
    return sum(df[c].sum() for c in cols)


def _sumar_columna_total(df):
    """Suma la columna TOTAL si existe."""
    if "TOTAL" not in df.columns:
        return None
    return float(df["TOTAL"].sum())


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path_c23 = carpeta / "cuadro_23_gastos_produccion_vs_primas_por_ramo.csv"
    if not path_c23.exists():
        print("[ERROR] No existe {}.".format(path_c23))
        return False
    df23 = pd.read_csv(path_c23, sep=SEP, encoding=ENCODING)

    # Valores esperados del Cuadro 23 (por fila: RAMO_DE_SEGUROS)
    def _valor_c23(rama_substr: str, col: str) -> float | None:
        col = col.upper()
        if col == "COMISIONES":
            col = "COMISIONES_GASTOS_ADQUISICION"
        elif col == "GASTOS_ADM":
            col = "GASTOS_ADMINISTRACION"
        for _, r in df23.iterrows():
            ramo = str(r["RAMO_DE_SEGUROS"]).strip().upper()
            if rama_substr.upper() in ramo:
                return float(r[col])
        return None

    esperado = {
        "23A_comisiones": _valor_c23("SEGURO DE PERSONAS", "COMISIONES"),
        "23B_comisiones": _valor_c23("SEGUROS PATRIMONIALES", "COMISIONES"),
        "23C_comisiones": _valor_c23("SEGUROS OBLIGACIONALES", "COMISIONES"),
        "23D_gastos_adm": _valor_c23("SEGURO DE PERSONAS", "GASTOS_ADM"),
        "23E_gastos_adm": _valor_c23("SEGUROS PATRIMONIALES", "GASTOS_ADM"),
        "23F_gastos_adm": _valor_c23("SEGUROS OBLIGACIONALES", "GASTOS_ADM"),
    }

    # Archivos: último archivo de cada cuadro tiene columna TOTAL
    archivos = [
        ("23-A", ["cuadro_23A_pag64_comisiones_5_ramos.csv", "cuadro_23A_pag65_comisiones_4_ramos_total.csv"], "23A_comisiones"),
        ("23-B", ["cuadro_23B_pag66_comisiones_6_ramos.csv", "cuadro_23B_pag67_comisiones_6_ramos.csv", "cuadro_23B_pag68_comisiones_4_ramos_total.csv"], "23B_comisiones"),
        ("23-C", ["cuadro_23C_pag69_comisiones_5_ramos.csv", "cuadro_23C_pag70_comisiones_3_ramos_total.csv"], "23C_comisiones"),
        ("23-D", ["cuadro_23D_pag71_gastos_adm_5_ramos.csv", "cuadro_23D_pag72_gastos_adm_4_ramos_total.csv"], "23D_gastos_adm"),
        ("23-E", ["cuadro_23E_pag73_gastos_adm_6_ramos.csv", "cuadro_23E_pag74_gastos_adm_6_ramos.csv", "cuadro_23E_pag75_gastos_adm_4_ramos_total.csv"], "23E_gastos_adm"),
        ("23-F", ["cuadro_23F_pag76_gastos_adm_5_ramos.csv", "cuadro_23F_pag77_gastos_adm_3_ramos_total.csv"], "23F_gastos_adm"),
    ]

    todo_ok = True
    print("")
    print("  Cuadros 23-A/B/C (comisiones) y 23-D/E/F (gastos adm) vs Cuadro 23")
    print("")

    for label, nombres, key in archivos:
        paths = [carpeta / n for n in nombres]
        if not all(p.exists() for p in paths):
            print("  [ERROR] Faltan archivos para {}.".format(label))
            todo_ok = False
            continue
        dfs = [pd.read_csv(p, sep=SEP, encoding=ENCODING) for p in paths]
        # Suma: todas las columnas numéricas de todos los archivos, pero sin duplicar (usar col TOTAL del último como referencia)
        suma_total_col = _sumar_columna_total(dfs[-1])
        if suma_total_col is not None:
            suma_usar = suma_total_col
        else:
            suma_usar = sum(_sumar_todo_menos_nombre(d) for d in dfs)
        esperado_val = esperado.get(key)
        if esperado_val is None:
            print("  {}  Esperado no encontrado en C23 para key {}.".format(label, key))
            todo_ok = False
            continue
        diff = abs(suma_usar - esperado_val)
        if diff <= TOLERANCIA:
            print("  {}  Suma = {:,.0f}   C23 = {:,.0f}   OK".format(label, suma_usar, esperado_val))
        else:
            print("  {}  Suma = {:,.0f}   C23 = {:,.0f}   diff = {:,.0f}   FALLO".format(
                label, suma_usar, esperado_val, suma_usar - esperado_val))
            todo_ok = False

    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
