"""
Vaciado secuencial de anuarios Seguro en Cifras por año ascendente (mas antiguo al mas reciente).
Verifica en el año mas antiguo que informacion esta disponible y escribe el vaciado consolidado.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import DATA_AUDIT_BY_SOURCE
from config.anuarios_paths import (
    INDICE_FUENTES_CSV,
    VACIADO_ENTIDADES_CSV,
    METRICAS_CSV,
    SEGURO_EN_CIFRAS_INDICE,
)
from src.etl.anuarios_seguro_en_cifras import (
    build_indice_fuentes,
    run_vaciado_secuencial,
    get_by_source_tables_path,
    _nombre_archivo_to_tables_csv,
)


def informe_anio_mas_antiguo():
    """Verifica que informacion hay disponible para el año mas antiguo (1967)."""
    fuentes = pd.read_csv(INDICE_FUENTES_CSV)
    anio_min = int(fuentes["anio"].min())
    row = fuentes[fuentes["anio"] == anio_min].iloc[0]
    nombre_archivo = row["nombre_archivo"]
    tipo = row["tipo"]
    tables_name = _nombre_archivo_to_tables_csv(nombre_archivo)
    by_source_path = Path(DATA_AUDIT_BY_SOURCE)
    tables_path = by_source_path / tables_name
    pdf_text_path = by_source_path / "pdf_text" / (Path(nombre_archivo).stem + ".txt" if tipo == "pdf" else "")

    lineas = []
    lineas.append("=" * 60)
    lineas.append("INFORME ANO MAS ANTIGUO: %d" % anio_min)
    lineas.append("=" * 60)
    lineas.append("Fuente: %s (tipo: %s)" % (nombre_archivo, tipo))
    lineas.append("")
    lineas.append("Disponibilidad en by_source:")
    lineas.append("  - Tablas extraidas (_tables.csv): %s" % tables_path.name)
    if tables_path.exists():
        try:
            df = pd.read_csv(tables_path, header=None, nrows=50, low_memory=False)
            lineas.append("    EXISTE. Filas (muestra): %d, Columnas: %d" % (len(df), len(df.columns) if not df.empty else 0))
            non_empty = (df.astype(str).apply(lambda s: s.str.strip() != "")).sum().sum()
            non_empty = int(non_empty)
            lineas.append("    Celdas no vacias (primeras 50 filas): %d" % non_empty)
            if non_empty == 0:
                lineas.append("    -> PDF probablemente escaneado/OCR: tabla vacia o sin estructura.")
        except Exception as e:
            lineas.append("    Error al leer: %s" % e)
    else:
        lineas.append("    NO EXISTE (ejecutar pipeline de extraccion PDF primero).")
    if tipo == "pdf":
        if pdf_text_path.exists():
            with open(pdf_text_path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
            lineas.append("  - Texto PDF (pdf_text): EXISTE. Longitud: %d caracteres" % len(text))
            if len(text.strip()) < 200:
                lineas.append("    -> Poco texto extraido (OCR limitado o PDF vacio).")
        else:
            lineas.append("  - Texto PDF (pdf_text): NO EXISTE.")
    lineas.append("")
    lineas.append("Conclusion: Para anios solo con PDF, el vaciado usa by_source/*_tables.csv.")
    lineas.append("Si el CSV esta vacio o no existe, ese anio no tendra entidades/metricas vaciadas.")
    lineas.append("")
    return "\n".join(lineas)


def main():
    build_indice_fuentes()
    print("Vaciado secuencial - Seguro en Cifras (orden ascendente por anio)")
    print("")

    # Informe año mas antiguo
    print(informe_anio_mas_antiguo())

    print("Ejecutando vaciado por cada anio...")
    ent, met, resumen = run_vaciado_secuencial()

    print("")
    print("Resumen por anio (ascendente):")
    print("-" * 70)
    for r in resumen:
        obs = ("  <- " + str(r.get("observacion", ""))[:50]) if r.get("observacion") else ""
        print("  %d  %s  entidades=%d  metricas=%d  origen=%s%s" % (
            r["anio"],
            r["tipo"].ljust(4),
            r["entidades"],
            r["metricas"],
            r.get("origen", ""),
            obs,
        ))

    total_ent = len(ent)
    total_met = len(met)
    anios_con_datos = sum(1 for r in resumen if r["entidades"] > 0 or r["metricas"] > 0)
    print("-" * 70)
    print("Total entidades (deduplicadas): %d" % total_ent)
    print("Total metricas: %d" % total_met)
    print("Anios con al menos algun dato vaciado: %d / %d" % (anios_con_datos, len(resumen)))
    print("")
    print("Archivos escritos:")
    print("  %s" % VACIADO_ENTIDADES_CSV)
    print("  %s" % METRICAS_CSV)

    # Guardar resumen en CSV
    resumen_path = SEGURO_EN_CIFRAS_INDICE / "vaciado_secuencial_resumen.csv"
    pd.DataFrame(resumen).to_csv(resumen_path, index=False, encoding="utf-8-sig")
    print("  %s" % resumen_path)


if __name__ == "__main__":
    main()
