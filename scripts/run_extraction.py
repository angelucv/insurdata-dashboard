# scripts/run_extraction.py
"""Orquesta la extracción: scraping SUDEASEG, descarga de PDF/XLSX."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.extraction.scraper import SudeasegScraper

def main():
    scraper = SudeasegScraper()
    print("Buscando enlaces en la sección de estadísticas SUDEASEG...")
    links = scraper.crawl_statistics_section()
    if not links:
        print("Probando todas las rutas configuradas (cifras-mensuales, boletín, etc.)...")
        links = scraper.crawl_all_estadisticas()
    if not links:
        print("No se encontraron enlaces. Coloca PDF/XLSX en data/raw/ o revisa SUDEASEG_BASE_URL.")
        return
    print(f"Encontrados {len(links)} archivos. Descargando...")
    paths = scraper.download_all(links)
    print(f"Descargados {len(paths)} archivos en data/raw/.")

if __name__ == "__main__":
    main()
