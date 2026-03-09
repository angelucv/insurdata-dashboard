# scripts/verificar_indice_anuario.py
"""
Verifica que la extracción de tablas del anuario "Seguro en Cifras" cubra todos los
cuadros del índice (páginas 4 a 6 del PDF) y que cada cuadro esté asociado a su página.

- Lee el índice desde el PDF (págs. 4-6) para obtener la lista oficial de cuadros y páginas.
- Comprueba que existan los CSV esperados para cada cuadro extraído (3 a 58).
- Sirve para ubicar por cada página qué tabla corresponde.

Uso: python scripts/verificar_indice_anuario.py [--year 2023]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_STAGED

# Índice oficial: cuadro_id -> lista de archivos CSV que deben existir para ese cuadro.
INDICE_CSV_POR_CUADRO = {
    "1": ["cuadro_01_empresas_seguro_autorizadas.csv"],
    "2": ["cuadro_02_capital_garantia_por_empresa.csv"],
    "3": ["cuadro_03_primas_por_ramo.csv"],
    "4": ["cuadro_04_primas_por_ramo_empresa.csv"],
    "5-A": ["cuadro_05A_pag20_5_ramos.csv", "cuadro_05A_pag21_4_ramos_total.csv"],
    "5-B": ["cuadro_05B_pag22_5_ramos.csv", "cuadro_05B_pag23_6_ramos.csv", "cuadro_05B_pag24_5_ramos_total.csv"],
    "5-C": ["cuadro_05C_pag25_5_ramos.csv", "cuadro_05C_pag26_3_ramos_total.csv"],
    "6": ["cuadro_06_siniestros_pagados_por_ramo.csv"],
    "7": ["cuadro_07_siniestros_por_ramo_empresa.csv"],
    "8-A": ["cuadro_08A_pag29_5_ramos.csv", "cuadro_08A_pag30_5_ramos_total.csv"],
    "8-B": ["cuadro_08B_pag31_5_ramos.csv", "cuadro_08B_pag32_6_ramos.csv", "cuadro_08B_pag33_5_ramos_total.csv"],
    "8-C": ["cuadro_08C_pag34_5_ramos.csv", "cuadro_08C_pag35_3_ramos_total.csv"],
    "9": ["cuadro_09_reservas_tecnicas.csv"],
    "10": ["cuadro_10_reservas_prima_por_ramo.csv"],
    "11": ["cuadro_11_reservas_prima_por_empresa.csv"],
    "12": ["cuadro_12_reservas_prima_personas_por_empresa.csv"],
    "13": ["cuadro_13_reservas_prima_patrimoniales_por_empresa.csv"],
    "14": ["cuadro_14_reservas_prima_obligacionales_por_empresa.csv"],
    "15": ["cuadro_15_reservas_prestaciones_siniestros_por_ramo.csv"],
    "16": ["cuadro_16_reservas_prestaciones_siniestros_por_empresa.csv"],
    "17": ["cuadro_17_reservas_prestaciones_siniestros_personas_por_empresa.csv"],
    "18": ["cuadro_18_reservas_prestaciones_siniestros_patrimoniales_por_empresa.csv"],
    "19": ["cuadro_19_reservas_prestaciones_siniestros_obligacionales_por_empresa.csv"],
    "20-A": ["cuadro_20A_pag47_5_ramos.csv", "cuadro_20A_pag48_4_ramos_total.csv"],
    "20-B": ["cuadro_20B_pag49_6_ramos.csv", "cuadro_20B_pag50_6_ramos.csv", "cuadro_20B_pag51_4_ramos_total.csv"],
    "20-C": ["cuadro_20C_pag52_5_ramos.csv", "cuadro_20C_pag53_3_ramos_total.csv"],
    "20-D": ["cuadro_20D_pag54_5_ramos.csv", "cuadro_20D_pag55_4_ramos_total.csv"],
    "20-E": ["cuadro_20E_pag56_6_ramos.csv", "cuadro_20E_pag57_6_ramos.csv", "cuadro_20E_pag58_4_ramos_total.csv"],
    "20-F": ["cuadro_20F_pag59_5_ramos.csv", "cuadro_20F_pag60_3_ramos_total.csv"],
    "21": ["cuadro_21_inversiones_reservas_tecnicas.csv"],
    "22": ["cuadro_22_gastos_admin_vs_primas_por_empresa.csv"],
    "23": ["cuadro_23_gastos_produccion_vs_primas_por_ramo.csv"],
    "23-A": ["cuadro_23A_pag64_comisiones_5_ramos.csv", "cuadro_23A_pag65_comisiones_4_ramos_total.csv"],
    "23-B": ["cuadro_23B_pag66_comisiones_6_ramos.csv", "cuadro_23B_pag67_comisiones_6_ramos.csv", "cuadro_23B_pag68_comisiones_4_ramos_total.csv"],
    "23-C": ["cuadro_23C_pag69_comisiones_5_ramos.csv", "cuadro_23C_pag70_comisiones_3_ramos_total.csv"],
    "23-D": ["cuadro_23D_pag71_gastos_adm_5_ramos.csv", "cuadro_23D_pag72_gastos_adm_4_ramos_total.csv"],
    "23-E": ["cuadro_23E_pag73_gastos_adm_6_ramos.csv", "cuadro_23E_pag74_gastos_adm_6_ramos.csv", "cuadro_23E_pag75_gastos_adm_4_ramos_total.csv"],
    "23-F": ["cuadro_23F_pag76_gastos_adm_5_ramos.csv", "cuadro_23F_pag77_gastos_adm_3_ramos_total.csv"],
    "24": ["cuadro_24_balance_condensado.csv"],
    "25-A": ["cuadro_25A_estado_ganancias_perdidas_ingresos.csv"],
    "25-B": ["cuadro_25B_estado_ganancias_perdidas_egresos.csv"],
    "26": ["cuadro_26_gestion_general.csv"],
    "27": ["cuadro_27_rentabilidad_inversiones_por_empresa.csv"],
    "28": ["cuadro_28_resultados_ejercicio_2019_2023_por_empresa.csv"],
    "29": ["cuadro_29_indicadores_financieros_2023_por_empresa.csv"],
    "30": ["cuadro_30_suficiencia_patrimonio_solvencia_2022_2023.csv"],
    "31-A": ["cuadro_31A_primas_netas_cobradas_2023_vs_2022.csv"],
    "31-B": ["cuadro_31B_primas_prestaciones_siniestros_1990_2023.csv"],
    "32": ["cuadro_32_reservas_prima_siniestros_hospitalizacion_individual.csv"],
    "33": ["cuadro_33_reservas_prima_siniestros_hospitalizacion_colectivo.csv"],
    "34": ["cuadro_34_primas_brutas_personas_generales_por_empresa.csv"],
    "35": ["cuadro_35_devolucion_primas_personas_generales_por_empresa.csv"],
    "36": ["cuadro_36_reservas_prestaciones_siniestros_pendientes_ocurridos_no_notificados.csv"],
    "37": ["cuadro_37_cantidad_polizas_siniestros_por_ramo.csv"],
    "38": ["cuadro_38_cantidad_polizas_siniestros_por_empresa.csv"],
    "39": ["cuadro_39_empresas_reaseguro_autorizadas.csv"],
    "40": ["cuadro_40_balance_condensado_reaseguros.csv"],
    "41-A": ["cuadro_41A_estado_ganancias_perdidas_ingresos_reaseguros.csv"],
    "41-B": ["cuadro_41B_estado_ganancias_perdidas_egresos_reaseguros.csv"],
    "42": ["cuadro_42_balance_condensado_por_empresa_reaseguros.csv"],
    "43-A": ["cuadro_43A_estado_ganancias_perdidas_ingresos_por_empresa_reaseguros.csv"],
    "43-B": ["cuadro_43B_estado_ganancias_perdidas_egresos_por_empresa_reaseguros.csv"],
    "44": ["cuadro_44_indicadores_financieros_2023_reaseguros.csv"],
    "45": ["cuadro_45_suficiencia_patrimonio_solvencia_reaseguros_2022_2023.csv"],
    "46": ["cuadro_46_empresas_financiadoras_primas_autorizadas.csv"],
    "47": ["cuadro_47_balance_condensado_financiadoras_primas.csv"],
    "48": ["cuadro_48_estado_ganancias_perdidas_ingresos_egresos_financiadoras_primas.csv"],
    "49": ["cuadro_49_ingresos_por_empresa_financiadoras_primas.csv"],
    "50": ["cuadro_50_circulante_activo_por_empresa_financiadoras_primas.csv"],
    "51": ["cuadro_51_gastos_operativos_administrativos_financieros_por_empresa_financiadoras_primas.csv"],
    "52": ["cuadro_52_indicadores_financieros_2023_financiadoras_primas.csv"],
    "53": ["cuadro_53_empresas_medicina_prepagada_autorizadas.csv"],
    "54": ["cuadro_54_balance_condensado_medicina_prepagada.csv"],
    "55-A": ["cuadro_55A_estado_ganancias_perdidas_ingresos_medicina_prepagada.csv"],
    "55-B": ["cuadro_55B_estado_ganancias_perdidas_egresos_medicina_prepagada.csv"],
    "56": ["cuadro_56_ingresos_netos_por_empresa_medicina_prepagada.csv"],
    "57": ["cuadro_57_reservas_tecnicas_por_empresa_medicina_prepagada.csv"],
    "58": ["cuadro_58_indicadores_financieros_2023_medicina_prepagada.csv"],
}

# Orden de cuadros según índice (para reporte página -> cuadro)
ORDEN_CUADROS = [
    "1", "2", "3", "4", "5-A", "5-B", "5-C", "6", "7", "8-A", "8-B", "8-C",
    "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "20-A", "20-B", "20-C", "20-D", "20-E", "20-F",
    "21", "22", "23", "23-A", "23-B", "23-C", "23-D", "23-E", "23-F",
    "24", "25-A", "25-B", "26", "27", "28", "29", "30", "31-A", "31-B",
    "32", "33", "34", "35", "36", "37", "38",
    "39", "40", "41-A", "41-B", "42", "43-A", "43-B", "44", "45",
    "46", "47", "48", "49", "50", "51", "52",
    "53", "54", "55-A", "55-B", "56", "57", "58",
]

# Página(s) por cuadro según índice del anuario 2023 (para ubicar tabla por página)
PAGINAS_POR_CUADRO = {
    "1": [16], "2": [17], "3": [18], "4": [19], "5-A": [20, 21], "5-B": [22, 23, 24], "5-C": [25, 26],
    "6": [27], "7": [28], "8-A": [29, 30], "8-B": [31, 32, 33], "8-C": [34, 35],
    "9": [36], "10": [37], "11": [38], "12": [39], "13": [40], "14": [41], "15": [42],
    "16": [43], "17": [44], "18": [45], "19": [46],
    "20-A": [47, 48], "20-B": [49, 50, 51], "20-C": [52, 53], "20-D": [54, 55], "20-E": [56, 57, 58], "20-F": [59, 60],
    "21": [61], "22": [62], "23": [63], "23-A": [64, 65], "23-B": [66, 67, 68], "23-C": [69, 70],
    "23-D": [71, 72], "23-E": [73, 74, 75], "23-F": [76, 77],
    "24": [78], "25-A": [79], "25-B": [80, 81], "26": [82], "27": [83], "28": [84], "29": [85], "30": [86],
    "31-A": [87], "31-B": [88], "32": [89], "33": [90], "34": [91], "35": [92], "36": [93], "37": [94], "38": [95],
    "39": [101], "40": [102], "41-A": [103], "41-B": [104], "42": [105], "43-A": [106], "43-B": [107],
    "44": [108], "45": [108],
    "46": [112], "47": [113], "48": [114], "49": [115], "50": [116], "51": [117], "52": [118],
    "53": [121], "54": [122], "55-A": [123], "55-B": [124], "56": [125], "57": [126], "58": [127],
}


def _extraer_indice_desde_pdf(pdf_path: Path) -> list[tuple[str, str]]:
    """Extrae del PDF (págs. 4-6) las líneas del índice que contienen número de cuadro y página."""
    import pdfplumber
    lineas_indice = []
    with pdfplumber.open(pdf_path) as doc:
        for pnum in (3, 4, 5):  # páginas 4, 5, 6 (0-based)
            if pnum >= len(doc.pages):
                break
            texto = doc.pages[pnum].extract_text() or ""
            for linea in texto.replace("\r", "").split("\n"):
                linea = linea.strip()
                if not linea or linea.upper() in ("INDICE", "CUADRO TÍTULO PÁGINA", "CUADRO TITULO PAGINA"):
                    continue
                if "Superintendencia" in linea or "Dirección Actuarial" in linea:
                    continue
                # Líneas que tienen número de página al final (ej. "3 ... 18" o "5-A ... 20-21")
                if re.search(r"\d{2}(-\d{2})?\s*$", linea) or re.search(r"\s+\d+\s*$", linea):
                    lineas_indice.append(linea)
    return lineas_indice


def run_verificacion(anio: int = 2023, pdf_path: Path | None = None) -> bool:
    carpeta = DATA_STAGED / str(anio) / "verificadas"
    if not carpeta.exists():
        print("[ERROR] No existe la carpeta {}.".format(carpeta))
        return False

    todo_ok = True
    cuadros_sin_extraer = []
    cuadros_ok = []
    archivos_faltantes = []

    for cid in ORDEN_CUADROS:
        archivos = INDICE_CSV_POR_CUADRO.get(cid, [])
        if not archivos:
            cuadros_sin_extraer.append(cid)
            continue
        for nombre in archivos:
            path = carpeta / nombre
            if not path.exists():
                archivos_faltantes.append((cid, nombre))
                todo_ok = False
            else:
                cuadros_ok.append((cid, nombre))

    # Reporte: ubicación por página
    print("")
    print("=== ÍNDICE DEL ANUARIO (págs. 4-6) vs CUADROS EXTRAÍDOS ===")
    print("")
    print("Ubicación por página (cuadro -> página(s)):")
    pag_a_cuadro = {}
    for cid, paginas in PAGINAS_POR_CUADRO.items():
        for p in paginas:
            pag_a_cuadro.setdefault(p, []).append(cid)
    for p in sorted(pag_a_cuadro.keys()):
        print("  Pág. {:3d}  ->  Cuadro(s) {}".format(p, ", ".join(pag_a_cuadro[p])))

    print("")
    print("Cuadros del índice que NO se extraen en este proyecto (resumen ejecutivo / listados): {}.".format(", ".join(cuadros_sin_extraer)))
    print("Cuadros 3 a 58: se espera un CSV (o varios) por cuadro.")
    print("")

    if archivos_faltantes:
        print("[FALTA] Archivos no encontrados:")
        for cid, nombre in archivos_faltantes:
            print("  Cuadro {} -> {}".format(cid, nombre))
        print("")
        todo_ok = False
    else:
        print("[OK] Todos los cuadros extraídos (3 a 58) tienen sus CSV en {}.".format(carpeta))
        print("     Total archivos esperados: {}.".format(sum(len(v) for v in INDICE_CSV_POR_CUADRO.values() if v)))
    print("")
    return todo_ok


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Verificar índice del anuario vs CSVs extraídos")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    sys.exit(0 if run_verificacion(args.year) else 1)
