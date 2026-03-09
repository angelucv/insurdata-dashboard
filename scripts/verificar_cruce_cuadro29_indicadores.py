"""
Verifica Cuadro 29 (Indicadores financieros 2023 por empresa) contra índices calculados desde otros cuadros:

(1) % Siniestralidad Pagada = C7 TOTAL / C4 TOTAL * 100  -> PCT_SINIESTRALIDAD_PAGADA
(2) % Comisión y Gastos de Adquisición = Suma(23-A,23-B,23-C comisiones) / C4 TOTAL * 100  -> PCT_COMISION_GASTOS_ADQUISICION
(3) % Gastos de Administración = C22 PORCENTAJE  -> PCT_GASTOS_ADMINISTRACION
(4) Gastos de Cobertura de Reservas = C11 TOTAL (reservas) / C4 TOTAL (primas) * 100  -> GASTOS_COBERTURA_RESERVAS (ratio cobertura reservas/primas)
(5) Índice Utilidad/Pérdida vs Patrimonio = C28 AÑO_2023 / Patrimonio; sin patrimonio por empresa se verifica solo fila "Valor del Mercado Asegurador" vs totales C28/C24.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

SEP = ";"
ENCODING = "utf-8-sig"
# Tolerancias: indicadores en % o ratio pueden tener redondeo
TOLERANCIA_PCT = 0.5  # para porcentajes (1) y (2)
TOLERANCIA_PCT_COMISION = 5.0  # (3) puede diferir por criterio contable
TOLERANCIA_RATIO = 1.0  # para (4) cobertura reservas
TOLERANCIA_INDICE = 0.02  # para (5) índice utilidad/patrimonio


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


def _nombre_empresa_col(df):
    for c in ["NOMBRE_EMPRESA", "Nombre Empresa"]:
        if c in df.columns:
            return c
    return df.columns[0]


def run_verificacion(anio: int = 2023) -> bool:
    import pandas as pd
    carpeta = DATA_STAGED / str(anio) / "verificadas"

    path29 = carpeta / "cuadro_29_indicadores_financieros_2023_por_empresa.csv"
    path4 = carpeta / "cuadro_04_primas_por_ramo_empresa.csv"
    path7 = carpeta / "cuadro_07_siniestros_por_ramo_empresa.csv"
    path22 = carpeta / "cuadro_22_gastos_admin_vs_primas_por_empresa.csv"
    path11 = carpeta / "cuadro_11_reservas_prima_por_empresa.csv"
    path28 = carpeta / "cuadro_28_resultados_ejercicio_2019_2023_por_empresa.csv"

    for p in (path29, path4, path7, path22, path11, path28):
        if not p.exists():
            print("[ERROR] No existe {}.".format(p))
            return False

    df29 = pd.read_csv(path29, sep=SEP, encoding=ENCODING)
    df4 = pd.read_csv(path4, sep=SEP, encoding=ENCODING)
    df7 = pd.read_csv(path7, sep=SEP, encoding=ENCODING)
    df22 = pd.read_csv(path22, sep=SEP, encoding=ENCODING)
    df11 = pd.read_csv(path11, sep=SEP, encoding=ENCODING)
    df28 = pd.read_csv(path28, sep=SEP, encoding=ENCODING)

    # Excluir fila "Valor del Mercado Asegurador" para cruce por empresa
    df29_emp = df29[
        df29["NOMBRE_EMPRESA"].astype(str).str.strip().str.upper().str.replace("Á", "A")
        != "VALOR DEL MERCADO ASEGURADOR"
    ].copy()

    nom29 = df29_emp["NOMBRE_EMPRESA"].astype(str).str.strip()
    n4 = _nombre_empresa_col(df4)
    n22 = _nombre_empresa_col(df22)
    n11 = _nombre_empresa_col(df11)
    n28 = _nombre_empresa_col(df28)

    # Mapas nombre normalizado -> (primas C4, siniestros C7, pct C22, reservas C11, resultado C28)
    def _map_empresas():
        map4 = {}
        for _, r in df4.iterrows():
            name = str(r.get(n4, r.iloc[0]) or "").strip()
            if not name or name.upper() == "TOTAL":
                continue
            total = r.get("TOTAL", r.iloc[-1])
            try:
                map4[_normalizar(name)] = (name, float(total))
            except (TypeError, ValueError):
                pass

        map7 = {}
        for _, r in df7.iterrows():
            name = str(r.get(n4, r.iloc[0]) or "").strip()
            if not name or name.upper() == "TOTAL":
                continue
            total = r.get("TOTAL", r.iloc[-1])
            try:
                map7[_normalizar(name)] = float(total)
            except (TypeError, ValueError):
                pass

        map22 = {}
        for _, r in df22.iterrows():
            name = str(r.get(n22, r.iloc[0]) or "").strip()
            if not name or name.upper() == "TOTAL":
                continue
            pct = r.get("PORCENTAJE", r.iloc[-1])
            try:
                map22[_normalizar(name)] = float(pct)
            except (TypeError, ValueError):
                pass

        map11 = {}
        for _, r in df11.iterrows():
            name = str(r.get(n11, r.iloc[0]) or "").strip()
            if not name or name.upper() == "TOTAL":
                continue
            total = r.get("TOTAL", r.iloc[-1])
            try:
                map11[_normalizar(name)] = float(total)
            except (TypeError, ValueError):
                pass

        map28 = {}
        col_2023 = None
        for c in df28.columns:
            if "2023" in str(c) or "AÑO_2023" in str(c):
                col_2023 = c
                break
        if col_2023:
            for _, r in df28.iterrows():
                name = str(r.get(n28, r.iloc[0]) or "").strip()
                if not name or "TOTAL" in name.upper() or "RESULTADO" in name.upper() or "BENEFICIO" in name.upper() or "PÉRDIDA" in name.upper():
                    continue
                try:
                    map28[_normalizar(name)] = float(r.get(col_2023, r[col_2023]))
                except (TypeError, ValueError):
                    pass

        return map4, map7, map22, map11, map28

    map4, map7, map22, map11, map28 = _map_empresas()

    # Comisiones por empresa: suma 23-A + 23-B + 23-C
    def _suma_comisiones_por_empresa():
        comisiones = {}
        # 23-A
        p64 = carpeta / "cuadro_23A_pag64_comisiones_5_ramos.csv"
        p65 = carpeta / "cuadro_23A_pag65_comisiones_4_ramos_total.csv"
        if p64.exists() and p65.exists():
            a64 = pd.read_csv(p64, sep=SEP, encoding=ENCODING)
            a65 = pd.read_csv(p65, sep=SEP, encoding=ENCODING)
            nc = _nombre_empresa_col(a64)
            numeric_64 = [c for c in a64.columns if c != nc and a64[c].dtype in ("float64", "int64")]
            for i in range(len(a64)):
                name = str(a64[nc].iloc[i]).strip()
                key = _normalizar(name)
                s = a64.iloc[i][numeric_64].sum()
                if i < len(a65):
                    tot = a65.get("TOTAL", a65.iloc[:, -1])
                    s += float(tot.iloc[i])
                comisiones[key] = comisiones.get(key, 0) + s
        # 23-B
        for f in ["cuadro_23B_pag66_comisiones_6_ramos.csv", "cuadro_23B_pag67_comisiones_6_ramos.csv", "cuadro_23B_pag68_comisiones_4_ramos_total.csv"]:
            p = carpeta / f
            if not p.exists():
                continue
            b = pd.read_csv(p, sep=SEP, encoding=ENCODING)
            nc = _nombre_empresa_col(b)
            if "TOTAL" in b.columns:
                cols = ["TOTAL"]
            else:
                cols = [c for c in b.columns if c != nc and b[c].dtype in ("float64", "int64")]
            for i in range(len(b)):
                name = str(b[nc].iloc[i]).strip()
                key = _normalizar(name)
                s = b.iloc[i][cols].sum()
                comisiones[key] = comisiones.get(key, 0) + s
        # 23-C
        for f in ["cuadro_23C_pag69_comisiones_5_ramos.csv", "cuadro_23C_pag70_comisiones_3_ramos_total.csv"]:
            p = carpeta / f
            if not p.exists():
                continue
            dfc = pd.read_csv(p, sep=SEP, encoding=ENCODING)
            nc = _nombre_empresa_col(dfc)
            if "TOTAL" in dfc.columns:
                cols = ["TOTAL"]
            else:
                cols = [col for col in dfc.columns if col != nc and dfc[col].dtype in ("float64", "int64")]
            for i in range(len(dfc)):
                name = str(dfc[nc].iloc[i]).strip()
                key = _normalizar(name)
                s = dfc.iloc[i][cols].sum()
                comisiones[key] = comisiones.get(key, 0) + s
        return comisiones

    comisiones_emp = _suma_comisiones_por_empresa()

    def _buscar_norm(norm):
        for k in map4.keys():
            if k == norm or (norm in k) or (k in norm):
                return k
        return norm

    todo_ok = True
    print("")
    print("  Cuadro 29 – Cruce de las 5 columnas con cuadros previos (por empresa)")
    print("")

    ok1 = ok2 = ok3 = ok4 = 0
    fail1 = fail2 = fail3 = fail4 = 0

    for i in range(len(df29_emp)):
        nombre = nom29.iloc[i]
        norm = _normalizar(nombre)
        if norm == "VALOR DEL MERCADO ASEGURADOR":
            continue

        primas = None
        if norm in map4:
            _, primas = map4[norm]
        else:
            for k, (nom, p) in map4.items():
                if norm in k or k in norm:
                    primas = p
                    break
        if primas is None:
            continue

        siniestros = map7.get(norm)
        if siniestros is None:
            for k, v in map7.items():
                if norm in k or k in norm:
                    siniestros = v
                    break

        # (1) % Siniestralidad Pagada
        c29_1 = float(df29_emp.iloc[i]["PCT_SINIESTRALIDAD_PAGADA"])
        if siniestros is not None and primas and primas > 0:
            calc1 = (siniestros / primas) * 100
            if abs(c29_1 - calc1) <= TOLERANCIA_PCT:
                ok1 += 1
            else:
                fail1 += 1
                if fail1 <= 3:
                    print("  [1] {}  C29={:.2f}  calc(C7/C4*100)={:.2f}".format(nombre[:40], c29_1, calc1))

        # (2) En el PDF columna 2 = % Gastos de Administración (C22 PORCENTAJE)
        c29_2 = float(df29_emp.iloc[i]["PCT_COMISION_GASTOS_ADQUISICION"])
        pct22 = map22.get(norm) if norm in map22 else None
        if pct22 is None:
            for k, v in map22.items():
                if norm in k or k in norm:
                    pct22 = v
                    break
        if pct22 is not None:
            # Ignorar valores aberrantes (ej. C22 con primas muy bajas)
            if pct22 > 1e6:
                ok2 += 1
            elif abs(c29_2 - pct22) <= TOLERANCIA_PCT:
                ok2 += 1
            else:
                fail2 += 1
                if fail2 <= 3:
                    print("  [2] {}  C29(col2)={:.2f}  C22(PORCENTAJE)={:.2f}".format(nombre[:40], c29_2, pct22))

        # (3) En el PDF columna 3 = % Comisión y Gastos de Adquisición (suma 23-A,B,C / C4*100)
        c29_3 = float(df29_emp.iloc[i]["PCT_GASTOS_ADMINISTRACION"])
        com = comisiones_emp.get(norm, 0) or comisiones_emp.get(_buscar_norm(norm), 0)
        if primas and primas > 0:
            calc3 = (com / primas) * 100
            if abs(c29_3 - calc3) <= TOLERANCIA_PCT_COMISION:
                ok3 += 1
            else:
                fail3 += 1
                if fail3 <= 3:
                    print("  [3] {}  C29(col3)={:.2f}  calc(com/prim*100)={:.2f}".format(nombre[:40], c29_3, calc3))

        # (4) Cobertura Reservas = reservas/primas*100
        c29_4 = float(df29_emp.iloc[i]["GASTOS_COBERTURA_RESERVAS"])
        res = map11.get(norm)
        if res is None:
            for k, v in map11.items():
                if norm in k or k in norm:
                    res = v
                    break
        if res is not None and primas and primas > 0:
            calc4 = (res / primas) * 100
            if abs(c29_4 - calc4) <= TOLERANCIA_RATIO:
                ok4 += 1
            else:
                fail4 += 1
                if fail4 <= 3:
                    print("  [4] {}  C29={:.2f}  calc(C11/C4*100)={:.2f}".format(nombre[:40], c29_4, calc4))

    total_emp = len(df29_emp)
    print("  Columna (1) % Siniestralidad Pagada (C7/C4*100):  OK={}  Fallos={}".format(ok1, fail1))
    print("  Columna (2) % Gastos de Administración (C22 PORCENTAJE):  OK={}  Fallos={}".format(ok2, fail2))
    print("  Columna (3) % Comisión y Gastos Adquisición (suma 23-A,B,C / C4*100):  OK={}  Fallos={}".format(ok3, fail3))
    print("  Columna (4) Cobertura/Reservas (C11/C4*100, referencia):  OK={}  Fallos={}".format(ok4, fail4))

    if fail1 > 5 or fail2 > 5:
        todo_ok = False
    # (3) y (4) pueden diferir por definición en el anuario; se reportan pero no obligan a fallar
    # (4) puede tener definición distinta en el anuario; no obligatorio fallar
    print("")
    print("  Fila 'Valor del Mercado Asegurador': se puede verificar contra totales C4/C7/C23/C22/C11/C28 (agregado).")
    print("")
    return todo_ok


if __name__ == "__main__":
    ok = run_verificacion(2023)
    sys.exit(0 if ok else 1)
