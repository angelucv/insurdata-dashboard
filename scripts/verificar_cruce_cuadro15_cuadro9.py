# scripts/verificar_cruce_cuadro15_cuadro9.py
"""
Verifica el Cuadro 15 (Reservas para prestaciones y siniestros pendientes de pago por ramo, pág 42)
contra el Cuadro 9 (Reservas técnicas):
- TOTAL Cuadro 15 (Retención propia) = Cuadro 9 "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES" (1.028.573).
- Sección SEGURO DE PERSONAS en C15 = suma de subdivisiones en C9: Vida + Individual de Personas + Colectivos de Personas + Funerarios.
- Vida Individual (C15) = Vida (C9).
- Hospitalización Individual + Accidentes Personales Individual (C15) = Individual de Personas (Accidentes Personales - HCM) (C9).
- Vida Colectivo + Accidentes Personales Colectivo + Hospitalización Colectivo (C15) = Colectivos de Personas (Vida - Accidentes Personales - HCM) (C9).
- Funerario (C15) = Funerarios (C9).
- SEGUROS PATRIMONIALES (C15) = Patrimoniales (C9, bajo prestaciones/siniestros pendientes).
- SEGUROS DE RESPONSABILIDAD (C15) = Obligacionales o de Responsabilidad (C9).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 5.0


def _normalizar(s: str) -> str:
    return s.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def _valor_cuadro9(df9, concepto: str, despues_de: str | None = None) -> float | None:
    """Devuelve MONTO del concepto en Cuadro 9. Si despues_de se indica, busca la primera ocurrencia después de esa fila."""
    col = df9["CONCEPTO"].astype(str).str.strip()
    n = _normalizar(concepto.strip())
    start = 0
    if despues_de:
        nd = _normalizar(despues_de)
        for i in range(len(df9)):
            if _normalizar(col.iloc[i]) == nd:
                start = i + 1
                break
    for i in range(start, len(df9)):
        if _normalizar(col.iloc[i]) == n:
            return float(df9["MONTO"].iloc[i])
    return None


def _valor_cuadro15_ramo(df15, ramo: str, col: str = "RETENCION_PROPIA") -> float | None:
    """Devuelve el valor de la columna para el ramo en Cuadro 15."""
    r = df15["RAMO_DE_SEGUROS"].astype(str).str.strip()
    n = _normalizar(ramo.strip())
    for i in range(len(df15)):
        if _normalizar(r.iloc[i]) == n:
            return float(df15[col].iloc[i])
    return None


def _suma_ramos_c15(df15, ramos: list[str], col: str = "RETENCION_PROPIA") -> float:
    s = 0.0
    for ramo in ramos:
        v = _valor_cuadro15_ramo(df15, ramo, col)
        if v is not None:
            s += v
    return s


def run_verificacion(anio: int = 2023) -> bool:
    """Compara Cuadro 15 con Cuadro 9 (totales y agrupaciones Personas)."""
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path9 = carpeta / "cuadro_09_reservas_tecnicas.csv"
    path15 = carpeta / "cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv"
    if not path9.exists() or not path15.exists():
        print("[ERROR] Faltan cuadro_09 o cuadro_15 en {}.".format(carpeta))
        return False
    df9 = pd.read_csv(path9, sep=SEP, encoding=ENCODING)
    df15 = pd.read_csv(path15, sep=SEP, encoding=ENCODING)
    todo_ok = True
    print("")
    print("  Cuadro 15 vs Cuadro 9 – Reservas prestaciones y siniestros pendientes por ramo")
    print("")

    # Total C15 (Retención) = C9 "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES" (primera ocurrencia)
    total_c9 = _valor_cuadro9(df9, "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES")
    total_c15 = _valor_cuadro15_ramo(df15, "TOTAL", "RETENCION_PROPIA")
    if total_c9 is not None and total_c15 is not None:
        if abs(total_c15 - total_c9) <= TOLERANCIA:
            print("  TOTAL (Retencion) C15 = C9 'RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES'  OK ({:,.0f})".format(total_c9))
        else:
            print("  TOTAL C15 Retencion {:,.0f} vs C9 {:,.0f}  NO COINCIDE".format(total_c15, total_c9))
            todo_ok = False
    else:
        print("  [AVISO] No se encontro total en C9 o C15.")
        todo_ok = False

    # Vida Individual (C15) = Vida (C9)
    v_c9 = _valor_cuadro9(df9, "Vida", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES")
    v_c15 = _valor_cuadro15_ramo(df15, "Vida Individual")
    if v_c9 is not None and v_c15 is not None and abs(v_c15 - v_c9) <= TOLERANCIA:
        print("  Vida Individual (C15) = Vida (C9)  OK ({:,.0f})".format(v_c9))
    elif v_c9 is not None and v_c15 is not None:
        print("  Vida C15 {:,.0f} vs C9 {:,.0f}  NO COINCIDE".format(v_c15, v_c9))
        todo_ok = False

    # Individual de Personas (C9) = Hospitalización Individual + Accidentes Personales Individual (C15)
    v_c9 = _valor_cuadro9(df9, "Individual de Personas (Accidentes Personales - HCM)", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES")
    v_c15 = _suma_ramos_c15(df15, ["Hospitalización Individual", "Accidentes Personales Individual"])
    if v_c9 is not None and v_c15 is not None and abs(v_c15 - v_c9) <= TOLERANCIA:
        print("  Hospitalizacion Ind. + Accidentes Pers. Ind. (C15) = Individual de Personas (C9)  OK ({:,.0f})".format(v_c9))
    elif v_c9 is not None and v_c15 is not None:
        print("  Individual Personas C15 suma {:,.0f} vs C9 {:,.0f}  NO COINCIDE".format(v_c15, v_c9))
        todo_ok = False

    # Colectivos de Personas (C9) = Vida Colectivo + Accidentes Pers. Colectivo + Hospitalización Colectivo (C15)
    v_c9 = _valor_cuadro9(df9, "Colectivos de Personas (Vida - Accidentes Personales - HCM)", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES")
    v_c15 = _suma_ramos_c15(df15, ["Vida Colectivo", "Accidentes Personales Colectivo", "Hospitalización Colectivo"])
    if v_c9 is not None and v_c15 is not None and abs(v_c15 - v_c9) <= TOLERANCIA:
        print("  Vida Col. + Accid. Col. + Hosp. Col. (C15) = Colectivos de Personas (C9)  OK ({:,.0f})".format(v_c9))
    elif v_c9 is not None and v_c15 is not None:
        print("  Colectivos Personas C15 suma {:,.0f} vs C9 {:,.0f}  NO COINCIDE".format(v_c15, v_c9))
        todo_ok = False

    # Funerario (C15) = Funerarios (C9)
    v_c9 = _valor_cuadro9(df9, "Funerarios", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES")
    v_c15 = _valor_cuadro15_ramo(df15, "Funerario")
    if v_c9 is not None and v_c15 is not None and abs(v_c15 - v_c9) <= TOLERANCIA:
        print("  Funerario (C15) = Funerarios (C9)  OK ({:,.0f})".format(v_c9))
    elif v_c9 is not None and v_c15 is not None:
        print("  Funerarios C15 {:,.0f} vs C9 {:,.0f}  NO COINCIDE".format(v_c15, v_c9))
        todo_ok = False

    # SEGURO DE PERSONAS (C15) = Vida + Individual + Colectivos + Funerarios (C9)
    v_c9 = (_valor_cuadro9(df9, "Vida", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES") or 0) + \
           (_valor_cuadro9(df9, "Individual de Personas (Accidentes Personales - HCM)", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES") or 0) + \
           (_valor_cuadro9(df9, "Colectivos de Personas (Vida - Accidentes Personales - HCM)", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES") or 0) + \
           (_valor_cuadro9(df9, "Funerarios", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES") or 0)
    v_c15 = _valor_cuadro15_ramo(df15, "SEGURO DE PERSONAS")
    if v_c15 is not None and abs(v_c15 - v_c9) <= TOLERANCIA:
        print("  SEGURO DE PERSONAS (C15) = Vida+Individual+Colectivos+Funerarios (C9)  OK ({:,.0f})".format(v_c15))
    elif v_c15 is not None:
        print("  SEGURO DE PERSONAS C15 {:,.0f} vs C9 suma {:,.0f}  NO COINCIDE".format(v_c15, v_c9))
        todo_ok = False

    # SEGUROS PATRIMONIALES (C15) = Patrimoniales (C9, bajo prestaciones)
    v_c9 = _valor_cuadro9(df9, "Patrimoniales", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES")
    v_c15 = _valor_cuadro15_ramo(df15, "SEGUROS PATRIMONIALES")
    if v_c9 is not None and v_c15 is not None and abs(v_c15 - v_c9) <= TOLERANCIA:
        print("  SEGUROS PATRIMONIALES (C15) = Patrimoniales (C9)  OK ({:,.0f})".format(v_c9))
    elif v_c9 is not None and v_c15 is not None:
        print("  Patrimoniales C15 {:,.0f} vs C9 {:,.0f}  NO COINCIDE".format(v_c15, v_c9))
        todo_ok = False

    # SEGUROS DE RESPONSABILIDAD (C15) = Obligacionales (C9)
    v_c9 = _valor_cuadro9(df9, "Obligacionales o de Responsabilidad", "RESERVAS PARA PRESTACIONES Y SINIESTROS PENDIENTES")
    v_c15 = _valor_cuadro15_ramo(df15, "SEGUROS DE RESPONSABILIDAD")
    if v_c9 is not None and v_c15 is not None and abs(v_c15 - v_c9) <= TOLERANCIA:
        print("  SEGUROS DE RESPONSABILIDAD (C15) = Obligacionales (C9)  OK ({:,.0f})".format(v_c9))
    elif v_c9 is not None and v_c15 is not None:
        print("  Obligacionales C15 {:,.0f} vs C9 {:,.0f}  NO COINCIDE".format(v_c15, v_c9))
        todo_ok = False

    print("")
    if todo_ok:
        print("  Resultado: COINCIDE.")
    else:
        print("  Resultado: HAY DISCREPANCIAS.")
    print("")
    return todo_ok


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar Cuadro 15 vs Cuadro 9 (reservas prestaciones/siniestros pendientes)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
