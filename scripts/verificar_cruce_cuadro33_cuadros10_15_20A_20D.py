"""
Verifica Cuadro 33 (Reservas de prima y reservas siniestros pendientes - Hospitalización, Cirugía y Maternidad COLECTIVO por empresa) contra tablas anteriores.

Mismo criterio que Cuadro 32 pero para el ramo COLECTIVO:
- Fila TOTAL C33: primeras 3 columnas (Reservas de Prima) = Cuadro 10 fila "Hospitalización Colectivo".
- Fila TOTAL C33: siguientes 3 columnas (Reservas Siniestros Pendientes) = Cuadro 15 fila "Hospitalización Colectivo".
- Por empresa: col. 1 = Cuadro 20-A pág 48 col. "Hospitalización Colectivo"; col. 4 = Cuadro 20-D pág 55 col. "Hospitalización Colectivo".
(*) No incluye Reservas para Siniestros Ocurridos y No Notificados.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 10.0


def _normalizar(s: str) -> str:
    return (
        s.upper()
        .strip()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
    )


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path33 = carpeta / "cuadro_33_reservas_prima_siniestros_hospitalizacion_colectivo.csv"
    path10 = carpeta / "cuadro_10_reservas_prima_por_ramo.csv"
    path15 = carpeta / "cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv"
    path20a48 = carpeta / "cuadro_20A_pag48_4_ramos_total.csv"
    path20d55 = carpeta / "cuadro_20D_pag55_4_ramos_total.csv"

    for p in (path33, path10, path15, path20a48, path20d55):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False

    df33 = pd.read_csv(path33, sep=SEP, encoding=ENCODING)
    df10 = pd.read_csv(path10, sep=SEP, encoding=ENCODING)
    df15 = pd.read_csv(path15, sep=SEP, encoding=ENCODING)
    df20a = pd.read_csv(path20a48, sep=SEP, encoding=ENCODING)
    df20d = pd.read_csv(path20d55, sep=SEP, encoding=ENCODING)

    todo_ok = True
    print("")
    print("  Cuadro 33 – Cruce con C10, C15 (TOTAL) y 20-A, 20-D (por empresa, Hospitalización Colectivo)")
    print("")

    fila_total = df33[df33["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL"]
    if fila_total.empty:
        print("  [ERROR] No se encontró fila TOTAL en Cuadro 33.")
        return False
    t = fila_total.iloc[0]
    c33_prima_ret = float(t["RESERVAS_PRIMA_RETENCION_PROPIA"])
    c33_prima_ac = float(t["RESERVAS_PRIMA_A_CARGO_REASEGURADORES"])
    c33_prima_tot = float(t["RESERVAS_PRIMA_TOTAL"])
    c33_sin_ret = float(t["RESERVAS_SINIESTROS_RETENCION_PROPIA"])
    c33_sin_ac = float(t["RESERVAS_SINIESTROS_A_CARGO_REASEGURADORES"])
    c33_sin_tot = float(t["RESERVAS_SINIESTROS_TOTAL"])

    ramo_col = df10.columns[0]
    c10_hosp = df10[df10[ramo_col].astype(str).str.upper().str.replace("Á", "A").str.contains("HOSPITALIZACION", na=False) & df10[ramo_col].astype(str).str.upper().str.contains("COLECTIVO", na=False)]
    if c10_hosp.empty:
        c10_hosp = df10[df10[ramo_col].astype(str).str.upper().str.contains("HOSPITAL", na=False) & df10[ramo_col].astype(str).str.upper().str.contains("COLECTIVO", na=False)]
    if not c10_hosp.empty:
        r = c10_hosp.iloc[0]
        c10_ret = float(r["RETENCION_PROPIA"])
        c10_ac = float(r["A_CARGO_REASEGURADORES"])
        c10_tot = float(r["TOTAL"])
        if abs(c33_prima_ret - c10_ret) <= TOLERANCIA and abs(c33_prima_ac - c10_ac) <= TOLERANCIA and abs(c33_prima_tot - c10_tot) <= TOLERANCIA:
            print("  OK  TOTAL C33 (Reservas de Prima) = C10 Hospitalización Colectivo  Ret={:,.0f}  A cargo={:,.0f}  Total={:,.0f}".format(c33_prima_ret, c33_prima_ac, c33_prima_tot))
        else:
            print("  FALLO  TOTAL C33 Prima  Ret={:,.0f}  A cargo={:,.0f}  Total={:,.0f}   C10  Ret={:,.0f}  A cargo={:,.0f}  Total={:,.0f}".format(
                c33_prima_ret, c33_prima_ac, c33_prima_tot, c10_ret, c10_ac, c10_tot))
            todo_ok = False
    else:
        print("  [AVISO] No se encontró ramo Hospitalización Colectivo en C10.")

    ramo15 = df15.columns[0]
    c15_hosp = df15[df15[ramo15].astype(str).str.upper().str.replace("Á", "A").str.contains("HOSPITALIZACION", na=False) & df15[ramo15].astype(str).str.upper().str.contains("COLECTIVO", na=False)]
    if c15_hosp.empty:
        c15_hosp = df15[df15[ramo15].astype(str).str.upper().str.contains("HOSPITAL", na=False) & df15[ramo15].astype(str).str.upper().str.contains("COLECTIVO", na=False)]
    if not c15_hosp.empty:
        r = c15_hosp.iloc[0]
        c15_ret = float(r["RETENCION_PROPIA"])
        c15_ac = float(r["A_CARGO_REASEGURADORES"])
        c15_tot = float(r["TOTAL"])
        if abs(c33_sin_ret - c15_ret) <= TOLERANCIA and abs(c33_sin_ac - c15_ac) <= TOLERANCIA and abs(c33_sin_tot - c15_tot) <= TOLERANCIA:
            print("  OK  TOTAL C33 (Reservas Siniestros Pendientes) = C15 Hospitalización Colectivo  Ret={:,.0f}  A cargo={:,.0f}  Total={:,.0f}".format(c33_sin_ret, c33_sin_ac, c33_sin_tot))
        else:
            print("  FALLO  TOTAL C33 Siniestros  Ret={:,.0f}  A cargo={:,.0f}  Total={:,.0f}   C15  Ret={:,.0f}  A cargo={:,.0f}  Total={:,.0f}".format(
                c33_sin_ret, c33_sin_ac, c33_sin_tot, c15_ret, c15_ac, c15_tot))
            todo_ok = False
    else:
        print("  [AVISO] No se encontró ramo Hospitalización Colectivo en C15.")

    col_hosp_a = None
    for c in df20a.columns:
        if "Hospitalizacion" in c or "Hospitalización" in c:
            if "Colectivo" in c or "colectivo" in c:
                col_hosp_a = c
                break
    if col_hosp_a is None:
        col_hosp_a = "Hospitalizacion Colectivo"
    col_hosp_d = None
    for c in df20d.columns:
        if "Hospitalizacion" in c or "Hospitalización" in c:
            if "Colectivo" in c or "colectivo" in c:
                col_hosp_d = c
                break
    if col_hosp_d is None:
        col_hosp_d = "Hospitalizacion Colectivo"

    nom_col = df20a.columns[0]
    df33_emp = df33[df33["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"]
    fallos = 0
    for _, row in df33_emp.iterrows():
        nombre = str(row["NOMBRE_EMPRESA"]).strip()
        norm = _normalizar(nombre)
        c33_rp = float(row["RESERVAS_PRIMA_RETENCION_PROPIA"])
        c33_rs = float(row["RESERVAS_SINIESTROS_RETENCION_PROPIA"])
        match_a = df20a[df20a[nom_col].astype(str).str.strip().apply(lambda x: _normalizar(str(x))) == norm]
        match_d = df20d[df20d[df20d.columns[0]].astype(str).str.strip().apply(lambda x: _normalizar(str(x))) == norm]
        if not match_a.empty and col_hosp_a in df20a.columns:
            v20a = float(match_a[col_hosp_a].iloc[0])
            if abs(c33_rp - v20a) > TOLERANCIA:
                fallos += 1
                if fallos <= 2:
                    print("  [Empresa] {}  C33 Prima Ret={:,.0f}  20-A Hosp.Col={:,.0f}".format(nombre[:40], c33_rp, v20a))
        if not match_d.empty and col_hosp_d in df20d.columns:
            v20d = float(match_d[col_hosp_d].iloc[0])
            if abs(c33_rs - v20d) > TOLERANCIA:
                fallos += 1
                if fallos <= 2:
                    print("  [Empresa] {}  C33 Siniestros Ret={:,.0f}  20-D Hosp.Col={:,.0f}".format(nombre[:40], c33_rs, v20d))
    if fallos == 0:
        print("  OK  Por empresa: Reservas prima Ret (C33) = 20-A Hospitalización Colectivo; Reservas siniestros Ret (C33) = 20-D Hospitalización Colectivo.")
    else:
        print("  [AVISO] {} empresas con diferencia en retención propia vs 20-A/20-D.".format(fallos))
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
