#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo sencillo: extracción PDF -> CSV.

Se asume que el PDF está en el mismo directorio que este script.
Ejecutar desde cualquier sitio; el script usa la carpeta donde está guardado.

  cd docs
  python ejemplo_flujo_extraccion_anuario_pdf.py

O desde la raíz:
  python docs/ejemplo_flujo_extraccion_anuario_pdf.py

Requisitos: pip install pdfplumber pandas
"""

import csv
import sys
from pathlib import Path

# Directorio donde está este script (y donde debe estar el PDF)
DIR = Path(__file__).resolve().parent

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Nombre del PDF esperado en el mismo directorio (o el primer .pdf que encuentre)
NOMBRE_PDF = "seguros-en-cifra-2023.pdf"
PAGINA_CUADRO_3 = 18  # número de página del Cuadro 3 en el anuario
SEP = ";"
SALIDA_CSV = "ejemplo_salida.csv"


def main():
    pdf_path = DIR / NOMBRE_PDF
    if not pdf_path.exists():
        # Buscar cualquier PDF en el mismo directorio
        pdfs = list(DIR.glob("*.pdf"))
        if pdfs:
            pdf_path = pdfs[0]
        else:
            print(f"No hay PDF en {DIR}. Coloca aquí {NOMBRE_PDF} (o cualquier .pdf).")
            return

    print("[PASO 1] PDF en el mismo directorio que el script")
    print("-" * 50)
    print(f"  Directorio: {DIR}")
    print(f"  PDF:        {pdf_path.name}")
    print()

    print("[PASO 2] Abrir PDF y extraer tabla de una página")
    print("-" * 50)
    try:
        import pdfplumber
        import pandas as pd
    except ImportError:
        print("  Instala: pip install pdfplumber pandas")
        return

    with pdfplumber.open(pdf_path) as doc:
        n_pag = len(doc.pages)
        print(f"  Páginas totales: {n_pag}")
        if PAGINA_CUADRO_3 > n_pag:
            print(f"  La página {PAGINA_CUADRO_3} no existe. Usando página 1.")
            pagina = 0
        else:
            pagina = PAGINA_CUADRO_3 - 1
        tablas = doc.pages[pagina].extract_tables()
        if not tablas or not tablas[0]:
            print("  No se encontraron tablas en esta página.")
            return
        filas = tablas[0]
        columnas = filas[0]
        datos = filas[1:]
        print(f"  Página usada: {pagina + 1}")
        print(f"  Columnas: {columnas}")
        print(f"  Filas de datos: {len(datos)}")
    print()

    print("[PASO 3] Escribir CSV (separador ; , texto entre comillas)")
    print("-" * 50)
    df = pd.DataFrame(datos, columns=columnas)
    out_path = DIR / SALIDA_CSV
    df.to_csv(
        out_path,
        index=False,
        encoding="utf-8-sig",
        sep=SEP,
        quoting=csv.QUOTE_NONNUMERIC,
    )
    print(f"  Guardado: {out_path}")
    print()

    print("[PASO 4] Leer CSV y mostrar resultado")
    print("-" * 50)
    df2 = pd.read_csv(out_path, sep=SEP, encoding="utf-8-sig")
    print(f"  Filas: {len(df2)}, Columnas: {len(df2.columns)}")
    print(f"  Primeras filas:")
    print(df2.head().to_string(index=False))
    print()
    print("Listo.")


if __name__ == "__main__":
    main()
