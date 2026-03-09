# scripts/verificar_anuario_local_y_nube.py
"""
Verifica que la informacion del anuario este completa: local (CSVs) y nube (Supabase).
Ejecuta verificar_csv_verificadas y verificar_carga_anuario_supabase y muestra un resumen.

Uso: python scripts/verificar_anuario_local_y_nube.py [--year 2023]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_env = ROOT / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)


def main():
    p = argparse.ArgumentParser(description="Verificar anuario: local (CSV) + nube (Supabase)")
    p.add_argument("--year", type=int, default=2023)
    args = p.parse_args()
    year = args.year

    print("=" * 60)
    print("VERIFICACION ANUARIO SEGURO EN CIFRAS (local + nube)")
    print("Anio:", year)
    print("=" * 60)

    # 1) Local: CSVs
    print("\n[1] LOCAL - CSVs en data/staged/{}/verificadas/".format(year))
    r1 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verificar_csv_verificadas.py"), "--year", str(year)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r1.returncode == 0:
        print("  OK - Archivos CSV presentes y legibles.")
    else:
        print("  FALLO - Revisar CSVs.")
        if r1.stdout:
            print(r1.stdout[-1000:])
        if r1.stderr:
            print(r1.stderr[-500:])

    # 2) Nube: Supabase
    print("\n[2] NUBE - Supabase (schema anuario)")
    r2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verificar_carga_anuario_supabase.py"), "--year", str(year)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r2.returncode == 0:
        print("  OK - Carga completa y coherente (CSV vs Supabase).")
    else:
        print("  FALLO - Hay diferencias o errores en Supabase.")
    if r2.stdout:
        print(r2.stdout)

    print("=" * 60)
    if r1.returncode == 0 and r2.returncode == 0:
        print("RESUMEN: Local y nube verificados correctamente.")
        sys.exit(0)
    print("RESUMEN: Revisar fallos arriba.")
    sys.exit(1)


if __name__ == "__main__":
    main()
