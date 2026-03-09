"""
Normalizacion de nombres para la base madre (ventana 2014-2024).
Unifica variantes como "adriatica de seguros c a" y "adriatica de seguros" en una misma clave.
"""
from __future__ import annotations

import re
import unicodedata


def normalize_entity_name_base(s: str) -> str:
    """Misma base que transformers.normalize_entity_name: minusculas, sin tildes, sin puntuacion."""
    if s is None or (isinstance(s, float) and str(s) == "nan"):
        return ""
    s = str(s).lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Sufijos y prefijos que se eliminan para obtener la clave base madre (evitar duplicados por C.A., S.A., etc.)
SUFIJOS_QUITAR = [
    r"\s+c\s*a\s*$",           # " c a" al final
    r"\s+s\s*a\s*$",           # " s a" al final
    r"\s+la\s*$",              # " la" al final (F C A Seguros La)
    r"\s+los\s*$",             # " los" al final (Andes C A Seguros Los)
    r"\s+de\s+seguros\s*$",    # " de seguros" al final si ya hay "seguros" antes
]
SUFIJOS_QUITAR_COMPILED = [re.compile(p, re.I) for p in SUFIJOS_QUITAR]


def normalize_para_base_madre(nombre: str) -> str:
    """
    Normalizacion para la base madre: aplica normalizacion base y luego
    quita sufijos redundantes (C.A., S.A., La, Los) para unificar variantes
    de la misma compania.
    """
    s = normalize_entity_name_base(nombre)
    if not s:
        return s
    # Quitar sufijos en orden
    for pat in SUFIJOS_QUITAR_COMPILED:
        s = pat.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
