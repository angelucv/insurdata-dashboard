"""
Verifica Cuadro 25-B (Estado de Ganancias y Pérdidas - Egresos) contra:

1) Cuadro 6 (Siniestros pagados por ramo):
   - 25-B Personas: Prestaciones Pagadas + Siniestros Pagados = C6 SEGURO DE PERSONAS (TOTAL).
   - 25-B Generales: Siniestros Pagados = C6 SEGUROS PATRIMONIALES + OBLIGACIONALES (TOTAL).

2) Cuadro 23 (Gastos de producción vs primas por ramo):
   - 25-B Comisiones y Gastos de Adquisición (Personas) = C23 COMISIONES_GASTOS_ADQUISICION fila SEGURO DE PERSONAS.
   - 25-B Gastos de Administración (Personas) = C23 GASTOS_ADMINISTRACION fila SEGURO DE PERSONAS.
   - 25-B Comisiones (Generales) = C23 COMISIONES Patr. + Oblig.
   - 25-B Gastos Adm (Generales) = C23 GASTOS_ADM Patr. + Oblig.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 50.0


def _normalizar(s: str) -> str:
    return s.upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def _valor_c(df, col_rama: str, rama_substr: str, col_val: str) -> float:
    for _, r in df.iterrows():
        if rama_substr.upper() in _normalizar(str(r[col_rama])):
            return float(r[col_val])
    return 0.0


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path_25b = carpeta / "cuadro_25B_estado_ganancias_perdidas_egresos.csv"
    path_c6 = carpeta / "cuadro_06_siniestros_pagados_por_ramo.csv"
    path_c23 = carpeta / "cuadro_23_gastos_produccion_vs_primas_por_ramo.csv"
    for p in (path_25b, path_c6, path_c23):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df25 = pd.read_csv(path_25b, sep=SEP, encoding=ENCODING)
    df6 = pd.read_csv(path_c6, sep=SEP, encoding=ENCODING)
    df23 = pd.read_csv(path_c23, sep=SEP, encoding=ENCODING)

    # Extraer de 25-B valores por sección (primera = Personas, segunda = Generales)
    def _lineas_por_seccion(df):
        secciones = []
        i = 0
        while i < len(df):
            r = df.iloc[i]
            if str(r["TIPO"]) == "SECCION":
                nombre = str(r["CONCEPTO"])
                lineas = []
                j = i + 1
                while j < len(df) and str(df.iloc[j]["TIPO"]) == "LINEA":
                    lineas.append(df.iloc[j])
                    j += 1
                secciones.append((nombre, lineas))
                i = j
            else:
                i += 1
        return secciones

    bloques = _lineas_por_seccion(df25)
    def _buscar_en_lineas(lineas, substr):
        for row in lineas:
            concepto = str(row.iloc[0]) if hasattr(row, "iloc") else str(row.get("CONCEPTO", row[0]))
            monto = float(row.iloc[1]) if hasattr(row, "iloc") else float(row.get("MONTO", row[1]))
            if substr.upper() in _normalizar(concepto):
                return monto
        return None
    def _sumar_en_lineas(lineas, *substrs):
        s = 0.0
        for row in lineas:
            concepto = str(row.iloc[0]) if hasattr(row, "iloc") else str(row.get("CONCEPTO", row[0]))
            monto = float(row.iloc[1]) if hasattr(row, "iloc") else float(row.get("MONTO", row[1]))
            c = _normalizar(concepto)
            for sub in substrs:
                if sub.upper() in c:
                    s += monto
                    break
        return s

    todo_ok = True
    print("")
    print("  Cuadro 25-B (Egresos) vs Cuadro 6 (Siniestros) y Cuadro 23 (Comisiones / Gastos Adm)")
    print("")

    if len(bloques) >= 1:
        _, lineas_personas = bloques[0]
        prest_pag = _buscar_en_lineas(lineas_personas, "Prestaciones Pagadas")
        sin_pag_p = _buscar_en_lineas(lineas_personas, "Siniestros Pagados")
        if prest_pag is not None and sin_pag_p is not None:
            total_personas_25b = prest_pag + sin_pag_p
        else:
            total_personas_25b = _sumar_en_lineas(lineas_personas, "Prestaciones", "Siniestros Pagados")
        total_personas_c6 = _valor_c(df6, df6.columns[0], "SEGURO DE PERSONAS", df6.columns[3])  # TOTAL
        if abs(total_personas_25b - total_personas_c6) <= TOLERANCIA:
            print("  OK  Siniestros/Prestaciones Personas: 25-B = {:,.0f}   C6 TOTAL Personas = {:,.0f}".format(
                total_personas_25b, total_personas_c6))
        else:
            print("  FALLO  Siniestros Personas: 25-B = {:,.0f}   C6 = {:,.0f}   diff = {:,.0f}".format(
                total_personas_25b, total_personas_c6, total_personas_25b - total_personas_c6))
            todo_ok = False

        comis_p = _buscar_en_lineas(lineas_personas, "Comisiones y Gastos") or _buscar_en_lineas(lineas_personas, "Comisiones")
        gastos_adm_p = _buscar_en_lineas(lineas_personas, "Gastos de Administración") or _buscar_en_lineas(lineas_personas, "Gastos de Admin")
        c23_comis_p = _valor_c(df23, "RAMO_DE_SEGUROS", "SEGURO DE PERSONAS", "COMISIONES_GASTOS_ADQUISICION")
        c23_gastos_p = _valor_c(df23, "RAMO_DE_SEGUROS", "SEGURO DE PERSONAS", "GASTOS_ADMINISTRACION")
        if comis_p is not None and abs(comis_p - c23_comis_p) <= TOLERANCIA:
            print("  OK  Comisiones Personas: 25-B = {:,.0f}   C23 = {:,.0f}".format(comis_p, c23_comis_p))
        else:
            print("  FALLO  Comisiones Personas: 25-B = {}   C23 = {:,.0f}".format(comis_p, c23_comis_p))
            todo_ok = False
        if gastos_adm_p is not None and abs(gastos_adm_p - c23_gastos_p) <= TOLERANCIA:
            print("  OK  Gastos Adm Personas: 25-B = {:,.0f}   C23 = {:,.0f}".format(gastos_adm_p, c23_gastos_p))
        else:
            print("  FALLO  Gastos Adm Personas: 25-B = {}   C23 = {:,.0f}".format(gastos_adm_p, c23_gastos_p))
            todo_ok = False

    if len(bloques) >= 2:
        _, lineas_generales = bloques[1]
        sin_pag_g = _buscar_en_lineas(lineas_generales, "Siniestros Pagados")
        total_patr_c6 = _valor_c(df6, df6.columns[0], "SEGUROS PATRIMONIALES", df6.columns[3])
        total_obl_c6 = _valor_c(df6, df6.columns[0], "OBLIGACIONALES", df6.columns[3])
        if total_obl_c6 == 0:
            total_obl_c6 = _valor_c(df6, df6.columns[0], "RESPONSABILIDAD", df6.columns[3])
        total_gen_c6 = total_patr_c6 + total_obl_c6
        if sin_pag_g is not None and abs(sin_pag_g - total_gen_c6) <= TOLERANCIA:
            print("  OK  Siniestros Generales: 25-B = {:,.0f}   C6 Patr.+Oblig. = {:,.0f}".format(sin_pag_g, total_gen_c6))
        else:
            print("  FALLO  Siniestros Generales: 25-B = {}   C6 = {:,.0f}   diff = {:,.0f}".format(
                sin_pag_g, total_gen_c6, (sin_pag_g or 0) - total_gen_c6))
            todo_ok = False

        comis_g = _buscar_en_lineas(lineas_generales, "Comisiones y Gastos") or _buscar_en_lineas(lineas_generales, "Comisiones")
        gastos_adm_g = _buscar_en_lineas(lineas_generales, "Gastos de Administración") or _buscar_en_lineas(lineas_generales, "Gastos de Admin")
        c23_comis_patr = _valor_c(df23, "RAMO_DE_SEGUROS", "SEGUROS PATRIMONIALES", "COMISIONES_GASTOS_ADQUISICION")
        c23_comis_obl = _valor_c(df23, "RAMO_DE_SEGUROS", "SEGUROS OBLIGACIONALES", "COMISIONES_GASTOS_ADQUISICION")
        if c23_comis_obl == 0:
            c23_comis_obl = _valor_c(df23, "RAMO_DE_SEGUROS", "RESPONSABILIDAD", "COMISIONES_GASTOS_ADQUISICION")
        c23_gastos_patr = _valor_c(df23, "RAMO_DE_SEGUROS", "SEGUROS PATRIMONIALES", "GASTOS_ADMINISTRACION")
        c23_gastos_obl = _valor_c(df23, "RAMO_DE_SEGUROS", "SEGUROS OBLIGACIONALES", "GASTOS_ADMINISTRACION")
        if c23_gastos_obl == 0:
            c23_gastos_obl = _valor_c(df23, "RAMO_DE_SEGUROS", "RESPONSABILIDAD", "GASTOS_ADMINISTRACION")
        if comis_g is not None and abs(comis_g - (c23_comis_patr + c23_comis_obl)) <= TOLERANCIA:
            print("  OK  Comisiones Generales: 25-B = {:,.0f}   C23 Patr.+Oblig. = {:,.0f}".format(
                comis_g, c23_comis_patr + c23_comis_obl))
        else:
            print("  FALLO  Comisiones Generales: 25-B = {}   C23 = {:,.0f}".format(
                comis_g, c23_comis_patr + c23_comis_obl))
            todo_ok = False
        if gastos_adm_g is not None and abs(gastos_adm_g - (c23_gastos_patr + c23_gastos_obl)) <= TOLERANCIA:
            print("  OK  Gastos Adm Generales: 25-B = {:,.0f}   C23 Patr.+Oblig. = {:,.0f}".format(
                gastos_adm_g, c23_gastos_patr + c23_gastos_obl))
        else:
            print("  FALLO  Gastos Adm Generales: 25-B = {}   C23 = {:,.0f}".format(
                gastos_adm_g, c23_gastos_patr + c23_gastos_obl))
            todo_ok = False

    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
