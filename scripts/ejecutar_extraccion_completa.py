"""
Ejecuta el flujo completo de extracción:
1) Verifica que se pueda extraer de PDFs escaneados (OCR).
2) Fase cruda: extrae todo Excel y PDF a data/audit/by_source (y pdf_text).
3) Fase mapeada: construye estructura coherente (mirror) para carga en nube.
4) Verificación de campos compilados.

Todo en disco (data/raw → data/audit). No toca la base de datos.
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PY = ROOT / "venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = sys.executable


def run_script(name: str) -> bool:
    path = ROOT / "scripts" / name
    if not path.exists():
        print(f"  No encontrado: {path}")
        return False
    r = subprocess.run([str(PY), str(path)], cwd=str(ROOT))
    return r.returncode == 0


def main():
    print("=" * 60)
    print("EXTRACCIÓN COMPLETA: crudo + estructura coherente (espejo)")
    print("=" * 60)

    # 1) Verificación PDF escaneados
    print("\n[1/4] Verificación de extracción en PDF (incl. escaneados con OCR)...")
    run_script("verificar_pdf_escaneados.py")
    print()

    # 2) Conteo de archivos en disco
    from config.settings import DATA_RAW
    excel_files = list(DATA_RAW.rglob("*.xlsx")) + list(DATA_RAW.rglob("*.xls"))
    pdf_files = list(DATA_RAW.rglob("*.pdf"))
    print(f"[2/4] Archivos en disco: {len(excel_files)} Excel, {len(pdf_files)} PDF")
    if not excel_files and not pdf_files:
        print("  No hay archivos en data/raw. Descarga datos primero.")
        return
    print()

    # 3) Pipeline: crudo + mapeo a estructura coherente
    print("[3/4] Pipeline: extraccion cruda -> mapeo a estructura coherente (mirror)...")
    from src.etl.audit_local import run_audit_pipeline
    stats = run_audit_pipeline(DATA_RAW)
    print(f"  Filas primas_mensuales (espejo): {stats['primas_rows']}")
    print(f"  Entidades únicas: {stats['entities']}")
    print(f"  Excel procesados: {stats['excel_processed']}")
    print(f"  PDF procesados: {stats['pdf_processed']}")
    print(f"  Manifest: {stats['manifest_path']}")
    print()

    # 4) Verificación de campos
    print("[4/4] Verificación de campos compilados...")
    run_script("audit_verificar_campos.py")

    print("\n" + "=" * 60)
    print("Siguiente paso: cargar a la base de datos con run_etl_to_supabase.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
