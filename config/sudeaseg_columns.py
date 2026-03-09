# config/sudeaseg_columns.py
"""Mapeo de columnas típicas de archivos SUDEASEG (Excel/PDF) al esquema de la BD."""

# Posibles nombres en archivos SUDEASEG -> nombre en primas_mensuales / entities
COLUMN_MAPPING = {
    # Entidad / empresa
    "empresa": "entity_name",
    "entidad": "entity_name",
    "razon_social": "entity_name",
    "aseguradora": "entity_name",
    "nombre": "entity_name",
    # Periodo
    "periodo": "periodo",
    "mes": "periodo",
    "fecha": "periodo",
    "anio": "anio",
    "año": "anio",
    # Primas
    "primas_netas": "primas_netas_ves",
    "primas_netas_ves": "primas_netas_ves",
    "primas_netas_cobradas": "primas_netas_ves",
    "primas netas": "primas_netas_ves",
    # Siniestros
    "siniestros_pagados": "siniestros_pagados_ves",
    "siniestros_pagados_ves": "siniestros_pagados_ves",
    "siniestros": "siniestros_pagados_ves",
    # Gastos
    "gastos_operativos": "gastos_operativos_ves",
    "gastos_operativos_ves": "gastos_operativos_ves",
}

# Columnas esperadas en primas_mensuales para insert en Supabase
PRIMAS_MENSUALES_COLUMNS = [
    "entity_id",
    "periodo",
    "primas_netas_ves",
    "primas_netas_usd",
    "siniestros_pagados_ves",
    "siniestros_pagados_usd",
    "gastos_operativos_ves",
    "gastos_operativos_usd",
]
