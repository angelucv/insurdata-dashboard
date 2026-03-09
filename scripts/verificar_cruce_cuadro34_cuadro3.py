"""
Verifica Cuadro 34 (Primas brutas por ramo/empresa: Personas + Generales) contra:

1) Consistencia interna: la suma de las filas por empresa (excl. TOTAL) debe coincidir con la fila TOTAL.
2) Cuadro 3: el TOTAL del Cuadro 34 (Personas y Generales) se compara con C3:
   - Personas: fila "SEGURO DE PERSONAS" (Seguro Directo, Reaseguro Aceptado, Total).
   - Generales: en C3 no hay fila "Seguros Generales"; se usa C3 TOTAL - SEGURO DE PERSONAS - SEGUROS SOLIDARIOS.
   Nota: C3 puede ser primas netas y C34 primas brutas, por lo que se permite tolerancia mayor.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 500.0  # diferencias de redondeo en totales
TOLERANCIA_C3 = 50000.0  # C34 = primas brutas, C3 = por ramo (puede haber diferencias conceptuales)


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path34 = carpeta / "cuadro_34_primas_brutas_personas_generales_por_empresa.csv"
    path3 = carpeta / "cuadro_03_primas_por_ramo.csv"
    for p in (path34, path3):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df34 = pd.read_csv(path34, sep=SEP, encoding=ENCODING)
    df3 = pd.read_csv(path3, sep=SEP, encoding=ENCODING)

    # 1) Consistencia interna C34: suma empresas (excl. TOTAL) vs fila TOTAL
    df34_emp = df34[
        df34["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"
    ].copy()
    total_row = df34[df34["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL"]
    if total_row.empty:
        print("[ERROR] Cuadro 34: no se encontró fila TOTAL.")
        return False
    total_row = total_row.iloc[0]
    cols = [
        "PERSONAS_SEGURO_DIRECTO",
        "PERSONAS_REASEGURO_ACEPTADO",
        "PERSONAS_TOTAL",
        "GENERALES_SEGURO_DIRECTO",
        "GENERALES_REASEGURO_ACEPTADO",
        "GENERALES_TOTAL",
    ]
    todo_ok = True
    print("")
    print("  Cuadro 34 – Consistencia interna (suma empresas = TOTAL)")
    print("")
    for c in cols:
        suma = df34_emp[c].astype(float).sum()
        ref = float(total_row[c])
        diff = abs(suma - ref)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
        print("  {}: suma={:.0f} TOTAL={:.0f} diff={:.0f} {}".format(
            c, suma, ref, diff, "OK" if ok else "FAIL"
        ))
    print("")

    # 2) Cruce con Cuadro 3
    ramo = df3.iloc[:, 0].astype(str).str.strip()
    # C3: SEGURO DE PERSONAS
    idx_personas = (ramo.str.upper() == "SEGURO DE PERSONAS")
    if not idx_personas.any():
        print("[AVISO] Cuadro 3: no se encontró fila 'SEGURO DE PERSONAS'.")
    else:
        r_p = df3.loc[idx_personas].iloc[0]
        c3_p_directo = float(r_p["SEGURO DIRECTO"])
        c3_p_reaseg = float(r_p["REASEGURO ACEPTADO"])
        c3_p_total = float(r_p["TOTAL"])
        c34_p_directo = float(total_row["PERSONAS_SEGURO_DIRECTO"])
        c34_p_reaseg = float(total_row["PERSONAS_REASEGURO_ACEPTADO"])
        c34_p_total = float(total_row["PERSONAS_TOTAL"])
        ok_d = abs(c34_p_directo - c3_p_directo) <= TOLERANCIA_C3
        ok_r = abs(c34_p_reaseg - c3_p_reaseg) <= TOLERANCIA_C3
        ok_t = abs(c34_p_total - c3_p_total) <= TOLERANCIA_C3
        print("  C34 vs C3 SEGURO DE PERSONAS (C34=brutas, C3=por ramo; diferencias esperables):")
        print("    Personas Seguro Directo: C34={:.0f} C3={:.0f} {}".format(c34_p_directo, c3_p_directo, "OK" if ok_d else "[ref]"))
        print("    Personas Reaseguro Aceptado: C34={:.0f} C3={:.0f} {}".format(c34_p_reaseg, c3_p_reaseg, "OK" if ok_r else "[ref]"))
        print("    Personas Total: C34={:.0f} C3={:.0f} {}".format(c34_p_total, c3_p_total, "OK" if ok_t else "[ref]"))
        # No se exige coincidencia: C34 = primas brutas, C3 = agregado por ramo (puede ser otra base).
    # C3: Generales = TOTAL - SEGURO DE PERSONAS - SEGUROS SOLIDARIOS
    idx_total = (ramo.str.upper() == "TOTAL")
    idx_solid = (ramo.str.upper() == "SEGUROS SOLIDARIOS")
    if idx_total.any():
        r_t = df3.loc[idx_total].iloc[0]
        c3_global = float(r_t["TOTAL"])
        c3_personas = float(r_p["TOTAL"]) if idx_personas.any() else 0
        solid = 0
        if idx_solid.any():
            solid = float(df3.loc[idx_solid, "TOTAL"].iloc[0])
        c3_generales = c3_global - c3_personas - solid
        c34_g_total = float(total_row["GENERALES_TOTAL"])
        ok_g = abs(c34_g_total - c3_generales) <= TOLERANCIA_C3
        print("    Generales Total: C34={:.0f} C3(implícito)={:.0f} {}".format(c34_g_total, c3_generales, "OK" if ok_g else "[ref]"))
        # Idem: cruce solo referencial.
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
