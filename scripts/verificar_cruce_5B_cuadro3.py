# scripts/verificar_cruce_5B_cuadro3.py
"""
Verifica que el Cuadro 5-B (Seguros Patrimoniales por ramo/empresa, páginas 22-24)
coincida por ramo con el Cuadro 3 (Primas netas por ramo - 16 ramos patrimoniales).
- Página 22: 6 ramos (columnas).
- Página 23: 5 ramos.
- Página 24: 5 ramos + TOTAL.
Total 16 ramos en el mismo orden que en Cuadro 3 (SEGUROS PATRIMONIALES).
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

# Los 16 ramos de Seguros Patrimoniales en el orden del Cuadro 3 (col. SEGURO DIRECTO)
RAMOS_SEG_PATRIMONIALES = [
    "Incendio",
    "Terremoto",
    "Robo",
    "Transporte",
    "Ramos Técnicos",
    "Petroleros",
    "Combinados",
    "Lucro cesante",
    "Automóvil casco",
    "Aeronaves",
    "Naves",
    "Agrícola",
    "Pecuario",
    "Bancarios",
    "Joyería",
    "Diversos",
]

# Distribución por página: (número_página, cantidad_columnas_numericas)
# 5+6+5 = 16 ramos; en pág 24 la 6ª columna es TOTAL (solo 5 ramos en p24)
PAGINAS_5B = [(22, 5), (23, 6), (24, 6)]


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


def _obtener_totales_patrimoniales_cuadro3(pdf_path: Path) -> list[float] | None:
    """
    Extrae Cuadro 3 (pág 18) y devuelve los 16 totales 'Seguro Directo' (índice 0 de nums)
    de los ramos Seguros Patrimoniales, parseando por líneas como en guardar_cuadro_3.
    """
    tablas = _extraer_tabla_pagina(pdf_path, 18)
    if not tablas:
        return None
    todas_filas = []  # (nombre_ramo, [seg_directo, reaseguro, total, %])
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
    # Buscar "SEGUROS PATRIMONIALES" y tomar los siguientes 16 ramos (columna Seguro Directo = nums[0])
    dieciseis = []
    i = 0
    while i < len(todas_filas):
        nombre, nums = todas_filas[i]
        if "SEGUROS PATRIMONIALES" in nombre.upper():
            i += 1
            for j in range(16):
                if i + j >= len(todas_filas):
                    break
                _, n = todas_filas[i + j]
                dieciseis.append(n[0])
            return dieciseis[:16] if len(dieciseis) == 16 else None
        i += 1
    return None


def _extraer_filas_5B_pagina(pdf_path: Path, pagina: int, n_columnas: int) -> list[tuple[str, list[float]]]:
    """Extrae filas (nombre_empresa, lista_numeros) de una página del Cuadro 5-B."""
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
    print("  CRUCE CUADRO 5-B (16 ramos) vs CUADRO 3 (Seguros Patrimoniales)")
    print("  Páginas 22 (5 ramos), 23 (6 ramos), 24 (5 ramos + TOTAL)")
    print("=" * 72)
    print("")

    # 1) Totales por ramo desde Cuadro 3 (16 ramos patrimoniales)
    totales_c3 = _obtener_totales_patrimoniales_cuadro3(pdf)
    if not totales_c3 or len(totales_c3) != 16:
        print("  [AVISO] No se pudieron obtener los 16 ramos del Cuadro 3.")
        return False

    total_patrimoniales_c3 = sum(totales_c3)
    print("  CUADRO 3 – Total por ramo (Seguro Directo, Seguros Patrimoniales):")
    for i in range(16):
        print("    {:2d}: {:>22s} = {:>12,.0f}".format(i + 1, RAMOS_SEG_PATRIMONIALES[i][:22], totales_c3[i]))
    print("    TOTAL 16 ramos (Cuadro 3): {:>12,.0f}".format(total_patrimoniales_c3))
    print("")

    # 2) Extraer cada página del 5-B
    listas_filas = []
    for pagina, n_cols in PAGINAS_5B:
        filas = _extraer_filas_5B_pagina(pdf, pagina, n_cols)
        listas_filas.append((pagina, n_cols, filas))
        print("  Página {}: {} filas con {} columnas.".format(pagina, len(filas), n_cols))

    # Elegir bloque de empresas (si hay dos bloques por página como en 5-A)
    n_emp = min(len(f[2]) for f in listas_filas)
    if n_emp == 0:
        print("  [ERROR] No se extrajeron filas.")
        return False

    # Si hay muchas filas (dos bloques), tomar el bloque con total alto
    if len(listas_filas[0][2]) >= 100:
        # Página 24 columna 1 (primer ramo de esa página) o última col (TOTAL) para decidir bloque
        pag24_filas = listas_filas[2][2]
        sum_b0 = sum(pag24_filas[i][1][-1] for i in range(min(51, len(pag24_filas))))
        sum_b1 = sum(pag24_filas[i][1][-1] for i in range(51, min(102, len(pag24_filas))))
        if sum_b1 > sum_b0:
            listas_filas = [
                (p, c, f[51:102]) for p, c, f in listas_filas
            ]
        else:
            listas_filas = [
                (p, c, f[:51]) for p, c, f in listas_filas
            ]
        n_emp = min(len(f[2]) for f in listas_filas)

    # 3) Sumas por ramo: p22 cols 0-4 (5), p23 cols 0-5 (6), p24 cols 0-4 (5; col 5 = TOTAL)
    sumas_ramos_5B = []
    for pagina, n_cols, filas in listas_filas:
        for j in range(n_cols):
            if pagina == 24 and j == 5:
                continue  # columna TOTAL
            sumas_ramos_5B.append(sum(filas[i][1][j] for i in range(min(n_emp, len(filas)))))
    sumas_ramos_5B = sumas_ramos_5B[:16]
    total_5B = sum(sumas_ramos_5B)

    print("")
    print("  CUADRO 5-B – Suma por ramo ({} empresas):".format(n_emp))
    for i in range(16):
        diff = sumas_ramos_5B[i] - totales_c3[i]
        print("    {:2d}: {:>22s}  5-B = {:>12,.0f}   C3 = {:>12,.0f}   Diff = {:>10,.0f}".format(
            i + 1, RAMOS_SEG_PATRIMONIALES[i][:22], sumas_ramos_5B[i], totales_c3[i], diff))
    print("    TOTAL:                5-B = {:>12,.0f}   C3 = {:>12,.0f}   Diff = {:>10,.0f}".format(
        total_5B, total_patrimoniales_c3, total_5B - total_patrimoniales_c3))
    print("")

    tolerancia = max(1, total_patrimoniales_c3 * 0.0001)
    ok_ramos = all(abs(sumas_ramos_5B[i] - totales_c3[i]) <= tolerancia for i in range(16))
    ok_total = abs(total_5B - total_patrimoniales_c3) <= tolerancia

    if ok_ramos and ok_total:
        print("  Resultado: COINCIDE por ramo y en total con Cuadro 3 (Seguros Patrimoniales).")
    else:
        print("  Resultado: NO COINCIDE en algún ramo o total (revisar bloques o orden de columnas).")
    print("")
    return ok_ramos and ok_total


def main():
    import argparse
    p = argparse.ArgumentParser(description="Cruce Cuadro 5-B (16 ramos) vs Cuadro 3")
    p.add_argument("--year", type=int, default=2023)
    p.add_argument("--pdf", type=Path, default=None)
    args = p.parse_args()
    ok = run_verificacion(anio=args.year, pdf_path=args.pdf)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
