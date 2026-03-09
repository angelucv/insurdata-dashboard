"""
Arqueo inicial de los archivos XLSX convertidos con Adobe (en data/raw/pdf).
Verifica formatos, hojas, dimensiones y detecta bloques 'Empresa' para compilación.
Genera: indice/arqueo_xlsx_adobe.csv e indice/arqueo_xlsx_adobe_resumen.txt
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import DATA_RAW
from config.anuarios_paths import SEGURO_EN_CIFRAS_INDICE
from src.etl.anuarios_seguro_en_cifras import build_indice_fuentes, _year_from_anuario_path

RAW_PDF = DATA_RAW / "pdf"
SALIDA_CSV = SEGURO_EN_CIFRAS_INDICE / "arqueo_xlsx_adobe.csv"
SALIDA_TXT = SEGURO_EN_CIFRAS_INDICE / "arqueo_xlsx_adobe_resumen.txt"


def _anio_desde_nombre(nombre: str) -> int | None:
    m = re.search(r"(\d{4})", nombre)
    return int(m.group(1)) if m else None


def arqueo_archivo(path: Path) -> dict:
    """Inspecciona un XLSX y retorna dict con formato, hojas, dimensiones y bloques Empresa."""
    out = {
        "archivo": path.name,
        "ruta": str(path.relative_to(DATA_RAW)),
        "anio": _anio_desde_nombre(path.name),
        "existe": path.exists(),
        "hojas": "",
        "n_hojas": 0,
        "filas": 0,
        "columnas": 0,
        "n_bloques_empresa": 0,
        "celdas_numericas": 0,
        "observacion": "",
    }
    if not path.exists():
        out["observacion"] = "Archivo no encontrado"
        return out

    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        out["observacion"] = str(e)[:80]
        return out

    out["hojas"] = ",".join(xl.sheet_names)
    out["n_hojas"] = len(xl.sheet_names)

    # Hoja principal (Table 1 o la primera)
    sheet = "Table 1" if "Table 1" in xl.sheet_names else xl.sheet_names[0]
    try:
        df = pd.read_excel(path, sheet_name=sheet, header=None)
    except Exception as e:
        out["observacion"] = str(e)[:80]
        return out

    out["filas"], out["columnas"] = df.shape

    # Contar celdas numéricas
    n_num = 0
    for i in range(min(2000, len(df))):
        for j in range(min(80, len(df.columns))):
            try:
                v = df.iloc[i].iloc[j]
                if pd.notna(v) and str(v).strip():
                    float(v)
                    n_num += 1
            except (TypeError, ValueError):
                pass
    out["celdas_numericas"] = n_num

    # Buscar celdas con "Empresa" (cabecera de tabla)
    bloques = 0
    for i in range(len(df)):
        for j in range(min(20, len(df.columns))):
            cell = df.iloc[i].iloc[j]
            if pd.isna(cell):
                continue
            s = str(cell).strip().lower()
            if s == "empresa" or (s.startswith("empresa") and len(s) < 25 and "empresas de seguros" not in s):
                bloques += 1
    out["n_bloques_empresa"] = bloques

    if out["observacion"] == "" and out["n_bloques_empresa"] == 0 and out["filas"] > 100:
        out["observacion"] = "Sin cabecera 'Empresa' detectada; revisar estructura"
    elif out["observacion"] == "":
        out["observacion"] = "OK"

    return out


def main() -> None:
    build_indice_fuentes()
    SEGURO_EN_CIFRAS_INDICE.mkdir(parents=True, exist_ok=True)

    # Listar XLSX en data/raw/pdf que sean anuarios (seguro en cifras)
    archivos = []
    for p in sorted(RAW_PDF.glob("*.xlsx")):
        anio, _ = _year_from_anuario_path(p)
        if anio is not None:
            archivos.append(p)

    if not archivos:
        print("No se encontraron XLSX de anuario en", RAW_PDF)
        sys.exit(1)

    print("Arqueo de", len(archivos), "archivos XLSX (Adobe) en", RAW_PDF)
    print()

    registros = []
    for p in archivos:
        r = arqueo_archivo(p)
        registros.append(r)
        print(r["archivo"], "|", r["n_hojas"], "hojas |", r["filas"], "x", r["columnas"],
              "| bloques Empresa:", r["n_bloques_empresa"], "| nums:", r["celdas_numericas"], "|", r["observacion"])

    df = pd.DataFrame(registros)
    df.to_csv(SALIDA_CSV, index=False, encoding="utf-8-sig")
    print()
    print("Guardado:", SALIDA_CSV)

    with open(SALIDA_TXT, "w", encoding="utf-8") as f:
        f.write("=== Arqueo XLSX convertidos con Adobe (Seguro en Cifras) ===\n\n")
        f.write("Formato: una hoja 'Table 1' por archivo; rejilla que refleja el PDF.\n")
        f.write("Campos verificados: hojas, filas x columnas, bloques con cabecera 'Empresa', celdas numéricas.\n\n")
        f.write(df.to_string() + "\n")
    print("Resumen:", SALIDA_TXT)


if __name__ == "__main__":
    main()
