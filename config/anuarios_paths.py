"""Rutas para la estructura Seguro en Cifras (anuarios) en disco."""
from pathlib import Path

from config.settings import DATA_AUDIT, DATA_RAW

# Raíz de la estructura solo para anuarios
SEGURO_EN_CIFRAS_ROOT = DATA_AUDIT / "seguro_en_cifras"
SEGURO_EN_CIFRAS_INDICE = SEGURO_EN_CIFRAS_ROOT / "indice"
SEGURO_EN_CIFRAS_ENTIDADES = SEGURO_EN_CIFRAS_ROOT / "entidades"
SEGURO_EN_CIFRAS_VARIABLES = SEGURO_EN_CIFRAS_ROOT / "variables"
SEGURO_EN_CIFRAS_VACIADO = SEGURO_EN_CIFRAS_ROOT / "vaciado"
SEGURO_EN_CIFRAS_RAW = SEGURO_EN_CIFRAS_ROOT / "raw"

CANONICO_CSV = SEGURO_EN_CIFRAS_VARIABLES / "canonico.csv"
INDICE_CUADROS_CSV = SEGURO_EN_CIFRAS_VARIABLES / "indice_cuadros.csv"

# Archivos de salida
INDICE_FUENTES_CSV = SEGURO_EN_CIFRAS_INDICE / "anuario_fuentes.csv"
ENTIDADES_CSV = SEGURO_EN_CIFRAS_ENTIDADES / "anuario_entidades.csv"
METRICAS_CSV = SEGURO_EN_CIFRAS_VACIADO / "anuario_metricas.csv"
VACIADO_ENTIDADES_CSV = SEGURO_EN_CIFRAS_VACIADO / "anuario_entidades.csv"


def ensure_anuarios_dirs() -> None:
    for d in (
        SEGURO_EN_CIFRAS_ROOT,
        SEGURO_EN_CIFRAS_INDICE,
        SEGURO_EN_CIFRAS_ENTIDADES,
        SEGURO_EN_CIFRAS_VARIABLES,
        SEGURO_EN_CIFRAS_VACIADO,
        SEGURO_EN_CIFRAS_RAW,
    ):
        d.mkdir(parents=True, exist_ok=True)
