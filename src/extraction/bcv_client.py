# src/extraction/bcv_client.py
"""Cliente para tasas de cambio BCV / DolarApi. Normalización monetaria VES -> USD."""
import re
from datetime import date
from typing import Any

import requests

from config.settings import BCV_URL, DOLAR_API_BASE


class BCVClient:
    """
    Obtiene tasas de cambio oficiales para normalizar montos en VES a USD.
    Usa DolarApi.com (rutas /ve) o scraping BCV como respaldo.
    """

    def __init__(self, api_base: str | None = None):
        self.api_base = (api_base or DOLAR_API_BASE).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SUDEASEG-DataPipeline/1.0",
            "Accept": "application/json",
        })

    def _dolarapi_ve(self, endpoint: str = "dolares") -> list[dict] | None:
        """GET a DolarApi: /v1/dolares o rutas específicas para Venezuela si existen."""
        try:
            # DolarApi: ej. /v1/dolares para Argentina; para VE a veces /ve/dolar
            url = f"{self.api_base}/v1/{endpoint}"
            r = self.session.get(url, timeout=10)
            if r.status_code != 200:
                return None
            data = r.json()
            return data if isinstance(data, list) else [data]
        except Exception as e:
            print(f"[BCV] DolarApi error: {e}")
            return None

    def get_rate_from_bcv_page(self, d: date) -> float | None:
        """
        Scraping básico a bcv.org.ve para la tasa del día.
        La página suele tener un elemento con la tasa oficial; ajustar selectores según DOM actual.
        """
        try:
            # URL típica de consulta por fecha (puede variar en el sitio)
            url = f"{BCV_URL}/estadisticas/tipo-cambio"
            r = self.session.get(url, timeout=15)
            if r.status_code != 200:
                return None
            text = r.text
            # Heurística: buscar número con decimales (tasa)
            match = re.search(r"(\d+[,.]\d{2,4})", text.replace(",", "."))
            if match:
                return float(match.group(1))
        except Exception as e:
            print(f"[BCV] Scraping BCV error: {e}")
        return None

    def get_rate_ves_usd(self, d: date) -> float | None:
        """
        Devuelve la tasa VES/USD para la fecha d.
        Prioridad: DolarApi (si hay ruta VE) > scraping BCV.
        """
        # Intentar API externa con ruta Venezuela si existe
        try:
            # Ejemplo: algunos servicios exponen /ve/dolar/oficial?date=YYYY-MM-DD
            url = f"{self.api_base}/ve/dolar/oficial"
            r = self.session.get(url, params={"date": d.isoformat()}, timeout=10)
            if r.status_code == 200:
                j = r.json()
                if isinstance(j, dict) and "venta" in j:
                    return float(j["venta"])
                if isinstance(j, dict) and "valor" in j:
                    return float(j["valor"])
        except Exception:
            pass
        return self.get_rate_from_bcv_page(d)

    def convert_ves_to_usd(self, amount_ves: float, rate: float | None) -> float | None:
        """Convierte monto en VES a USD. Si rate es None, devuelve None."""
        if rate is None or rate <= 0:
            return None
        return amount_ves / rate
