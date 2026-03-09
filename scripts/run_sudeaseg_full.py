# scripts/run_sudeaseg_full.py
"""Pipeline completo SUDEASEG: 1) Extracción (scraping), 2) ETL y carga a Supabase."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW
from src.extraction.scraper import SudeasegScraper
from src.etl.sudeaseg_to_supabase import run_full_pipeline


def main():
    print("=== 1) Extracción: buscando y descargando archivos SUDEASEG ===\n")
    scraper = SudeasegScraper()
    links = scraper.crawl_statistics_section()
    if not links:
        links = scraper.crawl_all_estadisticas()
    if links:
        paths = scraper.download_all(links)
        print(f"Descargados {len(paths)} archivos en data/raw/\n")
    else:
        print("No se encontraron enlaces. Usando archivos ya presentes en data/raw/\n")

    print("=== 2) ETL y carga a Supabase ===\n")
    stats = run_full_pipeline(DATA_RAW)
    print(f"\nResumen: {stats['excel']} Excel, {stats['pdf']} PDF procesados -> {stats['primas_rows']} filas en primas_mensuales.")
    print("Refresca el dashboard (streamlit run app.py) para ver los datos.")


if __name__ == "__main__":
    main()
