"""
Verifica Cuadro 36 (Reservas prestaciones y siniestros pendientes + ocurridos y no notificados) contra:

1) Consistencia interna: TOTAL (A+B) = PRESTACIONES_SINIESTROS_PENDIENTES_A + SINIESTROS_OCURRIDOS_NO_NOTIFICADOS_B.
2) Cuadro 16: la columna PRESTACIONES_SINIESTROS_PENDIENTES_A (A) del Cuadro 36 debe coincidir con
   RETENCION_PROPIA del Cuadro 16 (reservas para prestaciones y siniestros pendientes por empresa, retención propia).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
TOLERANCIA = 500.0  # diferencias de redondeo
TOLERANCIA_PCT = 0.5  # para % B/A


def _normalizar(s: str) -> str:
    return (
        s.upper()
        .strip()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace(",", "")
        .replace(".", "")
    )


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path36 = carpeta / "cuadro_36_reservas_prestaciones_siniestros_pendientes_ocurridos_no_notificados.csv"
    path16 = carpeta / "cuadro_16_reservas_prestaciones_siniestros_por_empresa.csv"
    for p in (path36, path16):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False
    df36 = pd.read_csv(path36, sep=SEP, encoding=ENCODING)
    df16 = pd.read_csv(path16, sep=SEP, encoding=ENCODING)

    todo_ok = True

    # 1) Consistencia interna: Total = A + B (excl. fila TOTAL para no duplicar)
    df36_emp = df36[
        df36["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() != "TOTAL"
    ].copy()
    print("")
    print("  Cuadro 36 – Consistencia interna (TOTAL = A + B)")
    print("")
    for i in range(len(df36_emp)):
        total = float(df36_emp.iloc[i]["TOTAL_A_MAS_B"])
        a = float(df36_emp.iloc[i]["PRESTACIONES_SINIESTROS_PENDIENTES_A"])
        b = float(df36_emp.iloc[i]["SINIESTROS_OCURRIDOS_NO_NOTIFICADOS_B"])
        suma = a + b
        diff = abs(total - suma)
        ok = diff <= TOLERANCIA
        if not ok:
            todo_ok = False
            print("  {}: TOTAL={:.0f} A+B={:.0f} diff={:.0f} FAIL".format(
                df36_emp.iloc[i]["NOMBRE_EMPRESA"][:40], total, suma, diff
            ))
    if todo_ok:
        print("  Todas las filas (empresas): TOTAL = A + B OK.")
    print("")

    # Fila TOTAL en C36: suma de columnas
    total_row = df36[df36["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper() == "TOTAL"]
    if not total_row.empty:
        t_total = float(total_row.iloc[0]["TOTAL_A_MAS_B"])
        t_a = float(total_row.iloc[0]["PRESTACIONES_SINIESTROS_PENDIENTES_A"])
        t_b = float(total_row.iloc[0]["SINIESTROS_OCURRIDOS_NO_NOTIFICADOS_B"])
        if abs(t_total - (t_a + t_b)) > TOLERANCIA:
            todo_ok = False
            print("  Fila TOTAL C36: TOTAL={:.0f} A+B={:.0f} FAIL".format(t_total, t_a + t_b))
        suma_emp_total = df36_emp["TOTAL_A_MAS_B"].astype(float).sum()
        suma_emp_a = df36_emp["PRESTACIONES_SINIESTROS_PENDIENTES_A"].astype(float).sum()
        suma_emp_b = df36_emp["SINIESTROS_OCURRIDOS_NO_NOTIFICADOS_B"].astype(float).sum()
        if abs(suma_emp_total - t_total) > TOLERANCIA or abs(suma_emp_a - t_a) > TOLERANCIA or abs(suma_emp_b - t_b) > TOLERANCIA:
            todo_ok = False
            print("  Suma empresas vs TOTAL C36: FAIL")
    print("")

    # 2) C36 columna (A) = C16 RETENCION_PROPIA por empresa
    nom16 = df16["NOMBRE_EMPRESA"].astype(str).str.strip()
    map16 = {}
    for i in range(len(df16)):
        n = _normalizar(nom16.iloc[i])
        if n:
            map16[n] = float(df16.iloc[i]["RETENCION_PROPIA"])

    print("  Cuadro 36 col. (A) vs Cuadro 16 RETENCION_PROPIA")
    print("")
    no_encontradas = []
    diferencias = []
    for i in range(len(df36_emp)):
        nombre = df36_emp.iloc[i]["NOMBRE_EMPRESA"]
        a_c36 = float(df36_emp.iloc[i]["PRESTACIONES_SINIESTROS_PENDIENTES_A"])
        n_norm = _normalizar(str(nombre))
        n_buscar = n_norm.split(" (")[0].strip()
        ref = None
        if n_buscar in map16:
            ref = map16[n_buscar]
        if ref is None:
            # _normalizar quita puntos: "C.A." -> "CA"
            n_alt = n_buscar.replace(" CA ", " SA ") if " CA " in n_buscar else n_buscar.replace(" SA ", " CA ")
            if n_alt in map16:
                ref = map16[n_alt]
        if ref is None:
            for k in map16:
                if k in n_buscar or n_buscar in k:
                    ref = map16[k]
                    break
        if ref is None:
            no_encontradas.append(nombre[:50])
            continue
        diff = abs(a_c36 - ref)
        if diff > TOLERANCIA:
            todo_ok = False
            diferencias.append((nombre[:45], a_c36, ref, diff))

    for nom, a36, ref, diff in diferencias[:15]:
        print("  [FAIL] {} C36(A)={:.0f} C16(Ret)={:.0f} diff={:.0f}".format(nom, a36, ref, diff))
    if len(diferencias) > 15:
        print("  ... y {} más.".format(len(diferencias) - 15))
    for nom in no_encontradas[:5]:
        print("  [NO ENCONTRADA en C16] {}".format(nom))
    if not diferencias and not no_encontradas:
        print("  Todas las empresas: C36 (A) = C16 RETENCION_PROPIA OK.")
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
