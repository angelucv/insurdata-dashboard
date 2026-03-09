"""
Verifica Cuadro 25-A (Estado de Ganancias y Pérdidas - Ingresos) contra Cuadro 3 (Primas por ramo):

1) Primas Aceptadas (Reaseguro): deben coincidir con REASEGURO ACEPTADO del Cuadro 3.
   - "Primas Aceptadas Seguros de Personas" (25-A) = suma REASEGURO ACEPTADO ramos Personas en C3.
   - "Primas Aceptadas Seguros Generales" (25-A) = suma REASEGURO ACEPTADO ramos Patrimoniales en C3.

2) Primas del Ejercicio: relación con Cuadro 3 (SEGURO DIRECTO o TOTAL por segmento).
   - Pueden existir diferencias por criterio (devengado/cobrado, bruto/neto); se reporta comparación con tolerancia.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA_REASEGURO = 10.0   # Primas aceptadas deben coincidir
TOLERANCIA_PRIMAS = 500000.0  # Primas del ejercicio pueden diferir por criterio contable


def _normalizar(s: str) -> str:
    return s.upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path_25a = carpeta / "cuadro_25A_estado_ganancias_perdidas_ingresos.csv"
    path_c3 = carpeta / "cuadro_03_primas_por_ramo.csv"
    for p in (path_25a, path_c3):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df25 = pd.read_csv(path_25a, sep=SEP, encoding=ENCODING)
    df3 = pd.read_csv(path_c3, sep=SEP, encoding=ENCODING)

    # Cuadro 3: ramos por segmento y columna REASEGURO ACEPTADO
    col_ramo = df3.columns[0]
    col_reaseguro = None
    for c in df3.columns:
        if "REASEGURO" in c.upper() and "ACEPTADO" in c.upper():
            col_reaseguro = c
            break
    if col_reaseguro is None:
        col_reaseguro = df3.columns[2] if len(df3.columns) > 2 else None
    col_directo = df3.columns[1] if len(df3.columns) > 1 else None
    col_total = None
    for c in df3.columns:
        if _normalizar(c) == "TOTAL" and c != col_ramo:
            col_total = c
            break
    if col_total is None and len(df3.columns) > 3:
        col_total = df3.columns[3]

    # Índices C3: fila SEGURO DE PERSONAS, SEGUROS PATRIMONIALES, SEGUROS OBLIGACIONALES (o RESPONSABILIDAD)
    def _valor_c3(rama_substr: str, col: str) -> float:
        for i, r in df3.iterrows():
            if rama_substr.upper() in _normalizar(str(r[col_ramo])):
                return float(r[col])
        return 0.0

    reaseguro_personas_c3 = _valor_c3("SEGURO DE PERSONAS", col_reaseguro)
    reaseguro_patrimoniales_c3 = _valor_c3("SEGUROS PATRIMONIALES", col_reaseguro)
    total_personas_c3 = _valor_c3("SEGURO DE PERSONAS", col_total) if col_total else 0.0
    total_patrimoniales_c3 = _valor_c3("SEGUROS PATRIMONIALES", col_total) if col_total else 0.0
    total_general_c3 = _valor_c3("TOTAL", col_total) if col_total else 0.0
    # En C3 no hay fila "SEGUROS OBLIGACIONALES"; obligacionales = TOTAL - Personas - Patrimoniales - Solidarios
    total_solidarios_c3 = _valor_c3("SEGUROS SOLIDARIOS", col_total) if col_total else 0.0
    total_obligacionales_c3 = total_general_c3 - total_personas_c3 - total_patrimoniales_c3 - total_solidarios_c3
    directo_personas_c3 = _valor_c3("SEGURO DE PERSONAS", col_directo) if col_directo else 0.0
    directo_patrimoniales_c3 = _valor_c3("SEGUROS PATRIMONIALES", col_directo) if col_directo else 0.0
    directo_general_c3 = _valor_c3("TOTAL", col_directo) if col_directo else 0.0
    directo_obligacionales_c3 = directo_general_c3 - directo_personas_c3 - directo_patrimoniales_c3

    # 25-A: extraer valores por concepto (hay dos "Primas del Ejercicio" y dos bloques de "Primas Aceptadas")
    def _valor_25a(concepto_substr: str, despues_de: str | None = None) -> float | None:
        encontrado = False
        for _, r in df25.iterrows():
            if despues_de and _normalizar(despues_de) in _normalizar(str(r["CONCEPTO"])):
                encontrado = True
                continue
            if not encontrado and despues_de:
                continue
            if concepto_substr.upper() in _normalizar(str(r["CONCEPTO"])):
                return float(r["MONTO"])
        return None

    primas_ejer_personas = _valor_25a("Primas del Ejercicio")  # primera ocurrencia
    primas_ejer_generales = None
    visto_personas = False
    for _, r in df25.iterrows():
        c = str(r["CONCEPTO"])
        if "OPERACIONES DE SEGUROS GENERALES" in _normalizar(c):
            visto_personas = True
        if visto_personas and "Primas del Ejercicio" in c:
            primas_ejer_generales = float(r["MONTO"])
            break
    primas_aceptadas_personas = _valor_25a("Primas Aceptadas Seguros de Personas")
    primas_aceptadas_generales = _valor_25a("Primas Aceptadas Seguros Generales")

    todo_ok = True
    print("")
    print("  Cuadro 25-A (Estado Ganancias y Pérdidas - Ingresos) vs Cuadro 3 (Primas por ramo)")
    print("")

    # 1) Primas Aceptadas = Reaseguro aceptado C3 (deben coincidir)
    if primas_aceptadas_personas is not None:
        if abs(primas_aceptadas_personas - reaseguro_personas_c3) <= TOLERANCIA_REASEGURO:
            print("  OK  Primas Aceptadas Seguros de Personas (25-A) = {:,.0f}   C3 REASEGURO Personas = {:,.0f}".format(
                primas_aceptadas_personas, reaseguro_personas_c3))
        else:
            print("  FALLO  Primas Aceptadas Personas: 25-A = {:,.0f}   C3 = {:,.0f}   diff = {:,.0f}".format(
                primas_aceptadas_personas, reaseguro_personas_c3, primas_aceptadas_personas - reaseguro_personas_c3))
            todo_ok = False
    if primas_aceptadas_generales is not None:
        if abs(primas_aceptadas_generales - reaseguro_patrimoniales_c3) <= TOLERANCIA_REASEGURO:
            print("  OK  Primas Aceptadas Seguros Generales (25-A) = {:,.0f}   C3 REASEGURO Patrimoniales = {:,.0f}".format(
                primas_aceptadas_generales, reaseguro_patrimoniales_c3))
        else:
            print("  FALLO  Primas Aceptadas Generales: 25-A = {:,.0f}   C3 = {:,.0f}   diff = {:,.0f}".format(
                primas_aceptadas_generales, reaseguro_patrimoniales_c3, primas_aceptadas_generales - reaseguro_patrimoniales_c3))
            todo_ok = False

    # 2) Primas del Ejercicio vs C3 (informativo; pueden diferir por criterio)
    print("")
    if primas_ejer_personas is not None:
        print("  Primas del Ejercicio (Personas)  25-A = {:,.0f}   C3 TOTAL Personas = {:,.0f}   C3 SEGURO DIRECTO = {:,.0f}".format(
            primas_ejer_personas, total_personas_c3, directo_personas_c3))
        if abs(primas_ejer_personas - total_personas_c3) > TOLERANCIA_PRIMAS and abs(primas_ejer_personas - directo_personas_c3) > TOLERANCIA_PRIMAS:
            print("    (Diferencia posible por criterio devengado/cobrado o bruto/neto.)")
    if primas_ejer_generales is not None:
        total_gen_c3 = total_patrimoniales_c3 + total_obligacionales_c3  # Patr. + Oblig. (sin fila sección en C3)
        directo_gen_c3 = directo_patrimoniales_c3 + directo_obligacionales_c3
        print("  Primas del Ejercicio (Generales) 25-A = {:,.0f}   C3 TOTAL Patr.+Oblig. = {:,.0f}   C3 SEG.DIRECTO Patr.+Oblig. = {:,.0f}".format(
            primas_ejer_generales, total_gen_c3, directo_gen_c3))
        if abs(primas_ejer_generales - total_gen_c3) > TOLERANCIA_PRIMAS and abs(primas_ejer_generales - directo_gen_c3) > TOLERANCIA_PRIMAS:
            print("    (Diferencia posible por criterio devengado/cobrado o bruto/neto.)")
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
