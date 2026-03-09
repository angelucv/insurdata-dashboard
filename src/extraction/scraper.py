# src/extraction/scraper.py
"""Raspado web del portal SUDEASEG para localizar y descargar PDF y XLSX."""
import re
import time
import random
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config.settings import (
    SUDEASEG_BASE_URL,
    SUDEASEG_ESTADISTICAS_PATH,
    SUDEASEG_CRAWL_PATHS,
    SUDEASEG_ANUARIOS_PATH,
    ANUARIO_YEAR_MIN,
    DATA_RAW,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    USER_AGENT,
)


class SudeasegScraper:
    """Extrae enlaces a archivos .pdf y .xlsx del portal de estadísticas SUDEASEG."""

    EXTENSIONS = (".pdf", ".xlsx", ".xls")
    HEADERS = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-VE,es;q=0.9,en;q=0.8",
    }

    def __init__(self, base_url: str | None = None, out_dir: Path | None = None):
        self.base_url = base_url or SUDEASEG_BASE_URL
        self.out_dir = out_dir or DATA_RAW
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _delay(self) -> None:
        """Cadencia aleatoria para simular comportamiento humano."""
        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

    def get_page(self, url: str) -> str | None:
        """Obtiene el HTML de una URL con manejo de errores."""
        try:
            self._delay()
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            print(f"[Scraper] Error al obtener {url}: {e}")
            return None

    def _normalize_download_url(self, full_url: str) -> str:
        """
        Si la URL resolvió a un host distinto de SUDEASEG (ej. http://Descargas/...),
        reescribe usando el dominio base de SUDEASEG para que la descarga funcione.
        El portal suele servir archivos bajo /Descargas/ en el mismo dominio.
        """
        parsed = urlparse(full_url)
        expected_netloc = urlparse(self.base_url).netloc.lower()
        if parsed.netloc and parsed.netloc.lower() != expected_netloc:
            path = parsed.path if parsed.path.startswith("/") else "/" + parsed.path
            # Si el host era "Descargas", el path real suele ser /Descargas/Estadisticas/...
            if "descargas" in parsed.netloc.lower() and not path.lower().startswith("/descargas"):
                path = "/Descargas" + path
            base = self.base_url.rstrip("/")
            full_url = f"{base}{path}"
            if parsed.query:
                full_url += "?" + parsed.query
        return full_url

    def extract_links(self, html: str, base: str | None = None) -> list[dict]:
        """
        Extrae todos los enlaces que apuntan a .pdf, .xlsx o .xls.
        Retorna lista de dicts con url, text, extension.
        """
        base = base or self.base_url
        soup = BeautifulSoup(html, "lxml")
        links = []
        seen = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#"):
                continue
            full_url = urljoin(base, href)
            full_url = self._normalize_download_url(full_url)
            path = urlparse(full_url).path.lower()
            ext = None
            for e in self.EXTENSIONS:
                if path.endswith(e) or e in path:
                    ext = e
                    break
            if ext and full_url not in seen:
                seen.add(full_url)
                links.append({
                    "url": full_url,
                    "text": (a.get_text() or "").strip(),
                    "extension": ext,
                })
        return links

    def crawl_statistics_section(self) -> list[dict]:
        """Navega a la sección de estadísticas y devuelve enlaces a archivos."""
        url = urljoin(self.base_url, SUDEASEG_ESTADISTICAS_PATH)
        html = self.get_page(url)
        if not html:
            return []
        return self.extract_links(html, url)

    def crawl_all_estadisticas(self) -> list[dict]:
        """Recorre todas las rutas en SUDEASEG_CRAWL_PATHS y devuelve enlaces únicos a PDF/XLSX."""
        seen_urls = set()
        all_links = []
        for path in SUDEASEG_CRAWL_PATHS:
            url = urljoin(self.base_url, path)
            html = self.get_page(url)
            if not html:
                continue
            for link in self.extract_links(html, url):
                if link["url"] not in seen_urls:
                    seen_urls.add(link["url"])
                    all_links.append(link)
        return all_links

    def download_file(self, url: str, subdir: str = "") -> Path | None:
        """
        Descarga un archivo y lo guarda en out_dir/subdir.
        Retorna la ruta del archivo o None si falla.
        """
        try:
            self._delay()
            r = self.session.get(url, timeout=60, stream=True)
            r.raise_for_status()
            name = Path(urlparse(url).path).name or "download"
            if not re.search(r"\.(pdf|xlsx|xls)$", name, re.I):
                name += ".bin"
            dest_dir = self.out_dir / subdir if subdir else self.out_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            path = dest_dir / name
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
        except Exception as e:
            print(f"[Scraper] Error descargando {url}: {e}")
            return None

    def download_all(self, links: list[dict] | None = None) -> list[Path]:
        """Descarga todos los archivos encontrados (o la lista pasada)."""
        if links is None:
            links = self.crawl_statistics_section()
        paths = []
        for item in links:
            ext = item.get("extension", "").replace(".", "")
            path = self.download_file(item["url"], subdir=ext)
            if path:
                paths.append(path)
        return paths

    @staticmethod
    def _year_from_text(url: str, text: str) -> list[int]:
        """Extrae años mencionados en URL o texto (ej. 1967, 1999-2004)."""
        combined = f"{url} {text}"
        years = re.findall(r"19[6-9]\d|20[0-4]\d", combined)
        return sorted(set(int(y) for y in years))

    def crawl_anuarios(self, year_min: int | None = None) -> list[dict]:
        """
        Recorre la sección de cifras anuales / anuarios y devuelve enlaces a PDF/XLSX.
        Incluye en cada link años inferidos (inferred_years) para filtrar por año mínimo.
        """
        year_min = year_min if year_min is not None else ANUARIO_YEAR_MIN
        url = urljoin(self.base_url, SUDEASEG_ANUARIOS_PATH)
        html = self.get_page(url)
        if not html:
            return []
        links = self.extract_links(html, url)
        for item in links:
            item["inferred_years"] = self._year_from_text(item["url"], item.get("text", ""))
            item["is_anuario"] = any(y >= year_min for y in item["inferred_years"]) or "anuario" in (item.get("text", "") + item["url"]).lower()
        return links

    def list_all_for_audit(self) -> list[dict]:
        """
        Lista todos los enlaces de estadísticas (todas las rutas) con metadatos
        para auditoría: url, text, extension, inferred_years, source_path.
        """
        result = []
        seen = set()
        for path in SUDEASEG_CRAWL_PATHS:
            url = urljoin(self.base_url, path)
            html = self.get_page(url)
            if not html:
                continue
            for link in self.extract_links(html, url):
                if link["url"] in seen:
                    continue
                seen.add(link["url"])
                link = dict(link)
                link["inferred_years"] = self._year_from_text(link["url"], link.get("text", ""))
                link["source_path"] = path
                result.append(link)
        return result

    def download_anuarios(self, year_min: int | None = None, subdir: str = "anuarios") -> list[Path]:
        """Descarga todos los archivos de la sección anuarios (cifras anuales) desde year_min."""
        links = self.crawl_anuarios(year_min=year_min)
        paths = []
        for item in links:
            ext = item.get("extension", "").replace(".", "")
            folder = f"{subdir}/{ext}" if ext else subdir
            path = self.download_file(item["url"], subdir=folder)
            if path:
                paths.append(path)
        return paths
