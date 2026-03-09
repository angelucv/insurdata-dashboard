"""
Verifica mes a mes si los campos acumulados (primas, siniestros pagados, comisiones, gastos)
no disminuyen al avanzar el año. La información en cada pestaña del Excel es ACUMULADA;
las bajas pueden deberse a empresas que no envían en un mes o a ajustes a la baja.
Solo las reservas (3),(4) y siniestros totales (5)=(2)+(3) se constituyen y liberan mes a mes,
por tanto NO se verifican como crecientes.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import DATA_STAGED

STAGED_2023 = DATA_STAGED / "2023"
BASE_CSV = STAGED_2023 / "resumen_por_empresa_2023_base.csv"
REPORTE_BAJAS = STAGED_2023 / "verificacion_acumulacion_bajas.csv"
REPORTE_RESUMEN = STAGED_2023 / "verificacion_acumulacion_resumen.txt"

# Campos acumulados (YTD): primas, siniestros pagados, comisiones, gastos. No incluir reservas (3)(4) ni (5).
CAMPOS_ACUMULABLES = [
    "primas_netas_ves",
    "siniestros_pagados_ves",
    "comisiones_ves",
    "gastos_adquisicion_ves",
    "gastos_administracion_ves",
    "gastos_operativos_ves",
]

# Tolerancia por redondeo (Bs.): diferencia menor se considera igual
TOLERANCIA = 1.0


def main():
    print("=" * 70)
    print("Verificacion: campos acumulables mes a mes (no deben bajar)")
    print("=" * 70)

    if not BASE_CSV.exists():
        print("No existe", BASE_CSV, "- ejecuta antes verificar_compilado_8_campos.py")
        return

    df = pd.read_csv(BASE_CSV, encoding="utf-8-sig")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
    df = df.sort_values(["entity_normalized", "mes"])

    campos = [c for c in CAMPOS_ACUMULABLES if c in df.columns]
    print("\nCampos a verificar como no decrecientes: {}".format(campos))

    # Por cada entidad y cada campo: detectar bajas (valor(mes N) < valor(mes N-1) - tolerancia)
    filas_baja = []
    resumen_entidad = {}  # entity -> { campo -> (n_bajas, lista de (mes_ant, mes, v_ant, v_act)) }

    for ent in df["entity_normalized"].dropna().unique():
        sub = df[df["entity_normalized"] == ent].sort_values("mes")
        if sub.empty:
            continue
        resumen_entidad[ent] = {}
        for col in campos:
            if col not in sub.columns:
                continue
            bajas = []
            prev_mes = None
            prev_val = None
            for _, row in sub.iterrows():
                mes = int(row["mes"])
                val = row.get(col)
                if pd.isna(val):
                    prev_mes, prev_val = mes, None
                    continue
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    prev_mes, prev_val = mes, None
                    continue
                if prev_val is not None and prev_mes is not None and mes > prev_mes:
                    if v < prev_val - TOLERANCIA:
                        bajas.append((prev_mes, mes, prev_val, v))
                        tipo = "baja_a_cero" if v < TOLERANCIA else "baja_ambos_positivos"
                        filas_baja.append({
                            "entity_normalized": ent,
                            "entity_canonical": row.get("entity_canonical", ent),
                            "campo": col,
                            "mes_anterior": prev_mes,
                            "mes_actual": mes,
                            "valor_anterior": prev_val,
                            "valor_actual": v,
                            "diferencia": v - prev_val,
                            "tipo_baja": tipo,
                        })
                prev_mes, prev_val = mes, v
            resumen_entidad[ent][col] = bajas

    # Resumen por campo: cuántas entidades tienen al menos una baja
    print("\n1) Resumen por campo (entidades con al menos una baja mes a mes)")
    print("   " + "-" * 60)
    entidades_con_baja_por_campo = {}
    for col in campos:
        entes = set()
        for ent, cols in resumen_entidad.items():
            if col in cols and cols[col]:
                entes.add(ent)
        entidades_con_baja_por_campo[col] = entes
        print("   {:30s} {:3d} entidades con al menos 1 baja".format(col, len(entes)))

    # Resumen global
    todas_entes_con_baja = set()
    for entes in entidades_con_baja_por_campo.values():
        todas_entes_con_baja |= entes
    n_entes_total = df["entity_normalized"].nunique()
    print("\n2) Total entidades con al menos una baja en algun campo: {} / {}".format(
        len(todas_entes_con_baja), n_entes_total))
    print("   Total registros (mes, entidad, campo) con baja: {}".format(len(filas_baja)))

    # Desglose: bajas a cero (falta de dato / empresa deja de reportar) vs bajas con ambos > 0
    if filas_baja:
        df_b = pd.DataFrame(filas_baja)
        n_cero = (df_b["tipo_baja"] == "baja_a_cero").sum()
        n_ambos = (df_b["tipo_baja"] == "baja_ambos_positivos").sum()
        print("\n3) Tipo de bajas:")
        print("   Baja a (casi) cero: {} (sugiere dato faltante o empresa dejo de reportar)".format(int(n_cero)))
        print("   Baja con ambos positivos: {} (sugiere datos MENSUALES o correccion en origen)".format(int(n_ambos)))
    if len(filas_baja) == 0:
        print("\n4) Resultado: Los valores mes a mes NUNCA bajan -> coherente con datos ACUMULADOS (YTD).")
    else:
        print("\n4) Resultado: Hay bajas mes a mes.")
        print("   Si predominan 'baja a cero', revisar carga de diciembre o empresas que dejan de reportar.")
        print("   Si predominan 'ambos positivos', el origen podria ser MENSUAL (no YTD).")

    # Guardar detalle de bajas
    if filas_baja:
        pd.DataFrame(filas_baja).to_csv(REPORTE_BAJAS, index=False, encoding="utf-8-sig")
        print("\n5) Detalle de bajas guardado: {}".format(REPORTE_BAJAS))
        print("   Muestra (primeras 15):")
        muestra = pd.DataFrame(filas_baja).head(15)
        for _, r in muestra.iterrows():
            print("   {} | {} | mes {}-{} | ant: {:.0f} -> act: {:.0f} (diff: {:.0f})".format(
                str(r["entity_canonical"])[:35],
                r["campo"],
                int(r["mes_anterior"]), int(r["mes_actual"]),
                r["valor_anterior"], r["valor_actual"], r["diferencia"]))
    else:
        print("\n5) No hay bajas; no se genera archivo de detalle.")

    # Resumen por mes: en cuántos (entidad, campo) hubo baja al pasar a ese mes
    if filas_baja:
        df_b = pd.DataFrame(filas_baja)
        bajas_por_mes = df_b.groupby("mes_actual").size()
        print("\n6) Bajas detectadas al pasar al mes (cuantas transiciones mes_anterior -> mes_actual):")
        for mes in sorted(bajas_por_mes.index):
            print("   Mes {:2d}: {} bajas".format(int(mes), int(bajas_por_mes[mes])))

    with open(REPORTE_RESUMEN, "w", encoding="utf-8") as f:
        f.write("Verificacion acumulacion 2023\n")
        f.write("Campos: {}\n".format(", ".join(campos)))
        f.write("Entidades con al menos 1 baja por campo:\n")
        for col in campos:
            f.write("  {}: {}\n".format(col, len(entidades_con_baja_por_campo.get(col, set()))))
        f.write("Total entidades con alguna baja: {} / {}\n".format(len(todas_entes_con_baja), n_entes_total))
        f.write("Total registros con baja: {}\n".format(len(filas_baja)))
        if filas_baja:
            df_b = pd.DataFrame(filas_baja)
            n_cero = (df_b["tipo_baja"] == "baja_a_cero").sum()
            n_ambos = (df_b["tipo_baja"] == "baja_ambos_positivos").sum()
            f.write("Bajas a cero: {} | Bajas ambos positivos: {}\n".format(int(n_cero), int(n_ambos)))
    print("\n7) Resumen escrito: {}".format(REPORTE_RESUMEN))
    print("=" * 70)


if __name__ == "__main__":
    main()
