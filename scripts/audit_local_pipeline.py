"""
Pipeline de auditoría 100% local: extrae todos los Excel y PDF de data/raw
a la estructura espejo (data/audit/mirror) y by_source, sin tocar la base de datos.
Ejecutar antes de cargar a Supabase para revisión y arqueo.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW
from src.etl.audit_local import run_audit_pipeline


def main():
    print("=== Pipeline de auditoría local (estructura espejo) ===\n")
    print(f"Origen: {DATA_RAW}")
    stats = run_audit_pipeline(DATA_RAW)
    print(f"\nResultado:")
    print(f"  Filas primas_mensuales (espejo): {stats['primas_rows']}")
    print(f"  Entidades únicas: {stats['entities']}")
    print(f"  Excel procesados: {stats['excel_processed']}")
    print(f"  PDF procesados: {stats['pdf_processed']}")
    print(f"  Manifest: {stats['manifest_path']}")
    print("\nSiguiente paso: python scripts/audit_verificar_campos.py")


if __name__ == "__main__":
    main()
