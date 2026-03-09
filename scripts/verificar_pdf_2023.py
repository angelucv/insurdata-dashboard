# scripts/verificar_pdf_2023.py
"""
Verifica que los datos del año 2023 convertidos desde PDF (Boletín en Cifras)
hayan sido extraídos de manera correcta.

Uso (desde la raíz del proyecto sudeaseg-dashboard):
  python scripts/verificar_pdf_2023.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.audit_paths import DATA_AUDIT_BY_SOURCE
from src.verification.pdf_2023 import run_verification_2023


def main():
    print("=" * 60)
    print("Verificación: datos 2023 convertidos desde PDF (Boletín en Cifras)")
    print("=" * 60)
    print(f"\nOrigen: {DATA_AUDIT_BY_SOURCE}\n")

    out = run_verification_2023(DATA_AUDIT_BY_SOURCE)

    print("--- 1) Archivos CSV generados desde PDF (2023) ---")
    if not out["archivos_pdf_csv"]:
        print("  No se encontraron archivos *_tables.csv de 2023 en by_source.")
    else:
        for r in out["archivos_pdf_csv"]:
            status = "OK" if r.get("ok") else "REVISAR"
            err = f"  [{status}] {r['archivo']}: {r['filas']} filas, {r['columnas']} cols, "
            err += f"{r['celdas_numericas']} celdas numéricas, {r['filas_con_datos']} filas con datos"
            if r.get("tiene_encabezados_esperados"):
                err += ", encabezados esperados [si]"
            if r.get("error"):
                err += f" | Error: {r['error']}"
            print(err)
        print(f"\n  Resumen: {out['archivos_ok']}/{out['total_archivos']} archivos OK.")

    print("\n--- 2) Referencia Excel 2023 (resumen por empresa) ---")
    ref = out["referencia_excel"]
    if ref.get("error"):
        print(f"  {ref['error']}")
    elif ref.get("ok"):
        print(f"  Archivo: {ref['archivo']}")
        print(f"  Filas: {ref['filas']}")
        print(f"  Total Primas Netas Cobradas (miles Bs.): {ref.get('total_primas_miles'):,.2f}" if ref.get("total_primas_miles") is not None else "  Total: N/A")
        print("  (Usar este total como referencia para comparar con totales del PDF si están en las mismas unidades.)")
    else:
        print("  No se pudo cargar la referencia o no hay columna de primas.")

    print("\n--- Conclusión ---")
    if out["todos_ok"] and out["archivos_pdf_csv"]:
        print("  Los CSV de 2023 extraídos desde PDF son legibles y tienen estructura y contenido esperados.")
        print("  Revisa manualmente totales frente a la referencia Excel si necesitas validar cifras exactas.")
    elif out["archivos_pdf_csv"]:
        print("  Algunos archivos requieren revisión (estructura vacía o sin datos numéricos).")
    else:
        print("  No hay archivos de PDF 2023 en by_source. Ejecuta antes el pipeline de extracción desde data/raw.")
    print()


if __name__ == "__main__":
    main()
