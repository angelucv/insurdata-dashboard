# src/etl/tasas_cambio.py
"""
Tasas de cambio anuales para conversión de montos (miles Bs/BsF/BsS/VES) a USD.
- BCV oficial: cierre (stock) y promedio (flujo primas).
- Tasa mercado sugerida: para siniestros pagados (siniestralidad real).
- Normalización a unidad 2024: factor 10^11 (2014-2017), 10^6 (2018-2020), 1 (2021+).
"""
from pathlib import Path
from typing import NamedTuple

from config.settings import BASE_DIR

VARIABLES_DIR = (
    BASE_DIR / "data" / "audit" / "seguro_en_cifras" / "variables"
)
TASA_CAMBIO_ANUAL_CSV = VARIABLES_DIR / "tasa_cambio_anual.csv"
TASA_BCV_2014_2024_CSV = VARIABLES_DIR / "tasa_cambio_bcv_2014_2024.csv"

# Métricas de stock: tasa BCV cierre.
METRICAS_STOCK = frozenset({
    "reservas_tecnicas", "reservas_primas", "reservas_siniestros_pendientes",
    "capital_garantia", "capital_pagado", "garantia_deposito",
    "activo_total", "pasivo_total", "inversiones_reservas", "balance_condensado",
})
# Siniestros: tasa mercado sugerida (siniestralidad real).
METRICAS_SINIESTROS = frozenset({"siniestros_pagados"})
# Resto flujo: tasa BCV promedio.
METRICAS_FLUJO = frozenset({
    "primas_netas_cobradas", "primas_netas_por_ramo",
    "comisiones_gastos_adquisicion", "resultados_economicos",
    "ingresos_netos", "gastos_operativos", "gastos_administracion", "gastos_produccion",
})

_tasas_cache: dict[int, float] | None = None
# anio -> (tasa_bcv_cierre, tasa_bcv_promedio, tasa_mercado_cierre, factor_ajuste, unidad)
_bcv_cache: dict[int, tuple[float, float, float, float, str]] | None = None


class ResultadoConversion(NamedTuple):
    """Valor original y valor en USD; indica si se usó tasa BCV o mercado."""
    valor_miles: float
    valor_unidades_anio: float
    valor_usd: float | None
    tasa_usada: float | None
    es_flujo: bool
    uso_tasa_mercado: bool  # True si se usó tasa mercado (siniestros)
    unidad_monetaria: str


def _load_tasas_legacy() -> dict[int, float]:
    """Carga tasa única desde tasa_cambio_anual.csv (años anteriores a 2014)."""
    out: dict[int, float] = {}
    if not TASA_CAMBIO_ANUAL_CSV.exists():
        return out
    import csv
    with open(TASA_CAMBIO_ANUAL_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                anio = int(row["anio"])
                tasa = float(row["tasa_unidades_por_usd"])
                if tasa > 0:
                    out[anio] = tasa
            except (ValueError, KeyError):
                continue
    return out


def _parse_factor(s: str) -> float:
    """Convierte '1e11', '1e6', '1' a float."""
    s = str(s).strip()
    if not s or s == "1":
        return 1.0
    try:
        return float(s)
    except ValueError:
        return 1.0


def _load_bcv_2014_2024() -> dict[int, tuple[float, float, float, float, str]]:
    """Carga BCV + tasa mercado + factor de ajuste desde CSV."""
    out: dict[int, tuple[float, float, float, float, str]] = {}
    if not TASA_BCV_2014_2024_CSV.exists():
        return out
    import csv
    with open(TASA_BCV_2014_2024_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                anio = int(row["anio"])
                # Nuevo formato: tasa_bcv_cierre, tasa_bcv_promedio, tasa_mercado_cierre, factor_ajuste_ceros
                cierre = float(row.get("tasa_bcv_cierre", row.get("tasa_cierre_bs_usd", 0)))
                prom = float(row.get("tasa_bcv_promedio", row.get("tasa_promedio_bs_usd", 0)))
                mercado = float(row.get("tasa_mercado_cierre", cierre))
                factor = _parse_factor(row.get("factor_ajuste_ceros", "1"))
                unidad = str(row.get("unidad_monetaria", "Bs.")).strip()
                if cierre > 0 and prom > 0:
                    out[anio] = (cierre, prom, mercado, factor, unidad)
            except (ValueError, KeyError):
                continue
    return out


def load_tasas_anuales() -> dict[int, float]:
    """Carga tasas únicas (legacy): anio -> unidades por 1 USD."""
    global _tasas_cache
    if _tasas_cache is not None:
        return _tasas_cache
    _tasas_cache = _load_tasas_legacy()
    return _tasas_cache


def load_tasas_bcv_cierre_promedio() -> dict[int, tuple[float, float, float, float, str]]:
    """Carga (bcv_cierre, bcv_promedio, mercado_cierre, factor_ajuste, unidad) 2014-2024."""
    global _bcv_cache
    if _bcv_cache is not None:
        return _bcv_cache
    _bcv_cache = _load_bcv_2014_2024()
    return _bcv_cache


def get_tasa_cierre(anio: int) -> float | None:
    """Tasa BCV cierre (31-Dic) para variables de stock."""
    bcv = load_tasas_bcv_cierre_promedio()
    if anio in bcv:
        return bcv[anio][0]
    return load_tasas_anuales().get(anio)


def get_tasa_promedio(anio: int) -> float | None:
    """Tasa BCV promedio anual para flujo (primas, etc.)."""
    bcv = load_tasas_bcv_cierre_promedio()
    if anio in bcv:
        return bcv[anio][1]
    return load_tasas_anuales().get(anio)


def get_tasa_mercado(anio: int) -> float | None:
    """Tasa mercado sugerida (cierre) para siniestros pagados — siniestralidad real."""
    bcv = load_tasas_bcv_cierre_promedio()
    if anio in bcv:
        return bcv[anio][2]
    return get_tasa_cierre(anio) or load_tasas_anuales().get(anio)


def get_factor_ajuste(anio: int) -> float:
    """Factor para normalizar a unidad 2024: 10^11 (2014-17), 10^6 (2018-20), 1 (2021+)."""
    bcv = load_tasas_bcv_cierre_promedio()
    if anio in bcv:
        return bcv[anio][3]
    if 2014 <= anio <= 2017:
        return 1e11
    if 2018 <= anio <= 2020:
        return 1e6
    return 1.0


def get_tasa_para_metrica(anio: int, metric_name: str) -> tuple[float | None, bool, bool]:
    """
    Devuelve (tasa, es_flujo, uso_tasa_mercado).
    Siniestros → tasa mercado; resto flujo → BCV promedio; stock → BCV cierre.
    """
    if metric_name in METRICAS_SINIESTROS:
        return (get_tasa_mercado(anio), True, True)
    if metric_name in METRICAS_FLUJO:
        return (get_tasa_promedio(anio), True, False)
    if metric_name in METRICAS_STOCK:
        return (get_tasa_cierre(anio), False, False)
    return (get_tasa_promedio(anio) or get_tasa_cierre(anio), True, False)


def get_unidad_monetaria_anio(anio: int) -> str:
    """Etiqueta de unidad monetaria del año."""
    bcv = load_tasas_bcv_cierre_promedio()
    if anio in bcv:
        return bcv[anio][4]
    if anio >= 2018:
        return "Bs.S"
    if anio >= 2008:
        return "Bs.F"
    return "Bs"


def normalizar_a_unidad_2024(value_miles: float, anio: int) -> float:
    """
    Convierte valor en miles (unidad del anuario) a Bs. actual (unidad 2024).
    value_miles * 1000 / factor_ajuste (10^11, 10^6 o 1).
    """
    factor = get_factor_ajuste(anio)
    if factor <= 0:
        return 0.0
    return (float(value_miles) * 1000.0) / factor


def convert_miles_local_to_usd(
    value_miles: float,
    anio: int,
    es_flujo: bool = True,
    usar_tasa_mercado: bool = False,
) -> float | None:
    """
    Convierte valor en 'miles de bolívares' a USD.
    es_flujo: tasa promedio (flujo) vs cierre (stock). usar_tasa_mercado: para siniestros.
    """
    if usar_tasa_mercado:
        tasa = get_tasa_mercado(anio)
    else:
        tasa = get_tasa_promedio(anio) if es_flujo else get_tasa_cierre(anio)
    if tasa is None:
        tasa = load_tasas_anuales().get(anio)
    if tasa is None or tasa <= 0:
        return None
    return (float(value_miles) * 1000.0) / tasa


def convertir_con_valor_original(
    value_miles: float,
    anio: int,
    metric_name: str,
) -> ResultadoConversion:
    """
    Convierte a USD: siniestros con tasa mercado; resto según stock/flujo BCV.
    Devuelve valor original + USD + indicador de tasa usada.
    """
    tasa, es_flujo, uso_mercado = get_tasa_para_metrica(anio, metric_name)
    valor_unidades = float(value_miles) * 1000.0
    valor_usd = (valor_unidades / tasa) if (tasa and tasa > 0) else None
    unidad = get_unidad_monetaria_anio(anio)
    return ResultadoConversion(
        valor_miles=float(value_miles),
        valor_unidades_anio=valor_unidades,
        valor_usd=valor_usd,
        tasa_usada=tasa,
        es_flujo=es_flujo,
        uso_tasa_mercado=uso_mercado,
        unidad_monetaria=unidad,
    )


def get_tasa_anio(anio: int) -> float | None:
    """Tasa única (legacy). Preferir get_tasa_promedio / get_tasa_mercado según métrica."""
    return get_tasa_promedio(anio) or get_tasa_cierre(anio) or load_tasas_anuales().get(anio)


def convert_miles_to_usd_equivalente_2024(
    value_miles: float,
    anio: int,
    tasa_usd_2024: float | None = None,
) -> float | None:
    """
    Convierte valor en miles (unidad del año) a USD usando unidad 2024 y tasa 2024.
    Evita saltos por reconversión: primero normaliza a Bs. actual (÷ factor), luego ÷ tasa 2024.
    Si no se pasa tasa_usd_2024, se usa tasa BCV cierre 2024.
    """
    valor_bs_actual = normalizar_a_unidad_2024(value_miles, anio)
    tasa = tasa_usd_2024 if tasa_usd_2024 is not None and tasa_usd_2024 > 0 else get_tasa_cierre(2024)
    if tasa is None or tasa <= 0:
        return None
    return valor_bs_actual / tasa


def clear_cache() -> None:
    """Limpia cachés."""
    global _tasas_cache, _bcv_cache
    _tasas_cache = None
    _bcv_cache = None
