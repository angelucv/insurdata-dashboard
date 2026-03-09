"""
Descarga todos los anuarios/cifras anuales desde SUDEASEG (desde 1967 si están disponibles).
Guarda en data/raw/anuario/pdf y data/raw/anuario/xlsx.
Lista enlaces en data/audit/manifest/descargas.csv para trazabilidad.
"""
import sys
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW, ANUARIO_YEAR_MIN
from config.audit_paths import MANIFEST_LINKS_CSV, DATA_AUDIT_MANIFEST
from src.extraction.scraper import SudeasegScraper


def main():
    print("=== Descarga de anuarios SUDEASEG (cifras anuales) ===\n")
    scraper = SudeasegScraper(out_dir=DATA_RAW)
    links = scraper.crawl_anuarios(year_min=ANUARIO_YEAR_MIN)
    print(f"Enlaces encontrados en sección anuarios: {len(links)}")
    if not links:
        print("No se encontraron enlaces. Revisa SUDEASEG_ANUARIOS_PATH y conectividad.")
        return
    DATA_AUDIT_MANIFEST.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_LINKS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["url", "text", "extension", "inferred_years", "is_anuario", "downloaded"])
    downloaded = scraper.download_anuarios(year_min=ANUARIO_YEAR_MIN, subdir="anuario")
    downloaded_names = {Path(p).name for p in downloaded}
    print(f"Archivos descargados: {len(downloaded)}")
    for p in downloaded[:20]:
        print(f"  {p}")
    if len(downloaded) > 20:
        print(f"  ... y {len(downloaded) - 20} más")
    # Escribir manifest con estado por enlace (por nombre de archivo en URL)
    from urllib.parse import urlparse
    with open(MANIFEST_LINKS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["url", "text", "extension", "inferred_years", "is_anuario", "downloaded"])
        for link in links:
            url = link.get("url", "")
            name = Path(urlparse(url).path).name
            w.writerow([
                url,
                link.get("text", ""),
                link.get("extension", ""),
                "|".join(map(str, link.get("inferred_years", []))),
                link.get("is_anuario", False),
                "yes" if name in downloaded_names else "no",
            ])
    print(f"\nListado de enlaces guardado en: {MANIFEST_LINKS_CSV}")


if __name__ == "__main__":
    main()
