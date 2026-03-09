# src/etl/entity_resolver.py
"""Catálogo maestro de entidades (aseguradoras): normalización y UUID/ID estable."""
import uuid
from pathlib import Path

import pandas as pd

from .transformers import normalize_entity_name


class EntityResolver:
    """
    Asigna un identificador estable a cada entidad (razón social) a pesar de
    variaciones nominales en el tiempo (fusiones, typos, etc.).
    """

    def __init__(self, lookup_path: Path | None = None):
        self.lookup_path = lookup_path
        self._map: dict[str, str] = {}  # nombre_normalizado -> uuid
        self._reverse: dict[str, str] = {}  # uuid -> nombre_canonico (opcional)
        self._load()

    def _load(self) -> None:
        if self.lookup_path and Path(self.lookup_path).exists():
            try:
                df = pd.read_csv(self.lookup_path)
                if "normalized" in df.columns and "entity_id" in df.columns:
                    self._map = dict(zip(df["normalized"], df["entity_id"]))
                if "entity_id" in df.columns and "canonical_name" in df.columns:
                    self._reverse = dict(zip(df["entity_id"], df["canonical_name"]))
            except Exception as e:
                print(f"[EntityResolver] Error cargando lookup: {e}")

    def resolve(self, raw_name: str) -> str:
        """
        Devuelve el entity_id (UUID) para la razón social.
        Si no existe, crea uno nuevo y lo registra en memoria.
        """
        key = normalize_entity_name(raw_name)
        if not key:
            key = "_empty"
        if key not in self._map:
            self._map[key] = str(uuid.uuid4())
            self._reverse[self._map[key]] = raw_name.strip()
        return self._map[key]

    def get_canonical_name(self, entity_id: str) -> str:
        """Devuelve el nombre canónico registrado para ese ID."""
        return self._reverse.get(entity_id, entity_id)

    def save_lookup(self, path: Path | None = None) -> None:
        """Persiste el catálogo en CSV."""
        path = path or self.lookup_path
        if not path:
            return
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            {"normalized": k, "entity_id": v, "canonical_name": self._reverse.get(v, k)}
            for k, v in self._map.items()
        ]
        pd.DataFrame(rows).to_csv(path, index=False)
