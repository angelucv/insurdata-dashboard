# scripts/verificar_cruce_5C_cuadro3.py
"""
Verifica que el Cuadro 5-C (Seguros Obligacionales o de Responsabilidad por ramo/empresa,
páginas 25 y 26) coincida por ramo con el Cuadro 3 (8 ramos).
- Página 25: 4 ramos (columnas).
- Página 26: 4 ramos + TOTAL (columnas).
Total 8 ramos en el mismo orden que en Cuadro 3 (SEGUROS OBLIGACIONALES O DE RESPONSABILIDAD).
"""
from __future__ import annotations

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

from scripts.verificar_cuadro_pdf import find_pdf, _fix_encoding_text

# Los 8 ramos de Seguros Obligacionales o de Responsabilidad (orden Cuadro 3, col. SEGURO DIRECTO)
RAMOS_SEG_OBLIGACIONALES = [
    "Responsabilidad Civil Automóvil",
    "Responsabilidad Civil Patronal",
    "Responsabilidad Civil General",
    "Responsabilidad Civil Profesional",
    "Fianzas",
    "Fidelidad de Empleados",
    "Responsabilidad Civil de Productos",
    "Seguros de Crédito",
]

# Pág 25: 5 columnas = ramos 1-5. Pág 26: 4 columnas (ramos 6-8 + TOTAL); usar solo cols 0-2 para ramos 6-8.
PAGINAS_5C = [(25, 5), (26, 4)]


def _todos_numeros_de_linea(linea: str) -> list[float]:
    """Extrae todos los números de una línea (formato europeo)."""
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
    """Extrae tablas de una sola página del PDF (pdfplumber)."""
    import pdfplumber
    tables = []
    with pdfplumber.open(pdf_path) as doc:
        if pagina < 1 or pagina > len(doc.pages):
            return []
        for t in doc.pages[pagina - 1].extract_tables():
            if t:
                tables.append(pd.DataFrame(t[1:], columns=t[0]))
    return tables


def _parsear_linea_cuadro3(linea: str) -> tuple[str, list[float]] | None:
    """Si la línea tiene 4 números (seguro directo, reaseguro, total, %), devuelve (ramo, [n1,n2,n3,n4])."""
    nums = _todos_numeros_de_linea(linea)
    if len(nums) != 4:
        return None
    for i, c in enumerate(linea):
        if c.isdigit():
            nombre = linea[:i].strip().rstrip()
            break
    else:
        nombre = linea.strip()
    return (_fix_encoding_text(nombre), nums)


def _obtener_totales_obligacionales_cuadro3(pdf_path: Path) -> list[float] | None:
    """
    Extrae Cuadro 3 (pág 18) y devuelve los 8 totales 'Seguro Directo' de los ramos
    Seguros Obligacionales o de Responsabilidad, parseando por líneas.
    """
    tablas = _extraer_tabla_pagina(pdf_path, 18)
    if not tablas:
        return None
    todas_filas = []
    for df in tablas:
        for _, row in df.iterrows():
            celda0 = row.iloc[0] if len(row) > 0 else None
            if pd.isna(celda0):
                continue
            texto = _fix_encoding_text(str(celda0))
            for linea in texto.replace("\r", "").split("\n"):
                linea = linea.strip()
                if not linea or linea.upper() == "TOTAL":
                    continue
                parsed = _parsear_linea_cuadro3(linea)
                if parsed:
                    todas_filas.append(parsed)
    # Buscar la primera fila que sea "Responsabilidad Civil Automóvil" y tomar 8 ramos (Seguro Directo = n[0])
    for i in range(len(todas_filas)):
        nombre, _ = todas_filas[i]
        if "Responsabilidad Civil Automóvil" in nombre or "RESPONSABILIDAD CIVIL AUTOM" in nombre.upper():
            ocho = []
            for j in range(8):
                if i + j >= len(todas_filas):
                    break
                _, n = todas_filas[i + j]
                ocho.append(n[0])
            return ocho if len(ocho) == 8 else None
    return None


def _extraer_filas_5C_pagina(pdf_path: Path, pagina: int, n_columnas: int) -> list[tuple[str, list[float]]]:
    """Extrae filas (nombre_empresa, lista_numeros) de una página del Cuadro 5-C."""
    tablas = _extraer_tabla_pagina(pdf_path, pagina)
    filas = []
    for df in tablas:
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
                if len(nums) < n_columnas:
                    continue
                nombre = linea
                for i, c in enumerate(linea):
                    if c.isdigit():
                        nombre = linea[:i].strip().rstrip()
                        break
                filas.append((nombre, nums[-n_columnas:]))
    return filas


def run_verificacion(anio: int = 2023, pdf_path: Path | None = None) -> bool:
    pdf = find_pdf(anio, pdf_path)
    if not pdf:
        print("[ERROR] No se encontró el PDF del anuario {}.".format(anio))
        return False

    print("")
    print("=" * 72)
    print("  CRUCE CUADRO 5-C (8 ramos) vs CUADRO 3 (Seguros Obligacionales / Responsabilidad)")
    print("  Páginas 25 (5 ramos), 26 (3 ramos + TOTAL)")
    print("=" * 72)
    print("")

    totales_c3 = _obtener_totales_obligacionales_cuadro3(pdf)
    if not totales_c3 or len(totales_c3) != 8:
        print("  [AVISO] No se pudieron obtener los 8 ramos del Cuadro 3.")
        return False

    total_oblig_c3 = sum(totales_c3)
    print("  CUADRO 3 – Total por ramo (Seguro Directo, Seguros Obligacionales):")
    for i in range(8):
        print("    {:2d}: {:>35s} = {:>12,.0f}".format(i + 1, RAMOS_SEG_OBLIGACIONALES[i][:35], totales_c3[i]))
    print("    TOTAL 8 ramos (Cuadro 3): {:>12,.0f}".format(total_oblig_c3))
    print("")

    listas_filas = []
    for pagina, n_cols in PAGINAS_5C:
        filas = _extraer_filas_5C_pagina(pdf, pagina, n_cols)
        listas_filas.append((pagina, n_cols, filas))
        print("  Página {}: {} filas con {} columnas.".format(pagina, len(filas), n_cols))

    n_emp = min(len(f[2]) for f in listas_filas)
    if n_emp == 0:
        print("  [ERROR] No se extrajeron filas.")
        return False

    if len(listas_filas[0][2]) >= 100:
        pag26_filas = listas_filas[1][2]
        sum_b0 = sum(pag26_filas[i][1][-1] for i in range(min(51, len(pag26_filas))))
        sum_b1 = sum(pag26_filas[i][1][-1] for i in range(51, min(102, len(pag26_filas))))
        if sum_b1 > sum_b0:
            listas_filas = [(p, c, f[51:102]) for p, c, f in listas_filas]
        else:
            listas_filas = [(p, c, f[:51]) for p, c, f in listas_filas]
        n_emp = min(len(f[2]) for f in listas_filas)

    sumas_ramos_5C = []
    _p25, n25, filas25 = listas_filas[0]
    for j in range(n25):
        sumas_ramos_5C.append(sum(filas25[i][1][j] for i in range(min(n_emp, len(filas25)))))
    _p26, n26, filas26 = listas_filas[1]
    for j in range(min(3, n26)):  # solo ramos 6-8, no TOTAL (col 3)
        sumas_ramos_5C.append(sum(filas26[i][1][j] for i in range(min(n_emp, len(filas26)))))
    sumas_ramos_5C = sumas_ramos_5C[:8]
    total_5C = sum(sumas_ramos_5C)

    print("")
    print("  CUADRO 5-C – Suma por ramo ({} empresas):".format(n_emp))
    for i in range(8):
        diff = sumas_ramos_5C[i] - totales_c3[i]
        print("    {:2d}: {:>35s}  5-C = {:>12,.0f}   C3 = {:>12,.0f}   Diff = {:>10,.0f}".format(
            i + 1, RAMOS_SEG_OBLIGACIONALES[i][:35], sumas_ramos_5C[i], totales_c3[i], diff))
    print("    TOTAL:                5-C = {:>12,.0f}   C3 = {:>12,.0f}   Diff = {:>10,.0f}".format(
        total_5C, total_oblig_c3, total_5C - total_oblig_c3))
    print("")

    tolerancia = max(1, total_oblig_c3 * 0.0001)
    ok_ramos = all(abs(sumas_ramos_5C[i] - totales_c3[i]) <= tolerancia for i in range(8))
    ok_total = abs(total_5C - total_oblig_c3) <= tolerancia

    if ok_ramos and ok_total:
        print("  Resultado: COINCIDE por ramo y en total con Cuadro 3 (Seguros Obligacionales).")
    else:
        print("  Resultado: NO COINCIDE en algún ramo o total.")
    print("")
    return ok_ramos and ok_total


def main():
    import argparse
    p = argparse.ArgumentParser(description="Cruce Cuadro 5-C (8 ramos) vs Cuadro 3")
    p.add_argument("--year", type=int, default=2023)
    p.add_argument("--pdf", type=Path, default=None)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year, pdf_path=args.pdf)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
