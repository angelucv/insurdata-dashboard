"""
Construye el índice de fuentes de anuarios Seguro en Cifras y ejecuta el vaciado inicial
(por ahora Excel 2024). Salida en data/audit/seguro_en_cifras/.
"""
import sys
from pathlib import Path

# Raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.anuarios_paths import INDICE_FUENTES_CSV, VACIADO_ENTIDADES_CSV, METRICAS_CSV
from src.etl.anuarios_seguro_en_cifras import build_indice_fuentes, run_vaciado_inicial


def main():
    print("Seguro en Cifras - Indice y vaciado inicial")
    print("=" * 50)
    build_indice_fuentes()
    print("Indice escrito:", INDICE_FUENTES_CSV)
    result = run_vaciado_inicial()
    print("Entidades (2024):", result.get("entidades", 0))
    print("Metricas (2024):", result.get("metricas", 0))
    print("Entidades CSV:", result.get("entidades_csv", VACIADO_ENTIDADES_CSV))
    print("Metricas CSV:", result.get("metricas_csv", METRICAS_CSV))
    if result.get("message"):
        print("Nota:", result["message"])


if __name__ == "__main__":
    main()
