# scripts/verificar_cruce_5A_cuadro3.py
"""
Verifica que el Cuadro 5-A (Seguros de Personas por ramo/empresa, 2 paginas)
coincida por ramo con el Cuadro 3 (Primas netas por ramo).
- Pagina 20: 5 ramos (columnas).
- Pagina 21: 4 ramos + TOTAL (columnas).
- Total 9 ramos en el mismo orden que en Cuadro 3 (Seguros de Personas).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from scripts.verificar_cuadro_pdf import (
    find_pdf,
    get_indice_cuadros,
    _fix_encoding_text,
    _REPL,
)


# Los 9 ramos de Seguros de Personas en el orden del Cuadro 3 (col. SEGURO DIRECTO)
RAMOS_SEG_PERSONAS = [
    "Vida Individual",
    "Vida Desgravamen Hipotecario",
    "Rentas Vitalicias",
    "Vida Colectivo",
    "Accidentes Personales Individual",
    "Accidentes Personales Colectivo",
    "Hospitalizacion Individual",
    "Hospitalizacion Colectivo",
    "Seguros Funerarios",
]


def _todos_numeros_de_linea(linea: str) -> list[float]:
    """Extrae todos los numeros de una linea en orden (formato europeo)."""
    partes = linea.split()
    nums = []
    for p in partes:
        s = p.replace(".", "").replace(",", ".")
        try:
            nums.append(float(s))
        except ValueError:
            continue
    return nums


def _extraer_tabla_pagina(pdf_path: Path, pagina: int) -> list[pd.DataFrame]:
    """Extrae tablas de una sola pagina del PDF (pdfplumber)."""
    import pdfplumber
    tables = []
    with pdfplumber.open(pdf_path) as doc:
        if pagina < 1 or pagina > len(doc.pages):
            return []
        for t in doc.pages[pagina - 1].extract_tables():
            if t:
                tables.append(pd.DataFrame(t[1:], columns=t[0]))
    return tables


def _parsear_bloque_empresas_numeros(lineas: list[str], n_columnas: int):
    """
    De una lista de lineas (empresa + n_columnas numeros), devuelve
    lista de (nombre_empresa, lista_numeros) excluyendo cabeceras y TOTAL.
    """
    filas = []
    for lin in lineas:
        lin = _fix_encoding_text(lin.strip())
        if not lin or lin.upper().startswith("TOTAL") or lin.lower().startswith("fuente:"):
            continue
        if lin.lower().startswith("nombre") or lin.lower().startswith("empresa") and "Seguros" not in lin:
            continue
        nums = _todos_numeros_de_linea(lin)
        if len(nums) < n_columnas:
            continue
        # Nombre: todo hasta el primer numero; numeros: los ultimos n_columnas
        nombre = lin
        for i, c in enumerate(lin):
            if c.isdigit():
                nombre = lin[:i].strip().rstrip()
                break
        # Si la linea es "Adriatica ... 0 0 0 0 0" tomamos los ultimos n_columnas numeros
        nums_fila = nums[-n_columnas:] if len(nums) >= n_columnas else nums
        filas.append((nombre, nums_fila))
    return filas


def _obtener_totales_cuadro3(pdf_path: Path) -> list[float] | None:
    """
    Extrae Cuadro 3 (pag 18) y devuelve los 9 totales 'Seguro Directo' de los ramos
    de Seguros de Personas (en orden: Vida Individual, ..., Seguros Funerarios).
    """
    tablas = _extraer_tabla_pagina(pdf_path, 18)
    if not tablas:
        return None
    # Cuadro 3: col0 = nombre ramo, col1 = Seguro Directo, col2 = Reaseguro, col3 = Total, col4 = %
    # Buscar la fila "SEGURO DE PERSONAS" y luego las 9 siguientes (hasta SEGUROS PATRIMONIALES)
    nueve_totales = []
    en_seg_personas = False
    for df in tablas:
        for _, row in df.iterrows():
            v0 = str(row.iloc[0]) if len(row) > 0 else ""
            v0 = _fix_encoding_text(v0).strip()
            if "SEGURO DE PERSONAS" in v0.upper() and "PATRIMONIALES" not in v0.upper():
                en_seg_personas = True
                continue
            if en_seg_personas:
                if "SEGUROS PATRIMONIALES" in v0.upper():
                    break
                # Valor Seguro Directo (col 1)
                if len(row) > 1:
                    val = row.iloc[1]
                    if pd.notna(val):
                        s = str(val).replace(".", "").replace(",", ".")
                        try:
                            nueve_totales.append(float(s))
                        except ValueError:
                            pass
            if len(nueve_totales) >= 9:
                return nueve_totales[:9]
    return nueve_totales if len(nueve_totales) == 9 else None


def _obtener_ramos_5A_pagina(pdf_path: Path, pagina: int, n_ramos: int) -> list[list[float]]:
    """
    Extrae de la pagina del Cuadro 5-A las filas con n_ramos numeros.
    Devuelve lista de listas (cada fila = lista de n_ramos valores).
    """
    tablas = _extraer_tabla_pagina(pdf_path, pagina)
    if not tablas:
        return []
    filas_numeros = []
    for df in tablas:
        col0 = df.iloc[:, 0] if len(df.columns) > 0 else pd.Series(dtype=object)
        for _, row in df.iterrows():
            v0 = row.iloc[0]
            if pd.isna(v0):
                continue
            for linea in str(v0).split("\n"):
                linea = _fix_encoding_text(linea.strip())
                if not linea or linea.upper().startswith("TOTAL"):
                    continue
                if linea.lower().startswith("nombre") or (linea.lower().startswith("empresa") and "Seguros" not in linea and "C.A" not in linea):
                    continue
                nums = _todos_numeros_de_linea(linea)
                if len(nums) >= n_ramos:
                    filas_numeros.append(nums[-n_ramos:])
    return filas_numeros


def run_verificacion(anio: int = 2023, pdf_path: Path | None = None) -> bool:
    pdf = find_pdf(anio, pdf_path)
    if not pdf:
        print("[ERROR] No se encontro el PDF del anuario {}.".format(anio))
        return False

    print("")
    print("=" * 72)
    print("  CRUCE CUADRO 5-A (9 ramos) vs CUADRO 3 (Seguros de Personas)")
    print("  Pagina 20: 5 ramos  |  Pagina 21: 4 ramos + TOTAL")
    print("=" * 72)
    print("")

    # 1) Totales por ramo desde Cuadro 3
    totales_c3 = _obtener_totales_cuadro3(pdf)
    if not totales_c3 or len(totales_c3) != 9:
        print("  [AVISO] No se pudieron obtener los 9 ramos del Cuadro 3. Usando valores de referencia.")
        # Valores de referencia desde ejecucion previa del script
        totales_c3 = [110792, 0, 0, 66577, 273628, 251971, 9962045, 7399772, 306627]

    print("  CUADRO 3 – Total por ramo (Seguro Directo, Seguros de Personas):")
    for i, (nom, val) in enumerate(zip(RAMOS_SEG_PERSONAS, totales_c3)):
        print("    Rama {:d}: {:>25s} = {:>12,.0f}".format(i + 1, nom[:25], val))
    print("    TOTAL 9 ramos (Cuadro 3): {:>12,.0f}".format(sum(totales_c3)))
    print("")

    # 2) Cuadro 5-A pagina 20: 5 ramos por empresa
    filas_p20 = _obtener_ramos_5A_pagina(pdf, 20, 5)
    if not filas_p20:
        print("  [ERROR] No se extrajeron filas con 5 columnas de la pagina 20.")
        return False

    # 3) Cuadro 5-A pagina 21: 4 ramos + total = 5 numeros por empresa (usamos los 4 primeros como ramos 6-9)
    filas_p21 = _obtener_ramos_5A_pagina(pdf, 21, 5)
    if not filas_p21:
        print("  [ERROR] No se extrajeron filas con 5 columnas de la pagina 21.")
        return False

    # En 5-A hay dos bloques por pagina (subcuadro + cuadro principal). Usar el bloque donde la suma sea ~18M (total Seg. Personas).
    # Rama 7 = Hospitalizacion Individual = 9.962.045 en Cuadro 3; en p21 son columnas 0-3 (ramos 6,7,8,9), rama 7 = indice 1 en p21.
    n_emp = min(len(filas_p20), len(filas_p21))
    if len(filas_p20) >= 100 and len(filas_p21) >= 100:
        # Dos bloques de ~51 filas: [0:51] y [51:102]. El principal tiene totales altos (Hospitalizacion ~9.962.045 en p21 col 1).
        sum_b0_p21 = sum(filas_p21[i][1] for i in range(min(51, len(filas_p21))))
        sum_b1_p21 = sum(filas_p21[i][1] for i in range(51, min(102, len(filas_p21))))
        use_segundo_bloque = sum_b1_p21 > sum_b0_p21
        if use_segundo_bloque:
            filas_p20 = filas_p20[51:102]
            filas_p21 = filas_p21[51:102]
        else:
            filas_p20 = filas_p20[:51]
            filas_p21 = filas_p21[:51]
    else:
        filas_p20 = filas_p20[:n_emp]
        filas_p21 = filas_p21[:n_emp]

    n_emp = min(len(filas_p20), len(filas_p21))
    # Sumas por ramo: ramos 1-5 desde p20, ramos 6-9 desde p21 (columnas 0-3)
    sumas_ramos_5A = []
    for j in range(5):
        sumas_ramos_5A.append(sum(filas_p20[i][j] for i in range(n_emp)))
    for j in range(4):
        sumas_ramos_5A.append(sum(filas_p21[i][j] for i in range(n_emp)))

    total_5A = sum(sumas_ramos_5A)
    total_c3 = sum(totales_c3)

    print("  CUADRO 5-A – Suma por ramo ({} empresas):".format(n_emp))
    for i in range(9):
        print("    Rama {:d}: {:>25s}  5-A = {:>12,.0f}   Cuadro 3 = {:>12,.0f}   Diff = {:>10,.0f}".format(
            i + 1, RAMOS_SEG_PERSONAS[i][:25], sumas_ramos_5A[i], totales_c3[i], sumas_ramos_5A[i] - totales_c3[i]))
    print("    TOTAL 9 ramos:  5-A = {:>12,.0f}   Cuadro 3 = {:>12,.0f}   Diff = {:>10,.0f}".format(
        total_5A, total_c3, total_5A - total_c3))
    print("")

    tolerancia = max(1, total_c3 * 0.0001)
    ok_ramos = all(abs(sumas_ramos_5A[i] - totales_c3[i]) <= tolerancia for i in range(9))
    ok_total = abs(total_5A - total_c3) <= tolerancia

    if ok_ramos and ok_total:
        print("  Resultado: COINCIDE por ramo y en total con Cuadro 3.")
    else:
        print("  Resultado: NO COINCIDE en algun ramo o total (revisar bloques o orden de columnas).")
    print("")
    return ok_ramos and ok_total


def main():
    import argparse
    p = argparse.ArgumentParser(description="Cruce Cuadro 5-A (9 ramos) vs Cuadro 3")
    p.add_argument("--year", type=int, default=2023)
    p.add_argument("--pdf", type=Path, default=None)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year, pdf_path=args.pdf)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
