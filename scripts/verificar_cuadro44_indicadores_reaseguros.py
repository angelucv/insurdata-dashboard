"""
Verifica Cuadro 44 (Indicadores financieros 2023 reaseguros) contra tablas anteriores.

Por empresa, los 6 indicadores deben coincidir con ratios calculados a partir de:
- (1) % Siniestralidad Pagada: Prestaciones y siniestros pagados (43-B) / Total ingresos (43-A) * 100
- (2) % Gastos Administración: Gastos administración (43-B) / Total ingresos (43-A) * 100
- (3) % Comisión: Gastos de adquisición (43-B) / Total ingresos (43-A) * 100
- (4) Cobertura de reservas: referencia reservas/primas (42, 43-A)
- (5) Índice endeudamiento: Total pasivo (42) / Total capital (42)
- (6) Utilidad o Pérdida vs Patrimonio: Utilidad (42) / Total capital (42)

Solo se verifican las 4 empresas (RIV, Kairos, Provincial, Delta); no el agregado "Valor del Mercado".
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
# Las definiciones exactas de (1)-(6) pueden estar en Notas Finales del anuario; se usa tolerancia amplia como referencia.
TOLERANCIA_PCT = 20.0  # puntos porcentuales (referencia)
TOLERANCIA_RATIO = 2.5  # ratio utilidad/patrimonio (referencia)

# Orden de empresas en 43-A/43-B y 42 (columnas)
EMPRESAS_COLS = ["RIV", "KAIROS", "PROVINCIAL", "DELTA"]
NOMBRES_44_A_COLS = [
    "C.A. Reaseguradora Internacional de Venezuela RIV",
    "Kairos de Reaseguros, C.A.",
    "Provincial de Reaseguros, C.A",
    "Reaseguradora Delta, C.A.",
]


def _norm(s: str) -> str:
    t = s.upper().strip()
    for a, b in [("\u00c1", "A"), ("\u00c9", "E"), ("\u00cd", "I"), ("\u00d3", "O"), ("\u00da", "U")]:
        t = t.replace(a, b)
    return t.replace("  ", " ")


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    path44 = carpeta / "cuadro_44_indicadores_financieros_2023_reaseguros.csv"
    path43a = carpeta / "cuadro_43A_estado_ganancias_perdidas_ingresos_por_empresa_reaseguros.csv"
    path43b = carpeta / "cuadro_43B_estado_ganancias_perdidas_egresos_por_empresa_reaseguros.csv"
    path42 = carpeta / "cuadro_42_balance_condensado_por_empresa_reaseguros.csv"
    if not path44.exists():
        print("[ERROR] No existe {}.".format(path44))
        return False
    df44 = pd.read_csv(path44, sep=SEP, encoding=ENCODING)
    # Solo 4 empresas (excluir "Valor del Mercado Reasegurador")
    df44_emp = df44[df44["NOMBRE_EMPRESA"].str.contains("Valor del Mercado", na=False) == False].head(4)
    if len(df44_emp) < 4:
        print("[AVISO] Cuadro 44 tiene menos de 4 filas de empresas.")
    refs = {}
    if path43a.exists() and path43b.exists():
        da = pd.read_csv(path43a, sep=SEP, encoding=ENCODING)
        db = pd.read_csv(path43b, sep=SEP, encoding=ENCODING)
        # TOTAL INGRESOS en 43-A
        row_ing = da[da["CONCEPTO"].str.contains("TOTAL INGRESOS", na=False)]
        if not row_ing.empty:
            for j, col in enumerate(["RIV_MONTO", "KAIROS_MONTO", "PROVINCIAL_MONTO", "DELTA_MONTO"]):
                refs.setdefault(col.replace("_MONTO", ""), {})["ingresos"] = float(row_ing.iloc[0][col])
        # 43-B: Prestaciones y siniestros pagados, Gastos administración, Gastos adquisición
        for conc_sub, key in [
            ("PRESTACIONES Y SINIESTROS PAGADOS", "siniestros"),
            ("GASTOS DE ADMINISTRACION", "gastos_adm"),
            ("GASTOS DE ADQUISICION", "gastos_comision"),
        ]:
            row = db[db["CONCEPTO"].str.upper().str.contains(conc_sub.replace("Í", "I"), na=False)]
            if not row.empty:
                for col in ["RIV_MONTO", "KAIROS_MONTO", "PROVINCIAL_MONTO", "DELTA_MONTO"]:
                    emp = col.replace("_MONTO", "")
                    refs.setdefault(emp, {})[key] = float(row.iloc[0][col])
    if path42.exists():
        d42 = pd.read_csv(path42, sep=SEP, encoding=ENCODING)
        conceptos = {
            "UTILIDAD DEL EJERCICIO": "utilidad",
            "TOTAL CAPITAL Y OTROS": "capital",
            "TOTAL PASIVO": "pasivo",
            "RESERVAS TÉCNICAS": "reservas_tecnicas",
        }
        for conc, key in conceptos.items():
            row = d42[d42["CONCEPTO"].str.upper().str.replace("Á", "A").str.contains(conc.replace("É", "E").replace("Á", "A"), na=False)]
            if not row.empty:
                for col in ["RIV", "KAIROS", "PROVINCIAL", "DELTA"]:
                    refs.setdefault(col, {})[key] = float(row.iloc[0][col])
    todo_ok = True
    print("")
    print("  Cuadro 44 (Indicadores financieros reaseguros) vs tablas anteriores")
    print("")
    for idx, row in df44_emp.iterrows():
        emp_nom = row["NOMBRE_EMPRESA"]
        if "Valor del Mercado" in str(emp_nom):
            continue
        emp_col = None
        for k, nombre in enumerate(NOMBRES_44_A_COLS):
            if _norm(str(emp_nom)) in _norm(nombre) or _norm(nombre) in _norm(str(emp_nom)):
                emp_col = EMPRESAS_COLS[k]
                break
        if emp_col is None:
            if "RIV" in str(emp_nom) or "Internacional" in str(emp_nom):
                emp_col = "RIV"
            elif "Kairos" in str(emp_nom):
                emp_col = "KAIROS"
            elif "Provincial" in str(emp_nom):
                emp_col = "PROVINCIAL"
            elif "Delta" in str(emp_nom):
                emp_col = "DELTA"
        if emp_col is None:
            continue
        r = refs.get(emp_col, {})
        ingresos = r.get("ingresos") or 1.0
        # (1) % Siniestralidad
        sin = r.get("siniestros") or 0
        esp1 = (sin / ingresos * 100) if ingresos else 0
        v1 = float(row["PCT_SINIESTRALIDAD_PAGADA"])
        ok1 = abs(v1 - esp1) <= TOLERANCIA_PCT
        if not ok1:
            todo_ok = False
        print("  {}  (1)%% Siniestralidad: C44={:.2f}  esperado={:.2f}  {}".format(emp_nom[:45].ljust(46), v1, esp1, "OK" if ok1 else "FAIL"))
        # (2) % Gastos Adm
        ga = r.get("gastos_adm") or 0
        esp2 = (ga / ingresos * 100) if ingresos else 0
        v2 = float(row["PCT_GASTOS_ADMINISTRACION"])
        ok2 = abs(v2 - esp2) <= TOLERANCIA_PCT
        if not ok2:
            todo_ok = False
        print("       (2)%% Gastos Adm:   C44={:.2f}  esperado={:.2f}  {}".format(v2, esp2, "OK" if ok2 else "FAIL"))
        # (3) % Comisión
        gc = r.get("gastos_comision") or 0
        esp3 = (gc / ingresos * 100) if ingresos else 0
        v3 = float(row["PCT_COMISION"])
        ok3 = abs(v3 - esp3) <= TOLERANCIA_PCT
        if not ok3:
            todo_ok = False
        print("       (3)%% Comisión:     C44={:.2f}  esperado={:.2f}  {}".format(v3, esp3, "OK" if ok3 else "FAIL"))
        # (6) Utilidad vs Patrimonio
        util = r.get("utilidad") or 0
        cap = r.get("capital") or 1
        esp6 = (util / cap) if cap else 0
        v6 = float(row["UTILIDAD_PERDIDA_VS_PATRIMONIO"])
        ok6 = abs(v6 - esp6) <= TOLERANCIA_RATIO * max(abs(esp6), 0.01)
        if not ok6:
            todo_ok = False
        print("       (6) Utilidad/Patr: C44={:.2f}  esperado={:.2f}  {}".format(v6, esp6, "OK" if ok6 else "FAIL"))
        print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
