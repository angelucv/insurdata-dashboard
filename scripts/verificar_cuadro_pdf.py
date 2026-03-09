# scripts/verificar_cuadro_pdf.py
"""
Verificación secuencial tabla a tabla del PDF anuario.
Extrae UN cuadro (por defecto el 4), muestra el resultado en consola para validar
que la extracción replica correctamente antes de incluir datos en lo compilado.

Uso:
  python scripts/verificar_cuadro_pdf.py --cuadro 4 [--year 2023] [--pdf ruta/al.pdf]
  python scripts/verificar_cuadro_pdf.py --cuadro 5-A --year 2023
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Consola en UTF-8 en Windows para que los acentos se muestren bien
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd

from config.settings import DATA_RAW, DATA_AUDIT_BY_SOURCE
from src.extraction.pdf_extractor import PDFTableExtractor

# Caracter de reemplazo Unicode (cuando falla la decodificacion)
_REPL = "\uFFFD"

# Reemplazos para corregir caracteres mal decodificados (PDF Latin-1/CP1252 leido como UTF-8)
_REPLACES_ENCODING = [
    ("Caron" + _REPL, "Caroní"),
    (_REPL + "vila", "Ávila"),
    ("Adri" + _REPL + "tica", "Adriática"),
    ("Constituci" + _REPL + "n", "Constitución"),
    ("Oce" + _REPL + "nica", "Oceánica"),
    ("Pir" + _REPL + "mide", "Pirámide"),
    ("V" + _REPL + "rtice", "Vértice"),
]


def _fix_encoding_text(s: str) -> str:
    """Corrige caracteres mal decodificados (�) en texto extraido del PDF."""
    if not s or not isinstance(s, str):
        return s
    for wrong, right in _REPLACES_ENCODING:
        s = s.replace(wrong, right)
    return s


def _parse_num_european(s: str) -> float:
    """Convierte numero en formato europeo (1.234,56) a float."""
    if not s or not isinstance(s, str):
        return 0.0
    s = s.strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _ultimo_numero_de_linea(linea: str) -> float | None:
    """Extrae el ultimo numero de una linea (ej. total de fila). None si no hay."""
    # Buscar numeros: enteros 122, o con decimal 24.976.109, 39,89
    partes = linea.split()
    for i in range(len(partes) - 1, -1, -1):
        p = partes[i].replace(".", "").replace(",", ".")
        try:
            return float(p)
        except ValueError:
            continue
    return None


def _ultimo_numero_en_fila(row: pd.Series) -> float | None:
    """De una fila (serie), concatena todo el texto y extrae el ultimo numero (ej. total)."""
    texto = " ".join(str(v) for v in row.dropna().astype(str))
    return _ultimo_numero_de_linea(texto)


def _extraer_filas_y_totales(tables: list[pd.DataFrame]) -> tuple[list[str], list[float], float | None]:
    """
    De las tablas extraidas (primera columna con texto con \\n), obtiene:
    - lineas: lista de lineas mostrables
    - totales_fila: total por cada fila de dato (excl. cabecera y TOTAL)
    - total_cuadro: valor del renglon TOTAL (ultimo numero de esa linea o de la fila)
    """
    lineas = []
    totales_fila = []
    total_cuadro = None
    linea_anterior_era_total = False
    for df in tables:
        col0 = df.iloc[:, 0] if len(df.columns) > 0 else pd.Series(dtype=object)
        for idx, row in df.iterrows():
            v0 = row.iloc[0]
            if pd.isna(v0):
                continue
            # Si la fila entera tiene "TOTAL" (en primera columna), el valor puede estar en otras columnas
            v0_str = str(v0).strip()
            if v0_str.upper().startswith("TOTAL") and "\n" not in v0_str:
                num_fila = _ultimo_numero_en_fila(row)
                if num_fila is not None:
                    total_cuadro = num_fila
                lineas.append(_fix_encoding_text(v0_str))
                linea_anterior_era_total = not (num_fila is not None)
                continue
            # Si en esta fila hay varias lineas (celda con \n), al terminar de procesar si quedo pendiente TOTAL, buscar en resto de columnas
            lineas_de_v0 = str(v0).split("\n")
            for linea in lineas_de_v0:
                linea = linea.strip()
                if not linea:
                    continue
                if linea.startswith("Fuente:"):
                    continue
                linea = _fix_encoding_text(linea)
                lineas.append(linea)
                num = _ultimo_numero_de_linea(linea)
                if linea.upper().startswith("TOTAL"):
                    if num is not None:
                        total_cuadro = num
                    else:
                        linea_anterior_era_total = True
                elif linea_anterior_era_total and num is not None:
                    total_cuadro = num
                    linea_anterior_era_total = False
                elif linea.lower().startswith("nombre") or ("Hospitalizaci" in linea and "%" in linea) or (linea.startswith("Individual") or "Individual" in linea[:20]):
                    linea_anterior_era_total = False
                    continue
                else:
                    linea_anterior_era_total = False
                    if num is not None:
                        totales_fila.append(num)
            # Si tras procesar la celda quedo pendiente TOTAL, el total puede estar en otras columnas de esta fila
            if linea_anterior_era_total:
                num_fila = _ultimo_numero_en_fila(row)
                if num_fila is not None:
                    total_cuadro = num_fila
                linea_anterior_era_total = False
    return lineas, totales_fila, total_cuadro


def _normalize_cuadro_arg(s: str) -> str:
    """Acepta '4', '5-A', '5A' y devuelve formato estándar para búsqueda (ej. 4, 5-A)."""
    s = str(s).strip().upper().replace(" ", "")
    if re.match(r"^\d+$", s):
        return s
    if re.match(r"^\d+[A-F]$", s):
        return s[0:-1] + "-" + s[-1]  # 5A -> 5-A
    if re.match(r"^\d+-[A-F]$", s):
        return s
    return s


def get_indice_cuadros(anio: int) -> dict[str, dict]:
    """
    Lee el índice desde by_source/seguros-en-cifra-{anio}_tables.csv.
    Devuelve dict: cuadro_num -> {pagina, pagina_camelot, titulo, seccion}.
    Incluye todos los cuadros (1, 2, 3, 4, 5-A, ...) para búsqueda.
    """
    csv_path = DATA_AUDIT_BY_SOURCE / f"seguros-en-cifra-{anio}_tables.csv"
    if not csv_path.exists():
        return {}
    try:
        df = pd.read_csv(csv_path, header=None, encoding="utf-8", on_bad_lines="skip")
    except Exception:
        return {}
    out = {}
    for _, row in df.iterrows():
        if len(row) < 4:
            continue
        num = row.iloc[0]
        seccion = row.iloc[1]
        titulo = row.iloc[2]
        pagina = row.iloc[3]
        if pd.isna(num) or pd.isna(pagina):
            continue
        num_str = str(num).strip()
        pag_str = str(pagina).strip()
        if not re.match(r"^\d+(-\d+)?$", pag_str):
            continue
        # Cualquier número de cuadro: 1, 2, 3, 4, 5-A, etc.
        if not num_str or not re.match(r"^\d+([-]?[A-Fa-f])?$", num_str):
            continue
        # Normalizar 5A -> 5-A para clave
        key = _normalize_cuadro_arg(num_str) if "-" not in num_str and len(num_str) > 1 and num_str[-1].isalpha() else num_str
        if key in out:
            continue
        out[key] = {
            "pagina": pag_str,
            "pagina_camelot": pag_str,
            "titulo": (str(titulo).strip() if pd.notna(titulo) else "") or "",
            "seccion": (str(seccion).strip() if pd.notna(seccion) else "") or "",
        }
    return out


def find_pdf(anio: int, pdf_path: Path | None) -> Path | None:
    """Resuelve la ruta del PDF del anuario."""
    if pdf_path and pdf_path.exists():
        return pdf_path
    for base in [DATA_RAW / "pdf", DATA_RAW]:
        p = base / f"seguros-en-cifra-{anio}.pdf"
        if p.exists():
            return p
    return None


def extraer_y_mostrar_cuadro(
    cuadro_num: str,
    anio: int = 2023,
    pdf_path: Path | None = None,
) -> bool:
    """
    Extrae un solo cuadro del PDF y lo muestra en consola.
    Devuelve True si hubo datos extraídos, False si error o sin datos.
    """
    indice = get_indice_cuadros(anio)
    if not indice:
        print("[ERROR] No se encontro el indice. Ejecuta antes el pipeline que genera")
        print("        data/audit/by_source/seguros-en-cifra-{}_tables.csv".format(anio))
        return False

    # Buscar por clave exacta o normalizada
    clave = _normalize_cuadro_arg(cuadro_num)
    info = indice.get(clave) or indice.get(cuadro_num) or indice.get(cuadro_num.replace("-", ""))
    if not info:
        print("[ERROR] Cuadro '{}' no esta en el indice. Cuadros disponibles: {}".format(
            cuadro_num, ", ".join(sorted(indice.keys(), key=lambda x: (len(x), x))[:20])
        ))
        if len(indice) > 20:
            print("        ... y {} mas.".format(len(indice) - 20))
        return False

    pdf = find_pdf(anio, pdf_path)
    if not pdf:
        print("[ERROR] No se encontro el PDF del anuario {}.".format(anio))
        print("        Coloca seguros-en-cifra-{}.pdf en data/raw/ o data/raw/pdf/".format(anio))
        return False

    pag = info["pagina_camelot"]
    titulo = info["titulo"]
    seccion = info["seccion"]

    print("")
    print("=" * 72)
    print("  CUADRO Nº {}  (pagina {})".format(cuadro_num, pag))
    print("  Seccion: {}".format(seccion))
    print("  Titulo:  {}".format(titulo[:70] + "..." if len(titulo) > 70 else titulo))
    print("=" * 72)
    print("  PDF: {}".format(pdf))
    print("  Extrayendo pagina(s) {}...".format(pag))
    print("")

    extractor = PDFTableExtractor()
    try:
        tables = extractor.extract_with_camelot(pdf, pages=pag)
    except Exception as e:
        print("[ERROR] Fallo al extraer: {}".format(e))
        return False

    if not tables:
        print("  [AVISO] No se extrajo ninguna tabla (Camelot). Intentando pdfplumber...")
        try:
            import pdfplumber
            with pdfplumber.open(pdf) as doc:
                page_nums = pag.split("-")
                p0 = int(page_nums[0])
                p1 = int(page_nums[1]) if len(page_nums) > 1 else p0
                for p in range(p0, p1 + 1):
                    if p <= len(doc.pages):
                        for t in doc.pages[p - 1].extract_tables():
                            if t:
                                tables.append(pd.DataFrame(t[1:], columns=t[0]))
        except Exception as e2:
            print("  [ERROR] pdfplumber: {}".format(e2))
        if not tables:
            print("  No hay datos extraidos para este cuadro.")
            return False

    # Corregir encoding (acentos) en celdas que tengan el caracter de reemplazo
    for df in tables:
        for c in df.columns:
            for i in df.index:
                v = df.at[i, c]
                if isinstance(v, str) and _REPL in v:
                    df.at[i, c] = _fix_encoding_text(v)

    # Extraer lineas y totales para mostrar tabla y verificar suma vs TOTAL del cuadro
    lineas, totales_fila, total_cuadro = _extraer_filas_y_totales(tables)
    # En cuadros de varias paginas (varias tablas) usar solo la primera tabla para la suma
    if len(tables) > 1:
        _, totales_primera_tabla, _ = _extraer_filas_y_totales(tables[:1])
        totales_para_suma = totales_primera_tabla
    else:
        totales_para_suma = totales_fila

    # Contar empresas (filas que parecen nombre de empresa, excl. TOTAL y cabeceras)
    def _es_fila_empresa(lin):
        if not lin or lin.strip().upper() in ("TOTAL", "NOMBRE EMPRESA", "EMPRESA"):
            return False
        s = lin.strip()
        if s.startswith("Fuente:") or (s.startswith("Nombre") and "Empresa" in s[:20]):
            return False
        return ("Seguros" in s or "C.A." in s or "S.A." in s) and any(c.isdigit() for c in s)
    n_empresas = sum(1 for lin in lineas if _es_fila_empresa(lin))

    # Mostrar tabla en consola
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 200)
    pd.set_option("display.max_colwidth", 35)

    def _clean_cell(x):
        if pd.isna(x) or x is None:
            return ""
        s = str(x).strip().replace("\r\n", " ").replace("\n", " ")
        return s[:60] + "..." if len(s) > 60 else s

    # Nombres de campos tipicos para cuadro "Primas netas por ramo/empresa" (Cuadro 4)
    CAMPOS_PRIMAS_RAMO_EMPRESA_DISPLAY = [
        "Nombre Empresa",
        "Hospitalización Individual", "% (Hosp. Ind.)",
        "Hospitalización Colectivo", "% (Hosp. Col.)",
        "Automóvil Casco", "% (Auto)",
        "Resto de Ramos", "% (Resto)",
        "TOTAL",
    ]
    # Cuadro 5-A: Seguros de Personas – pag 20: 5 ramos, pag 21: 4 ramos + TOTAL (9 ramos = Cuadro 3)
    CAMPOS_5A_PAG1 = [
        "Nombre Empresa",
        "Vida Individual", "Vida Desgravamen Hipot.", "Rentas Vitalicias", "Vida Colectivo", "Accid. Pers. Individual",
    ]
    CAMPOS_5A_PAG2 = [
        "Nombre Empresa",
        "Accid. Pers. Colectivo", "Hospitalizacion Ind.", "Hospitalizacion Col.", "Seguros Funerarios",
        "TOTAL",
    ]
    CAMPOS_5A_DISPLAY = [
        "Nombre Empresa",
        "Rama 1 (Vida Ind.)", "Rama 2", "Rama 3", "Rama 4", "Rama 5",
        "Rama 6", "Rama 7", "Rama 8", "Rama 9", "TOTAL",
    ]
    # Total esperado Cuadro 3 "SEGURO DE PERSONAS" para cruce con 5-A
    TOTAL_CUADRO_3_SEG_PERSONAS = 18_371_411

    for i, df in enumerate(tables):
        n_filas, n_cols = len(df), len(df.columns)
        print("  --- Tabla {} ({} filas x {} columnas) ---".format(i + 1, n_filas, n_cols))
        # Nombres de columnas: usar los del DataFrame o inferir desde la primera fila de contenido
        col0 = df.iloc[:, 0] if n_cols else pd.Series(dtype=object)
        tiene_celdas_con_newline = len(col0) > 0 and col0.astype(str).str.contains("\n", na=False).any()
        es_5A = str(cuadro_num).replace("-", "").upper() in ("5A", "5-A")
        if tiene_celdas_con_newline and es_5A and n_cols >= 5:
            nombres_campos = (CAMPOS_5A_DISPLAY + ["(col {:d})".format(k) for k in range(6, 15)])[:n_cols]
            print("  COLUMNAS (CAMPOS) – Cuadro 5-A Seguros de Personas por ramo/empresa:")
            for k, nom in enumerate(nombres_campos):
                print("    [{:2d}] {}".format(k, nom))
        elif tiene_celdas_con_newline and lineas and (lineas[0].strip().lower().startswith("nombre") or lineas[0].strip().lower().startswith("empresa")):
            nombres_campos = CAMPOS_PRIMAS_RAMO_EMPRESA_DISPLAY
            print("  COLUMNAS (CAMPOS) – interpretados para uso de la informacion:")
            for k, nom in enumerate(nombres_campos):
                print("    [{:2d}] {}".format(k, nom))
        else:
            print("  COLUMNAS (CAMPOS):")
            for k, col in enumerate(df.columns):
                col_str = _fix_encoding_text(str(col).replace("\n", " ").strip())
                if not col_str or col_str == "None":
                    col_str = "(columna {:d})".format(k)
                else:
                    col_str = col_str[:70] + "..." if len(col_str) > 70 else col_str
                print("    [{:2d}] {}".format(k, col_str))
        if i == 0:
            if len(tables) > 1 and n_empresas > 50:
                print("  CANTIDAD DE EMPRESAS: {} filas de dato (aprox. {} empresas unicas, {} bloques/paginas)".format(
                    n_empresas, n_empresas // len(tables), len(tables)))
            else:
                print("  CANTIDAD DE EMPRESAS (filas de dato): {}".format(n_empresas))
        print("")
        if tiene_celdas_con_newline:
            if es_5A:
                print("  FILAS (datos) – orden: Empresa, Rama 1, Rama 2, Rama 3, Rama 4, TOTAL:")
            else:
                print("  FILAS (datos) – orden: Empresa, Hosp.Ind, %, Hosp.Col, %, Auto, %, Resto, %, TOTAL:")
            for j, lin in enumerate(lineas[:70], 1):
                print("    {:3d} | {}".format(j, lin[:90] + ("..." if len(lin) > 90 else "")))
            if len(lineas) > 70:
                print("    ... ({} lineas mas)".format(len(lineas) - 70))
        else:
            print("  DATOS (con cabecera de columnas):")
            df_show = df.map(_clean_cell) if hasattr(df, "map") else df.applymap(_clean_cell)
            print(df_show.to_string(index=False))
        print("")

    # Verificacion: suma de totales por fila vs TOTAL del cuadro
    print("  " + "=" * 60)
    print("  VERIFICACION: Suma de datos extraidos vs TOTAL del cuadro")
    print("  " + "=" * 60)
    suma_extraida = sum(totales_para_suma)
    n_filas_para_suma = len(totales_para_suma)
    if len(tables) > 1:
        print("  (Cuadro en {} paginas; suma sobre primera tabla, {} filas)".format(len(tables), n_filas_para_suma))
    if total_cuadro is not None and n_filas_para_suma > 0:
        diff = abs(suma_extraida - total_cuadro)
        tolerancia = max(1.0, total_cuadro * 0.0001)
        ok = diff <= tolerancia
        print("  Suma de totales por fila ({} filas): {:,.2f}".format(n_filas_para_suma, suma_extraida))
        print("  TOTAL del cuadro (renglon TOTAL):    {:,.2f}".format(total_cuadro))
        print("  Diferencia:                          {:,.2f}".format(suma_extraida - total_cuadro))
        if ok:
            print("  Resultado: COINCIDE (suma = total del cuadro)")
        else:
            print("  Resultado: NO COINCIDE (revisar extraccion o redondeos)")
        # Cruce con Cuadro 3 cuando aplique (5-A = Seguros de Personas)
        if str(cuadro_num).replace("-", "").upper() in ("5A", "5-A"):
            if abs(total_cuadro - TOTAL_CUADRO_3_SEG_PERSONAS) <= 1:
                print("  Cruce con Cuadro 3: TOTAL coincide con Seguros de Personas (18.371.411) [TOTAL del documento verificado]")
                print("  Cruce por ramo (9 ramos: pag 20 = 5 ramos, pag 21 = 4 ramos + TOTAL): python scripts/verificar_cruce_5A_cuadro3.py")
                if not ok:
                    print("  Nota: Suma por filas puede no coincidir si el cuadro tiene 2 bloques (2 pag.); el TOTAL del renglon es la referencia.")
            else:
                print("  Cruce con Cuadro 3: TOTAL ({:,.0f}) vs Seguros de Personas (18.371.411) – revisar".format(total_cuadro))
    else:
        print("  No se pudo obtener TOTAL del cuadro o no hay filas con totales.")
        if total_cuadro is None:
            print("  (No se encontro renglon 'TOTAL' con numero.)")
        print("  Suma de totales por fila: {:,.2f} ({} filas)".format(suma_extraida, n_filas_para_suma))
    print("")

    print("  Total: {} tabla(s), {} filas en total.".format(
        len(tables), sum(len(t) for t in tables)
    ))
    print("")
    return True


def main():
    import argparse
    p = argparse.ArgumentParser(description="Verificar extraccion de un cuadro del PDF anuario (consola)")
    p.add_argument("--cuadro", default="4", help="Numero de cuadro (ej. 4, 5-A, 6)")
    p.add_argument("--year", type=int, default=2023, help="Anio del anuario")
    p.add_argument("--pdf", type=Path, default=None, help="Ruta al PDF (opcional)")
    args = p.parse_args()

    ok = extraer_y_mostrar_cuadro(args.cuadro, anio=args.year, pdf_path=args.pdf)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
