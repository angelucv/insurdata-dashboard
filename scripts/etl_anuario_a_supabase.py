# scripts/etl_anuario_a_supabase.py
"""
ETL mínimo: carga datos del anuario "Seguro en Cifras" desde CSV (verificadas) a Supabase (schema anuario).
Carga balances_condensados y listados_empresas para el año indicado. Idempotente: borra datos del año antes de insertar.

Requisitos: 001, 002, 003 y 004 ejecutados en Supabase; schema anuario expuesto en API.
Uso: python scripts/etl_anuario_a_supabase.py [--year 2023]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Asegurar que .env se cargue desde la raíz del proyecto
import os
_env = ROOT / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

from config.settings import DATA_STAGED, SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY

SEP = ";"
ENCODING = "utf-8-sig"

# Cuadros → archivo CSV (un archivo por cuadro para estas tablas)
BALANCES_CONDENSADOS_CSV = {
    "24": "cuadro_24_balance_condensado.csv",
    "40": "cuadro_40_balance_condensado_reaseguros.csv",
    "47": "cuadro_47_balance_condensado_financiadoras_primas.csv",
    "54": "cuadro_54_balance_condensado_medicina_prepagada.csv",
}
LISTADOS_EMPRESAS_CSV = {
    "1": "cuadro_01_empresas_seguro_autorizadas.csv",
    "39": "cuadro_39_empresas_reaseguro_autorizadas.csv",
    "46": "cuadro_46_empresas_financiadoras_primas_autorizadas.csv",
    "53": "cuadro_53_empresas_medicina_prepagada_autorizadas.csv",
}
CAPITAL_GARANTIA_CSV = "cuadro_02_capital_garantia_por_empresa.csv"

# Primas (cuadros 3, 4)
PRIMAS_POR_RAMO_CSV = {"3": "cuadro_03_primas_por_ramo.csv"}
PRIMAS_POR_RAMO_EMPRESA_CSV = "cuadro_04_primas_por_ramo_empresa.csv"
# Siniestros (cuadro 6, 7, 8-A, 8-B, 8-C)
SINIESTROS_POR_RAMO_CSV = "cuadro_06_siniestros_pagados_por_ramo.csv"
SINIESTROS_POR_RAMO_EMPRESA_CSV = "cuadro_07_siniestros_por_ramo_empresa.csv"
SINIESTROS_8A_CSV = ["cuadro_08A_pag29_5_ramos.csv", "cuadro_08A_pag30_5_ramos_total.csv"]
SINIESTROS_8B_CSV = ["cuadro_08B_pag31_5_ramos.csv", "cuadro_08B_pag32_6_ramos.csv", "cuadro_08B_pag33_5_ramos_total.csv"]
SINIESTROS_8C_CSV = ["cuadro_08C_pag34_5_ramos.csv", "cuadro_08C_pag35_3_ramos_total.csv"]
# Reservas (cuadros 9, 10, 11-14, 15, 16-19)
RESERVAS_TECNICAS_CSV = "cuadro_09_reservas_tecnicas.csv"
RESERVAS_PRIMA_POR_RAMO_CSV = "cuadro_10_reservas_prima_por_ramo.csv"
RESERVAS_PRIMA_POR_EMPRESA_CSV = {
    "11": "cuadro_11_reservas_prima_por_empresa.csv",
    "12": "cuadro_12_reservas_prima_personas_por_empresa.csv",
    "13": "cuadro_13_reservas_prima_patrimoniales_por_empresa.csv",
    "14": "cuadro_14_reservas_prima_obligacionales_por_empresa.csv",
}
RESERVAS_PRESTACIONES_POR_RAMO_CSV = "cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv"
RESERVAS_PRESTACIONES_POR_EMPRESA_CSV = {
    "16": "cuadro_16_reservas_prestaciones_siniestros_por_empresa.csv",
    "17": "cuadro_17_reservas_prestaciones_siniestros_personas_por_empresa.csv",
    "18": "cuadro_18_reservas_prestaciones_siniestros_patrimoniales_por_empresa.csv",
    "19": "cuadro_19_reservas_prestaciones_siniestros_obligacionales_por_empresa.csv",
}

# Estados ingresos y egresos (25-A, 25-B, 41-A, 41-B, 48, 55-A, 55-B)
ESTADOS_INGRESOS_EGRESOS_CSV = {
    "25-A": "cuadro_25A_estado_ganancias_perdidas_ingresos.csv",
    "25-B": "cuadro_25B_estado_ganancias_perdidas_egresos.csv",
    "41-A": "cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros.csv",
    "41-B": "cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros.csv",
    "48": "cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas.csv",
    "55-A": "cuadro_55A_estado_ganancias_perdidas_ingresos_medicina_prepagada.csv",
    "55-B": "cuadro_55B_estado_ganancias_perdidas_egresos_medicina_prepagada.csv",
}

# Primas 5-A, 5-B, 5-C (varios CSV por cuadro; se agrega por ramo)
PRIMAS_5A_CSV = ["cuadro_05A_pag20_5_ramos.csv", "cuadro_05A_pag21_4_ramos_total.csv"]
PRIMAS_5B_CSV = ["cuadro_05B_pag22_5_ramos.csv", "cuadro_05B_pag23_6_ramos.csv", "cuadro_05B_pag24_5_ramos_total.csv"]
PRIMAS_5C_CSV = ["cuadro_05C_pag25_5_ramos.csv", "cuadro_05C_pag26_3_ramos_total.csv"]

# Gestión general (cuadro 26)
GESTION_GENERAL_CSV = "cuadro_26_gestion_general.csv"

# Indicadores financieros por empresa (cuadros 29, 44, 52, 58)
INDICADORES_FINANCIEROS_CSV = {
    "29": "cuadro_29_indicadores_financieros_2023_por_empresa.csv",
    "44": "cuadro_44_indicadores_financieros_2023_reaseguros.csv",
    "52": "cuadro_52_indicadores_financieros_2023_financiadoras_primas.csv",
    "58": "cuadro_58_indicadores_financieros_2023_medicina_prepagada.csv",
}

# Suficiencia patrimonio (30, 45)
SUFICIENCIA_PATRIMONIO_CSV = {
    "30": "cuadro_30_suficiencia_patrimonio_solvencia_2022_2023.csv",
    "45": "cuadro_45_suficiencia_patrimonio_solvencia_reaseguros_2022_2023.csv",
}

# Series históricas primas (31-A, 31-B)
SERIES_HISTORICAS_CSV = {
    "31-A": "cuadro_31A_primas_netas_cobradas_2023_vs_2022.csv",
    "31-B": "cuadro_31B_primas_prestaciones_siniestros_1990_2023.csv",
}

# Gastos vs primas (22, 23)
GASTOS_VS_PRIMAS_CSV = {
    "22": "cuadro_22_gastos_admin_vs_primas_por_empresa.csv",
    "23": "cuadro_23_gastos_produccion_vs_primas_por_ramo.csv",
}

# Cantidad pólizas y siniestros (37, 38)
CANTIDAD_POLIZAS_CSV = {
    "37": "cuadro_37_cantidad_polizas_siniestros_por_ramo.csv",
    "38": "cuadro_38_cantidad_polizas_siniestros_por_empresa.csv",
}

# Datos por empresa (27, 28, 34, 35, 36, 49, 50, 51, 56, 57)
DATOS_POR_EMPRESA_CSV = {
    "27": "cuadro_27_rentabilidad_inversiones_por_empresa.csv",
    "28": "cuadro_28_resultados_ejercicio_2019_2023_por_empresa.csv",
    "34": "cuadro_34_primas_brutas_personas_generales_por_empresa.csv",
    "35": "cuadro_35_devolucion_primas_personas_generales_por_empresa.csv",
    "36": "cuadro_36_reservas_prestaciones_siniestros_pendientes_ocurridos_no_notificados.csv",
    "49": "cuadro_49_ingresos_por_empresa_financiadoras_primas.csv",
    "50": "cuadro_50_circulante_activo_por_empresa_financiadoras_primas.csv",
    "51": "cuadro_51_gastos_operativos_administrativos_financieros_por_empresa_financiadoras_primas.csv",
    "56": "cuadro_56_ingresos_netos_por_empresa_medicina_prepagada.csv",
    "57": "cuadro_57_reservas_tecnicas_por_empresa_medicina_prepagada.csv",
}


def _verificadas_dir(year: int) -> Path:
    return DATA_STAGED / str(year) / "verificadas"


def load_balances_condensados(verificadas: Path, year: int) -> list[dict]:
    rows = []
    for cuadro_id, filename in BALANCES_CONDENSADOS_CSV.items():
        path = verificadas / filename
        if not path.exists():
            print(f"[ETL] No encontrado: {path}")
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        idx_c = header.index("CONCEPTO") if "CONCEPTO" in header else 0
        idx_m = header.index("MONTO") if "MONTO" in header else 1
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            if len(parts) <= max(idx_c, idx_m):
                continue
            concepto = parts[idx_c] if idx_c < len(parts) else ""
            monto = parts[idx_m] if idx_m < len(parts) else ""
            if not concepto and not monto:
                continue
            rows.append({
                "anio": year,
                "cuadro_id": cuadro_id,
                "concepto": concepto or None,
                "monto": monto or None,
                "tipo": None,
            })
    return rows


def load_listados_empresas(verificadas: Path, year: int) -> list[dict]:
    rows = []
    for cuadro_id, filename in LISTADOS_EMPRESAS_CSV.items():
        path = verificadas / filename
        if not path.exists():
            print(f"[ETL] No encontrado: {path}")
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        idx_num = header.index("NUMERO_ORDEN") if "NUMERO_ORDEN" in header else 0
        idx_nom = header.index("NOMBRE_EMPRESA") if "NOMBRE_EMPRESA" in header else 1
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            if len(parts) <= max(idx_num, idx_nom):
                continue
            num = parts[idx_num] if idx_num < len(parts) else None
            nombre = parts[idx_nom] if idx_nom < len(parts) else ""
            try:
                numero_orden = int(num) if num and str(num).isdigit() else None
            except (ValueError, TypeError):
                numero_orden = None
            rows.append({
                "anio": year,
                "cuadro_id": cuadro_id,
                "numero_orden": numero_orden,
                "nombre_empresa": nombre or None,
            })
    return rows


def load_capital_garantia_por_empresa(verificadas: Path, year: int) -> list[dict]:
    """Carga Cuadro 2: Capital y garantía por empresa (inscripción número/año, empresa, capital, garantías)."""
    rows = []
    path = verificadas / CAPITAL_GARANTIA_CSV
    if not path.exists():
        print(f"[ETL] No encontrado: {path}")
        return rows
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return rows
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_num = header.index("INSCRIPCION_NUMERO") if "INSCRIPCION_NUMERO" in header else 0
    idx_anio = header.index("INSCRIPCION_ANIO") if "INSCRIPCION_ANIO" in header else 1
    idx_emp = header.index("EMPRESA") if "EMPRESA" in header else 2
    idx_cap = header.index("CAPITAL_SOCIAL_SUSCRITO") if "CAPITAL_SOCIAL_SUSCRITO" in header else 3
    idx_gs = header.index("GARANTIA_OPERACIONES_SEGUROS") if "GARANTIA_OPERACIONES_SEGUROS" in header else 4
    idx_gf = header.index("GARANTIA_OPERACIONES_FIDEICOMISO") if "GARANTIA_OPERACIONES_FIDEICOMISO" in header else 5
    idx_gt = header.index("GARANTIA_TOTAL") if "GARANTIA_TOTAL" in header else 6
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= max(idx_emp, idx_cap):
            continue
        rows.append({
            "anio": year,
            "cuadro_id": "2",
            "inscripcion_numero": parts[idx_num] if idx_num < len(parts) else None,
            "inscripcion_anio": parts[idx_anio] if idx_anio < len(parts) else None,
            "nombre_empresa": parts[idx_emp] if idx_emp < len(parts) else None,
            "capital_social_suscrito": parts[idx_cap] if idx_cap < len(parts) else None,
            "garantia_operaciones_seguros": parts[idx_gs] if idx_gs < len(parts) else None,
            "garantia_operaciones_fideicomiso": parts[idx_gf] if idx_gf < len(parts) else None,
            "garantia_total": parts[idx_gt] if idx_gt < len(parts) else None,
        })
    return rows


def _csv_header_index(header: list, *names: str) -> int:
    """Devuelve índice de la primera columna que coincida (sin importar mayúsculas/espacios)."""
    h_upper = [x.strip().upper().replace(" ", "_") for x in header]
    for n in names:
        n_upper = n.strip().upper().replace(" ", "_")
        for i, h in enumerate(h_upper):
            if n_upper in h or h in n_upper or h.replace("_", "") == n_upper.replace("_", ""):
                return i
    return 0


def load_primas_por_ramo(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 3 (y opcionalmente 5-A, 5-B, 5-C) en primas_por_ramo."""
    rows = []
    for cuadro_id, filename in PRIMAS_POR_RAMO_CSV.items():
        path = verificadas / filename
        if not path.exists():
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        idx_ramo = _csv_header_index(header, "RAMO DE SEGUROS", "RAMO")
        idx_sd = _csv_header_index(header, "SEGURO DIRECTO")
        idx_reas = _csv_header_index(header, "REASEGURO ACEPTADO")
        idx_tot = _csv_header_index(header, "TOTAL")
        idx_pct = _csv_header_index(header, "%", "PORCENTAJE")
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            if len(parts) <= idx_ramo:
                continue
            rows.append({
                "anio": year,
                "cuadro_id": cuadro_id,
                "concepto_ramo": parts[idx_ramo] if idx_ramo < len(parts) else None,
                "seguro_directo": parts[idx_sd] if idx_sd < len(parts) else None,
                "reaseguro_aceptado": parts[idx_reas] if idx_reas < len(parts) else None,
                "total": parts[idx_tot] if idx_tot < len(parts) else None,
                "pct": parts[idx_pct] if idx_pct < len(parts) else None,
            })
    return rows


def load_primas_por_ramo_empresa(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 4 en primas_por_ramo_empresa (nombre_empresa + resto en datos)."""
    path = verificadas / PRIMAS_POR_RAMO_EMPRESA_CSV
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_nom = _csv_header_index(header, "Nombre Empresa", "NOMBRE_EMPRESA")
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= idx_nom:
            continue
        nombre = parts[idx_nom] if idx_nom < len(parts) else None
        datos = {header[i]: parts[i] for i in range(len(parts)) if i != idx_nom and i < len(header)}
        rows.append({
            "anio": year,
            "cuadro_id": "4",
            "nombre_empresa": nombre,
            "datos": datos if datos else None,
        })
    return rows


def load_siniestros_por_ramo(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 6 en siniestros_por_ramo (concepto_ramo + columnas en datos)."""
    path = verificadas / SINIESTROS_POR_RAMO_CSV
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_ramo = _csv_header_index(header, "RAMO DE SEGUROS", "RAMO")
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= idx_ramo:
            continue
        concepto_ramo = parts[idx_ramo] if idx_ramo < len(parts) else None
        datos = {header[i]: parts[i] for i in range(min(len(parts), len(header)))}
        rows.append({
            "anio": year,
            "cuadro_id": "6",
            "concepto_ramo": concepto_ramo,
            "datos": datos if datos else None,
        })
    return rows


def load_siniestros_por_ramo_empresa(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 7 en siniestros_por_ramo_empresa (nombre_empresa + datos)."""
    path = verificadas / SINIESTROS_POR_RAMO_EMPRESA_CSV
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_nom = _csv_header_index(header, "Nombre Empresa", "NOMBRE_EMPRESA")
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= idx_nom:
            continue
        nombre = parts[idx_nom] if idx_nom < len(parts) else None
        datos = {header[i]: parts[i] for i in range(len(parts)) if i != idx_nom and i < len(header)}
        rows.append({
            "anio": year,
            "cuadro_id": "7",
            "nombre_empresa": nombre,
            "datos": datos if datos else None,
        })
    return rows


def _agregar_siniestros_por_ramo_desde_empresas(verificadas: Path, year: int, cuadro_id: str, filenames: list[str]) -> list[dict]:
    """Suma por columna (ramo) desde CSVs empresa x ramo; devuelve filas para siniestros_por_ramo."""
    from collections import defaultdict
    totals = defaultdict(float)
    for filename in filenames:
        path = verificadas / filename
        if not path.exists():
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        idx_nom = _csv_header_index(header, "Nombre Empresa", "NOMBRE_EMPRESA")
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            for i, h in enumerate(header):
                if i == idx_nom or i >= len(parts):
                    continue
                try:
                    v = float(parts[i].replace(",", "."))
                    totals[h] += v
                except (ValueError, TypeError):
                    pass
    return [
        {"anio": year, "cuadro_id": cuadro_id, "concepto_ramo": ramo, "datos": {"total": round(total, 2)}}
        for ramo, total in sorted(totals.items())
    ]


def load_siniestros_8A_8B_8C(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 8-A, 8-B, 8-C agregados por ramo en siniestros_por_ramo."""
    out = []
    out.extend(_agregar_siniestros_por_ramo_desde_empresas(verificadas, year, "8-A", SINIESTROS_8A_CSV))
    out.extend(_agregar_siniestros_por_ramo_desde_empresas(verificadas, year, "8-B", SINIESTROS_8B_CSV))
    out.extend(_agregar_siniestros_por_ramo_desde_empresas(verificadas, year, "8-C", SINIESTROS_8C_CSV))
    return out


def load_reservas_tecnicas_agregado(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 9 en reservas_tecnicas_agregado."""
    path = verificadas / RESERVAS_TECNICAS_CSV
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_c = _csv_header_index(header, "CONCEPTO")
    idx_m = _csv_header_index(header, "MONTO")
    idx_t = _csv_header_index(header, "TIPO")
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= max(idx_c, idx_m):
            continue
        rows.append({
            "anio": year,
            "cuadro_id": "9",
            "concepto": parts[idx_c] if idx_c < len(parts) else None,
            "monto": parts[idx_m] if idx_m < len(parts) else None,
            "tipo": parts[idx_t] if idx_t < len(parts) else None,
        })
    return rows


def load_reservas_prima_por_ramo(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 10 en reservas_prima_por_ramo (concepto_ramo + datos)."""
    path = verificadas / RESERVAS_PRIMA_POR_RAMO_CSV
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_ramo = _csv_header_index(header, "RAMO_DE_SEGUROS", "RAMO DE SEGUROS")
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= idx_ramo:
            continue
        concepto_ramo = parts[idx_ramo] if idx_ramo < len(parts) else None
        datos = {header[i]: parts[i] for i in range(min(len(parts), len(header)))}
        rows.append({
            "anio": year,
            "cuadro_id": "10",
            "concepto_ramo": concepto_ramo,
            "datos": datos if datos else None,
        })
    return rows


def load_reservas_prestaciones_por_ramo(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 15 en reservas_prestaciones_por_ramo (concepto_ramo + datos)."""
    path = verificadas / RESERVAS_PRESTACIONES_POR_RAMO_CSV
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_ramo = _csv_header_index(header, "RAMO_DE_SEGUROS", "RAMO DE SEGUROS")
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= idx_ramo:
            continue
        concepto_ramo = parts[idx_ramo] if idx_ramo < len(parts) else None
        datos = {header[i]: parts[i] for i in range(min(len(parts), len(header)))}
        rows.append({
            "anio": year,
            "cuadro_id": "15",
            "concepto_ramo": concepto_ramo,
            "datos": datos if datos else None,
        })
    return rows


def _load_reservas_por_empresa_csv(verificadas: Path, year: int, cuadro_id: str, filename: str) -> list[dict]:
    """Carga un CSV reservas por empresa (NOMBRE_EMPRESA + resto en datos)."""
    path = verificadas / filename
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_nom = _csv_header_index(header, "NOMBRE_EMPRESA", "Nombre Empresa")
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= idx_nom:
            continue
        nombre = parts[idx_nom] if idx_nom < len(parts) else None
        datos = {header[i]: parts[i] for i in range(len(parts)) if i != idx_nom and i < len(header)}
        rows.append({
            "anio": year,
            "cuadro_id": cuadro_id,
            "nombre_empresa": nombre,
            "datos": datos if datos else None,
        })
    return rows


def load_reservas_prima_por_empresa(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 11, 12, 13, 14 en reservas_prima_por_empresa."""
    out = []
    for cuadro_id, filename in RESERVAS_PRIMA_POR_EMPRESA_CSV.items():
        out.extend(_load_reservas_por_empresa_csv(verificadas, year, cuadro_id, filename))
    return out


def load_reservas_prestaciones_por_empresa(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 16, 17, 18, 19 en reservas_prestaciones_por_empresa."""
    out = []
    for cuadro_id, filename in RESERVAS_PRESTACIONES_POR_EMPRESA_CSV.items():
        out.extend(_load_reservas_por_empresa_csv(verificadas, year, cuadro_id, filename))
    return out


def load_indicadores_financieros_empresa(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 29, 44, 52, 58 en indicadores_financieros_empresa (nombre_empresa + resto en datos)."""
    out = []
    for cuadro_id, filename in INDICADORES_FINANCIEROS_CSV.items():
        out.extend(_load_reservas_por_empresa_csv(verificadas, year, cuadro_id, filename))
    return out


def load_suficiencia_patrimonio(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 30, 45 en suficiencia_patrimonio (nombre_empresa + datos)."""
    out = []
    for cuadro_id, filename in SUFICIENCIA_PATRIMONIO_CSV.items():
        out.extend(_load_reservas_por_empresa_csv(verificadas, year, cuadro_id, filename))
    return out


def _load_csv_concepto_valores(verificadas: Path, year: int, cuadro_id: str, filename: str, col_concepto: str) -> list[dict]:
    """Carga CSV con columna concepto (ramo o empresa) y resto en datos. Para gastos_vs_primas."""
    path = verificadas / filename
    if not path.exists():
        return []
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx = _csv_header_index(header, col_concepto)
    rows = []
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= idx:
            continue
        concepto = parts[idx] if idx < len(parts) else None
        datos = {header[i]: parts[i] for i in range(len(parts)) if i != idx and i < len(header)}
        rows.append({
            "anio": year,
            "cuadro_id": cuadro_id,
            "origen_archivo": filename,
            "concepto_ramo_o_empresa": concepto,
            "datos": datos if datos else None,
        })
    return rows


def load_gastos_vs_primas(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 22, 23 en gastos_vs_primas."""
    out = []
    for cuadro_id, filename in GASTOS_VS_PRIMAS_CSV.items():
        col = "NOMBRE_EMPRESA" if cuadro_id == "22" else "RAMO_DE_SEGUROS"
        out.extend(_load_csv_concepto_valores(verificadas, year, cuadro_id, filename, col))
    return out


def load_cantidad_polizas_siniestros(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 37, 38 en cantidad_polizas_siniestros (concepto, polizas, siniestros, datos)."""
    out = []
    for cuadro_id, filename in CANTIDAD_POLIZAS_CSV.items():
        path = verificadas / filename
        if not path.exists():
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        idx_concepto = _csv_header_index(header, "RAMO_DE_SEGUROS", "NOMBRE_EMPRESA")
        idx_pol = _csv_header_index(header, "POLIZAS")
        idx_sin = _csv_header_index(header, "SINIESTROS")
        if idx_concepto is None:
            idx_concepto = 0
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            if len(parts) <= idx_concepto:
                continue
            concepto = parts[idx_concepto] if idx_concepto < len(parts) else None
            pol = parts[idx_pol] if idx_pol is not None and idx_pol < len(parts) else None
            sin = parts[idx_sin] if idx_sin is not None and idx_sin < len(parts) else None
            datos = {header[i]: parts[i] for i in range(len(parts)) if i not in (idx_concepto, idx_pol, idx_sin) and i < len(header)}
            out.append({
                "anio": year,
                "cuadro_id": cuadro_id,
                "concepto_ramo_o_empresa": concepto,
                "polizas": pol,
                "siniestros": sin,
                "datos": datos if datos else None,
            })
    return out


def load_series_historicas_primas(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 31-A, 31-B en series_historicas_primas (tipo_serie + datos)."""
    out = []
    for cuadro_id, filename in SERIES_HISTORICAS_CSV.items():
        path = verificadas / filename
        if not path.exists():
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            datos = {header[i]: parts[i] for i in range(min(len(parts), len(header)))}
            out.append({
                "anio": year,
                "cuadro_id": cuadro_id,
                "tipo_serie": cuadro_id,
                "datos": datos if datos else None,
            })
    return out


def load_datos_por_empresa(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 27, 28, 34, 35, 36, 49, 50, 51, 56, 57 en datos_por_empresa."""
    out = []
    for cuadro_id, filename in DATOS_POR_EMPRESA_CSV.items():
        path = verificadas / filename
        if not path.exists():
            continue
        out.extend(_load_reservas_por_empresa_csv(verificadas, year, cuadro_id, filename))
    return out


def load_estados_ingresos_egresos(verificadas: Path, year: int) -> list[dict]:
    """Carga estados de resultado (ingresos/egresos) por cuadro. CONCEPTO, MONTO, TIPO."""
    rows = []
    for cuadro_id, filename in ESTADOS_INGRESOS_EGRESOS_CSV.items():
        path = verificadas / filename
        if not path.exists():
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        idx_c = _csv_header_index(header, "CONCEPTO")
        idx_m = _csv_header_index(header, "MONTO")
        idx_t = _csv_header_index(header, "TIPO")
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            if len(parts) <= max(idx_c, idx_m):
                continue
            rows.append({
                "anio": year,
                "cuadro_id": cuadro_id,
                "concepto": parts[idx_c] if idx_c < len(parts) else None,
                "monto": parts[idx_m] if idx_m < len(parts) else None,
                "tipo": parts[idx_t] if idx_t < len(parts) else None,
            })
    return rows


def _agregar_primas_por_ramo_desde_empresas(verificadas: Path, year: int, cuadro_id: str, filenames: list[str]) -> list[dict]:
    """Lee CSVs con Nombre Empresa + columnas ramo, suma por columna, devuelve filas para primas_por_ramo."""
    from collections import defaultdict
    totals = defaultdict(float)
    for filename in filenames:
        path = verificadas / filename
        if not path.exists():
            continue
        with open(path, encoding=ENCODING) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) < 2:
            continue
        header = [h.strip('"') for h in lines[0].split(SEP)]
        idx_nom = _csv_header_index(header, "Nombre Empresa", "NOMBRE_EMPRESA")
        for line in lines[1:]:
            parts = [p.strip('"') for p in line.split(SEP)]
            for i, h in enumerate(header):
                if i == idx_nom or i >= len(parts):
                    continue
                try:
                    v = float(parts[i].replace(",", "."))
                    totals[h] += v
                except (ValueError, TypeError):
                    pass
    return [
        {
            "anio": year,
            "cuadro_id": cuadro_id,
            "concepto_ramo": ramo,
            "seguro_directo": str(int(round(total))),
            "reaseguro_aceptado": None,
            "total": str(int(round(total))),
            "pct": None,
        }
        for ramo, total in sorted(totals.items())
    ]


def load_primas_5A_5B_5C(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadros 5-A, 5-B, 5-C agregados por ramo en primas_por_ramo."""
    out = []
    out.extend(_agregar_primas_por_ramo_desde_empresas(verificadas, year, "5-A", PRIMAS_5A_CSV))
    out.extend(_agregar_primas_por_ramo_desde_empresas(verificadas, year, "5-B", PRIMAS_5B_CSV))
    out.extend(_agregar_primas_por_ramo_desde_empresas(verificadas, year, "5-C", PRIMAS_5C_CSV))
    return out


def load_gestion_general(verificadas: Path, year: int) -> list[dict]:
    """Carga cuadro 26 en gestion_general (concepto, monto)."""
    rows = []
    path = verificadas / GESTION_GENERAL_CSV
    if not path.exists():
        return rows
    with open(path, encoding=ENCODING) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) < 2:
        return rows
    header = [h.strip('"') for h in lines[0].split(SEP)]
    idx_c = _csv_header_index(header, "CONCEPTO")
    idx_m = _csv_header_index(header, "MONTO")
    for line in lines[1:]:
        parts = [p.strip('"') for p in line.split(SEP)]
        if len(parts) <= max(idx_c, idx_m):
            continue
        rows.append({
            "anio": year,
            "cuadro_id": "26",
            "concepto": parts[idx_c] if idx_c < len(parts) else None,
            "monto": parts[idx_m] if idx_m < len(parts) else None,
        })
    return rows


def run_etl(year: int) -> bool:
    # ETL necesita INSERT/DELETE: usar SUPABASE_SERVICE_ROLE_KEY (secret). Anon solo tiene SELECT.
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
    if not SUPABASE_URL or not key:
        print("[ETL] Configure SUPABASE_URL y SUPABASE_KEY o SUPABASE_SERVICE_ROLE_KEY (ej. .env).")
        if not SUPABASE_SERVICE_ROLE_KEY and SUPABASE_KEY:
            print("[ETL] Para cargar datos use SUPABASE_SERVICE_ROLE_KEY (clave secret) en .env.")
        return False

    if not SUPABASE_SERVICE_ROLE_KEY and SUPABASE_KEY:
        print("[ETL] Aviso: usando SUPABASE_KEY (anon). Si falla por permisos, defina SUPABASE_SERVICE_ROLE_KEY.")

    try:
        from supabase import create_client
        from supabase.lib.client_options import SyncClientOptions
        sb = create_client(SUPABASE_URL, key, options=SyncClientOptions(schema="anuario"))
    except Exception as e:
        print(f"[ETL] No se pudo crear cliente Supabase (schema anuario): {e}")
        return False

    verificadas = _verificadas_dir(year)
    if not verificadas.exists():
        print(f"[ETL] No existe directorio: {verificadas}")
        return False

    # 0) Asegurar que cuadros 1, 2, 11-14, 16-19 existan (para FK)
    try:
        cuadros_extra = [
            {"cuadro_id": "1", "nombre": "Empresas de seguro autorizadas", "sector": "seguro_directo"},
            {"cuadro_id": "2", "nombre": "Capital y garantía por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "11", "nombre": "Reservas prima por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "12", "nombre": "Reservas prima personas por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "13", "nombre": "Reservas prima patrimoniales por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "14", "nombre": "Reservas prima obligacionales por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "16", "nombre": "Reservas prestaciones por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "17", "nombre": "Reservas prestaciones personas por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "18", "nombre": "Reservas prestaciones patrimoniales por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "19", "nombre": "Reservas prestaciones obligacionales por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "29", "nombre": "Indicadores financieros por empresa (seguro)", "sector": "seguro_directo"},
            {"cuadro_id": "44", "nombre": "Indicadores financieros reaseguros", "sector": "reaseguro"},
            {"cuadro_id": "52", "nombre": "Indicadores financieros financiadoras de primas", "sector": "financiadoras_primas"},
            {"cuadro_id": "58", "nombre": "Indicadores financieros medicina prepagada", "sector": "medicina_prepagada"},
            {"cuadro_id": "30", "nombre": "Suficiencia patrimonio solvencia", "sector": "seguro_directo"},
            {"cuadro_id": "45", "nombre": "Suficiencia patrimonio reaseguros", "sector": "reaseguro"},
            {"cuadro_id": "31-A", "nombre": "Series primas netas 2023 vs 2022", "sector": "seguro_directo"},
            {"cuadro_id": "31-B", "nombre": "Series primas prestaciones 1990-2023", "sector": "seguro_directo"},
            {"cuadro_id": "22", "nombre": "Gastos administración vs primas", "sector": "seguro_directo"},
            {"cuadro_id": "23", "nombre": "Gastos producción vs primas por ramo", "sector": "seguro_directo"},
            {"cuadro_id": "37", "nombre": "Cantidad pólizas y siniestros por ramo", "sector": "seguro_directo"},
            {"cuadro_id": "38", "nombre": "Cantidad pólizas y siniestros por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "27", "nombre": "Rentabilidad inversiones por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "28", "nombre": "Resultados ejercicio 2019-2023 por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "34", "nombre": "Primas brutas personas por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "35", "nombre": "Devolución primas por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "36", "nombre": "Reservas prestaciones pendientes por empresa", "sector": "seguro_directo"},
            {"cuadro_id": "49", "nombre": "Ingresos por empresa financiadoras", "sector": "financiadoras_primas"},
            {"cuadro_id": "50", "nombre": "Circulante activo por empresa financiadoras", "sector": "financiadoras_primas"},
            {"cuadro_id": "51", "nombre": "Gastos operativos por empresa financiadoras", "sector": "financiadoras_primas"},
            {"cuadro_id": "56", "nombre": "Ingresos netos por empresa medicina prepagada", "sector": "medicina_prepagada"},
            {"cuadro_id": "57", "nombre": "Reservas técnicas por empresa medicina prepagada", "sector": "medicina_prepagada"},
        ]
        sb.table("cuadros").upsert(cuadros_extra, on_conflict="cuadro_id").execute()
    except Exception as e:
        print(f"[ETL] Aviso al asegurar cuadros: {e}")

    # 1) Balances condensados
    balances = load_balances_condensados(verificadas, year)
    if balances:
        try:
            sb.table("balances_condensados").delete().eq("anio", year).execute()
            chunk_size = 200
            for i in range(0, len(balances), chunk_size):
                chunk = balances[i : i + chunk_size]
                sb.table("balances_condensados").insert(chunk).execute()
            print(f"[ETL] balances_condensados: {len(balances)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Error balances_condensados: {e}")
            return False
    else:
        print("[ETL] No se cargaron filas en balances_condensados.")

    # 2) Listados empresas
    listados = load_listados_empresas(verificadas, year)
    if listados:
        try:
            sb.table("listados_empresas").delete().eq("anio", year).execute()
            chunk_size = 200
            for i in range(0, len(listados), chunk_size):
                chunk = listados[i : i + chunk_size]
                sb.table("listados_empresas").insert(chunk).execute()
            print(f"[ETL] listados_empresas: {len(listados)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Error listados_empresas: {e}")
            return False
    else:
        print("[ETL] No se cargaron filas en listados_empresas.")

    # 3) Capital y garantía por empresa (Cuadro 2) — requiere tabla en Supabase (006 o 002)
    capital_garantia = load_capital_garantia_por_empresa(verificadas, year)
    if capital_garantia:
        try:
            sb.table("capital_garantia_por_empresa").delete().eq("anio", year).execute()
            chunk_size = 200
            for i in range(0, len(capital_garantia), chunk_size):
                chunk = capital_garantia[i : i + chunk_size]
                sb.table("capital_garantia_por_empresa").insert(chunk).execute()
            print(f"[ETL] capital_garantia_por_empresa: {len(capital_garantia)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso: capital_garantia_por_empresa no cargado (¿tabla existe? Ejecute 006 en Supabase): {e}")
    else:
        print("[ETL] No se cargaron filas en capital_garantia_por_empresa.")

    # 4) Primas por ramo (cuadro 3 + 5-A, 5-B, 5-C)
    primas_ramo = load_primas_por_ramo(verificadas, year) + load_primas_5A_5B_5C(verificadas, year)
    if primas_ramo:
        try:
            sb.table("primas_por_ramo").delete().eq("anio", year).execute()
            for i in range(0, len(primas_ramo), 200):
                sb.table("primas_por_ramo").insert(primas_ramo[i : i + 200]).execute()
            print(f"[ETL] primas_por_ramo: {len(primas_ramo)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso primas_por_ramo: {e}")

    # 4b) Estados ingresos y egresos (25-A, 25-B, 41-A, 41-B, 48, 55-A, 55-B)
    estados = load_estados_ingresos_egresos(verificadas, year)
    if estados:
        try:
            sb.table("estados_ingresos_egresos").delete().eq("anio", year).execute()
            for i in range(0, len(estados), 200):
                sb.table("estados_ingresos_egresos").insert(estados[i : i + 200]).execute()
            print(f"[ETL] estados_ingresos_egresos: {len(estados)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso estados_ingresos_egresos: {e}")

    # 4c) Gestión general (cuadro 26)
    gestion = load_gestion_general(verificadas, year)
    if gestion:
        try:
            sb.table("gestion_general").delete().eq("anio", year).execute()
            for i in range(0, len(gestion), 200):
                sb.table("gestion_general").insert(gestion[i : i + 200]).execute()
            print(f"[ETL] gestion_general: {len(gestion)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso gestion_general: {e}")

    # 5) Primas por ramo y empresa (cuadro 4)
    primas_emp = load_primas_por_ramo_empresa(verificadas, year)
    if primas_emp:
        try:
            sb.table("primas_por_ramo_empresa").delete().eq("anio", year).execute()
            for i in range(0, len(primas_emp), 200):
                sb.table("primas_por_ramo_empresa").insert(primas_emp[i : i + 200]).execute()
            print(f"[ETL] primas_por_ramo_empresa: {len(primas_emp)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso primas_por_ramo_empresa: {e}")

    # 6) Siniestros por ramo (cuadro 6 + 8-A, 8-B, 8-C)
    siniestros = load_siniestros_por_ramo(verificadas, year) + load_siniestros_8A_8B_8C(verificadas, year)
    if siniestros:
        try:
            sb.table("siniestros_por_ramo").delete().eq("anio", year).execute()
            for i in range(0, len(siniestros), 200):
                sb.table("siniestros_por_ramo").insert(siniestros[i : i + 200]).execute()
            print(f"[ETL] siniestros_por_ramo: {len(siniestros)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso siniestros_por_ramo: {e}")

    # 6b) Siniestros por ramo y empresa (cuadro 7)
    siniestros_emp = load_siniestros_por_ramo_empresa(verificadas, year)
    if siniestros_emp:
        try:
            sb.table("siniestros_por_ramo_empresa").delete().eq("anio", year).execute()
            for i in range(0, len(siniestros_emp), 200):
                sb.table("siniestros_por_ramo_empresa").insert(siniestros_emp[i : i + 200]).execute()
            print(f"[ETL] siniestros_por_ramo_empresa: {len(siniestros_emp)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso siniestros_por_ramo_empresa (¿tabla existe? Ejecute 007 en Supabase): {e}")

    # 7) Reservas técnicas agregado (cuadro 9)
    res_tec = load_reservas_tecnicas_agregado(verificadas, year)
    if res_tec:
        try:
            sb.table("reservas_tecnicas_agregado").delete().eq("anio", year).execute()
            for i in range(0, len(res_tec), 200):
                sb.table("reservas_tecnicas_agregado").insert(res_tec[i : i + 200]).execute()
            print(f"[ETL] reservas_tecnicas_agregado: {len(res_tec)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso reservas_tecnicas_agregado: {e}")

    # 8) Reservas prima por ramo (cuadro 10)
    res_prima = load_reservas_prima_por_ramo(verificadas, year)
    if res_prima:
        try:
            sb.table("reservas_prima_por_ramo").delete().eq("anio", year).execute()
            for i in range(0, len(res_prima), 200):
                sb.table("reservas_prima_por_ramo").insert(res_prima[i : i + 200]).execute()
            print(f"[ETL] reservas_prima_por_ramo: {len(res_prima)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso reservas_prima_por_ramo: {e}")

    # 9) Reservas prestaciones por ramo (cuadro 15)
    res_prest = load_reservas_prestaciones_por_ramo(verificadas, year)
    if res_prest:
        try:
            sb.table("reservas_prestaciones_por_ramo").delete().eq("anio", year).execute()
            for i in range(0, len(res_prest), 200):
                sb.table("reservas_prestaciones_por_ramo").insert(res_prest[i : i + 200]).execute()
            print(f"[ETL] reservas_prestaciones_por_ramo: {len(res_prest)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso reservas_prestaciones_por_ramo: {e}")

    # 10) Reservas prima por empresa (cuadros 11, 12, 13, 14)
    res_prima_emp = load_reservas_prima_por_empresa(verificadas, year)
    if res_prima_emp:
        try:
            sb.table("reservas_prima_por_empresa").delete().eq("anio", year).execute()
            for i in range(0, len(res_prima_emp), 200):
                sb.table("reservas_prima_por_empresa").insert(res_prima_emp[i : i + 200]).execute()
            print(f"[ETL] reservas_prima_por_empresa: {len(res_prima_emp)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso reservas_prima_por_empresa: {e}")

    # 11) Reservas prestaciones por empresa (cuadros 16, 17, 18, 19)
    res_prest_emp = load_reservas_prestaciones_por_empresa(verificadas, year)
    if res_prest_emp:
        try:
            sb.table("reservas_prestaciones_por_empresa").delete().eq("anio", year).execute()
            for i in range(0, len(res_prest_emp), 200):
                sb.table("reservas_prestaciones_por_empresa").insert(res_prest_emp[i : i + 200]).execute()
            print(f"[ETL] reservas_prestaciones_por_empresa: {len(res_prest_emp)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso reservas_prestaciones_por_empresa: {e}")

    # 12) Indicadores financieros por empresa (cuadros 29, 44, 52, 58)
    ind_fin = load_indicadores_financieros_empresa(verificadas, year)
    if ind_fin:
        try:
            sb.table("indicadores_financieros_empresa").delete().eq("anio", year).execute()
            for i in range(0, len(ind_fin), 200):
                sb.table("indicadores_financieros_empresa").insert(ind_fin[i : i + 200]).execute()
            print(f"[ETL] indicadores_financieros_empresa: {len(ind_fin)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso indicadores_financieros_empresa: {e}")

    # 13) Suficiencia patrimonio (30, 45)
    suf = load_suficiencia_patrimonio(verificadas, year)
    if suf:
        try:
            sb.table("suficiencia_patrimonio").delete().eq("anio", year).execute()
            for i in range(0, len(suf), 200):
                sb.table("suficiencia_patrimonio").insert(suf[i : i + 200]).execute()
            print(f"[ETL] suficiencia_patrimonio: {len(suf)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso suficiencia_patrimonio: {e}")

    # 14) Series históricas primas (31-A, 31-B)
    series = load_series_historicas_primas(verificadas, year)
    if series:
        try:
            sb.table("series_historicas_primas").delete().eq("anio", year).execute()
            for i in range(0, len(series), 200):
                sb.table("series_historicas_primas").insert(series[i : i + 200]).execute()
            print(f"[ETL] series_historicas_primas: {len(series)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso series_historicas_primas: {e}")

    # 15) Gastos vs primas (22, 23)
    gastos = load_gastos_vs_primas(verificadas, year)
    if gastos:
        try:
            sb.table("gastos_vs_primas").delete().eq("anio", year).execute()
            for i in range(0, len(gastos), 200):
                sb.table("gastos_vs_primas").insert(gastos[i : i + 200]).execute()
            print(f"[ETL] gastos_vs_primas: {len(gastos)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso gastos_vs_primas: {e}")

    # 16) Cantidad pólizas y siniestros (37, 38)
    polizas = load_cantidad_polizas_siniestros(verificadas, year)
    if polizas:
        try:
            sb.table("cantidad_polizas_siniestros").delete().eq("anio", year).execute()
            for i in range(0, len(polizas), 200):
                sb.table("cantidad_polizas_siniestros").insert(polizas[i : i + 200]).execute()
            print(f"[ETL] cantidad_polizas_siniestros: {len(polizas)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso cantidad_polizas_siniestros: {e}")

    # 17) Datos por empresa (27, 28, 34, 35, 36, 49, 50, 51, 56, 57)
    datos_emp = load_datos_por_empresa(verificadas, year)
    if datos_emp:
        try:
            sb.table("datos_por_empresa").delete().eq("anio", year).execute()
            for i in range(0, len(datos_emp), 200):
                sb.table("datos_por_empresa").insert(datos_emp[i : i + 200]).execute()
            print(f"[ETL] datos_por_empresa: {len(datos_emp)} filas insertadas (año {year}).")
        except Exception as e:
            print(f"[ETL] Aviso datos_por_empresa: {e}")

    return True


def main():
    p = argparse.ArgumentParser(description="Carga anuario (balances + listados) a Supabase schema anuario.")
    p.add_argument("--year", type=int, default=2023, help="Año del anuario (carpeta staged)")
    args = p.parse_args()
    ok = run_etl(args.year)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
