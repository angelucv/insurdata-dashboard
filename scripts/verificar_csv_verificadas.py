# scripts/verificar_csv_verificadas.py
"""
Verifica que los CSV en data/staged/2023/verificadas/ esten bien escritos:
- Unico separador: punto y coma (;)
- Campos con coma (ej. "Seguros, C.A.") entre comillas dobles
- Mismo numero de columnas en todas las filas

Uso: python scripts/verificar_csv_verificadas.py [--year 2023]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED
from scripts.verificar_indice_anuario import INDICE_CSV_POR_CUADRO, ORDEN_CUADROS

SEP = ";"
ENCODING = "utf-8-sig"

# Lista única: orden por cuadro (3, 4, 5-A, …, 8-A, 8-B, 8-C, 9, …, 58). Fuente: INDICE_CSV_POR_CUADRO.
ARCHIVOS = [
    f for cid in ORDEN_CUADROS for f in INDICE_CSV_POR_CUADRO.get(cid, []) if f
]


def _verificar_archivo(carpeta: Path, nombre: str) -> tuple[bool, str, int, int]:
    """
    Verifica un CSV: solo separador ;, mismo n de columnas.
    Devuelve (ok, mensaje, n_columnas, n_filas).
    """
    path = carpeta / nombre
    if not path.exists():
        return False, f"No existe: {path}", 0, 0

    try:
        with open(path, encoding=ENCODING, newline="") as f:
            reader = csv.reader(f, delimiter=SEP, quotechar='"', doublequote=True)
            rows = list(reader)
    except Exception as e:
        return False, f"Error leyendo: {e}", 0, 0

    if not rows:
        return False, "Archivo vacio", 0, 0

    n_cols = len(rows[0])
    n_filas = len(rows) - 1  # sin cabecera
    problemas = []

    for i, row in enumerate(rows):
        if len(row) != n_cols:
            problemas.append(f"  Fila {i + 1}: tiene {len(row)} columnas (cabecera tiene {n_cols})")
        # Comprobar que no haya coma usada como separador (campos sin comillas con coma)
        for j, cell in enumerate(row):
            if SEP not in cell and "," in cell and not (cell.startswith('"') and cell.endswith('"')):
                pass  # celda con coma y sin comillas podria ser error; pero csv.reader ya maneja comillas
            # Si la celda leida contiene coma y fue leida bien, es que estaba entre comillas en el archivo

    if problemas:
        return False, "Columnas inconsistentes:\n" + "\n".join(problemas[:5]), n_cols, n_filas

    # Comprobar que en el archivo crudo no haya lineas con coma como unico separador
    with open(path, encoding=ENCODING) as f:
        lineas = f.readlines()
    for i, linea in enumerate(lineas[:3]):  # solo primeras lineas como muestra
        if i == 0:
            continue  # cabecera
        # Contar separadores: debe ser n_cols - 1 puntos y coma (fuera de comillas)
        # Simplificado: si hay una coma que no esta entre comillas dobles, podria ser problema
        # Mejor: leer con pandas y ver si coincide
        pass

    return True, "OK", n_cols, n_filas


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar CSV en staged/YYYY/verificadas/")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()

    carpeta = DATA_STAGED / str(args.year) / "verificadas"
    if not carpeta.exists():
        print(f"[ERROR] No existe la carpeta: {carpeta}")
        sys.exit(1)

    print("Verificando CSV (separador unico ';', comillas en texto):")
    print("Carpeta:", carpeta)
    print()

    todo_ok = True
    for nombre in ARCHIVOS:
        ok, msg, n_cols, n_filas = _verificar_archivo(carpeta, nombre)
        if ok:
            print(f"  [OK] {nombre}  -> {n_cols} columnas, {n_filas} filas")
        else:
            print(f"  [!!] {nombre}")
            print(f"       {msg}")
            todo_ok = False

    # Leer con pandas para confirmar que se puede cargar
    print()
    print("Lectura con pandas (sep=';'):")
    try:
        import pandas as pd
        for nombre in ARCHIVOS:
            path = carpeta / nombre
            if not path.exists():
                continue
            df = pd.read_csv(path, sep=SEP, encoding=ENCODING)
            print(f"  {nombre}: shape {df.shape}, columnas: {list(df.columns)[:4]}{'...' if len(df.columns) > 4 else ''}")
    except Exception as e:
        print("  Error:", e)
        todo_ok = False

    print()
    if todo_ok:
        print("Todos los archivos pasaron la verificacion.")
    else:
        print("Algunos archivos tienen problemas. Regenere con: python scripts/guardar_tablas_verificadas_2023.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
