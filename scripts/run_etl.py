# scripts/run_etl.py
"""Ejecuta el pipeline ETL sobre archivos en data/raw/ y opcionalmente carga en Supabase."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DATA_RAW, DATA_PROCESSED
from src.etl.pipeline import ETLPipeline
from src.db import get_supabase_client, load_df_into_table

def main():
    pipeline = ETLPipeline()
    raw = DATA_RAW

    # Procesar Excels de Cifras Mensuales
    for ext in ("xlsx", "xls"):
        for path in raw.rglob(f"*.{ext}"):
            print(f"Procesando {path}...")
            try:
                df = pipeline.process_excel(
                    path,
                    sheet_name=0,
                    entity_column=None,  # Ajustar al nombre de columna de empresa en tus archivos
                )
                if not df.empty:
                    out_name = path.stem + "_processed"
                    pipeline.save_for_db(df, out_name)
                    print(f"  -> {len(df)} filas guardadas en {out_name}.parquet")
            except Exception as e:
                print(f"  Error: {e}")

    # Procesar PDFs (boletines)
    for path in raw.rglob("*.pdf"):
        print(f"Extrayendo tablas de {path}...")
        try:
            tables = pipeline.process_pdf_tables(path)
            for i, t in enumerate(tables):
                if not t.empty:
                    pipeline.save_for_db(t, f"{path.stem}_tabla{i}")
                    print(f"  -> Tabla {i}: {len(t)} filas")
        except Exception as e:
            print(f"  Error: {e}")

    # Opcional: cargar a Supabase
    sb = get_supabase_client()
    if sb:
        for parquet in DATA_PROCESSED.glob("*.parquet"):
            import pandas as pd
            df = pd.read_parquet(parquet)
            if "entity_id" in df.columns and "periodo" in df.columns:
                table = "primas_mensuales"
            else:
                table = "series_historicas"
            n = load_df_into_table(df, table, sb)
            print(f"Cargadas {n} filas en {table} desde {parquet.name}")

if __name__ == "__main__":
    main()
