# src/app/anuario_config.py
"""Configuración compartida para el dashboard del anuario: sectores, cuadros por sección, etiquetas."""

# Nombre del aplicativo (sidebar, page_title, etc.)
APP_NAME = "InsurData-Dashboard del Seguro en Cifras"

# Logos Actuarial Cortex (URLs desde el sitio oficial)
LOGO_ACTUARIAL_CORTEX_SIDEBAR = "https://actuarial-cortex.pages.dev/logo-AC/logo-AC-AC-vertical-blanco.png"
LOGO_ACTUARIAL_CORTEX_INICIO = "https://actuarial-cortex.pages.dev/logo-AC/logo-actuarial-cortex-principal-blanco.png"


def render_sidebar_logo():
    """Muestra el logo de Actuarial Cortex en la parte superior del menú lateral. Llamar al inicio del sidebar en cada página."""
    import streamlit as st
    try:
        st.sidebar.image(LOGO_ACTUARIAL_CORTEX_SIDEBAR, use_container_width=True)
    except Exception:
        st.sidebar.caption("Actuarial Cortex")
    st.sidebar.markdown("---")

# Código en BD -> etiqueta en UI (denominación consistente en todo el dashboard)
SECTORES = {
    "seguro_directo": "Empresas de Seguro",
    "reaseguro": "Empresas de Reaseguro",
    "financiadoras_primas": "Financiadoras de Primas",
    "medicina_prepagada": "Medicina Prepagada",
}

# Cuadros de balances condensados por sector (tabla balances_condensados)
BALANCES_CUADRO_POR_SECTOR = {
    "seguro_directo": "24",
    "reaseguro": "40",
    "financiadoras_primas": "47",
    "medicina_prepagada": "54",
}

# Cuadros de listados de empresas por sector (tabla listados_empresas). Cuadro 1 = seguro directo.
LISTADOS_CUADRO_POR_SECTOR = {
    "seguro_directo": "1",
    "reaseguro": "39",
    "financiadoras_primas": "46",
    "medicina_prepagada": "53",
}

# Orden de sectores para tabs y filtros
ORDEN_SECTORES = ["seguro_directo", "reaseguro", "financiadoras_primas", "medicina_prepagada"]

# Encabezados de sección en balances (conceptos con monto 0 que no son líneas reales; se ocultan en la vista)
CONCEPTOS_ENCABEZADO_BALANCE = {"ACTIVO", "PASIVO", "CAPITAL", "MÁS", "MAS", "ACTIVOS", "PASIVOS"}


def filtrar_encabezados_balance(df, col_concepto="concepto", col_monto="monto"):
    """Quita filas que son solo encabezados de sección con monto 0 (ACTIVO, PASIVO, etc.)."""
    if df.empty or col_concepto not in df.columns or col_monto not in df.columns:
        return df
    import pandas as pd
    conceptos_upper = df[col_concepto].astype(str).str.strip().str.upper()
    monto_num = pd.to_numeric(df[col_monto], errors="coerce")
    es_encabezado_cero = conceptos_upper.isin(CONCEPTOS_ENCABEZADO_BALANCE) & (monto_num == 0)
    return df.loc[~es_encabezado_cero]


def extraer_totales_balance(df_sector, col_concepto="concepto", col_monto="monto"):
    """
    De un DataFrame de balance (una sector), extrae total activo, total pasivo, utilidad y pérdida.
    Devuelve dict: total_activo, total_pasivo, utilidad_ejercicio, perdida_ejercicio.
    """
    import pandas as pd
    if df_sector.empty or col_concepto not in df_sector.columns or col_monto not in df_sector.columns:
        return {"total_activo": None, "total_pasivo": None, "utilidad_ejercicio": None, "perdida_ejercicio": None}
    df = df_sector.copy()
    df["_concepto_norm"] = df[col_concepto].astype(str).str.strip().str.upper()
    df["_monto_num"] = pd.to_numeric(df[col_monto], errors="coerce")

    total_activo = None
    total_pasivo = None
    utilidad_ejercicio = None
    perdida_ejercicio = None

    for _, row in df.iterrows():
        c = row["_concepto_norm"]
        v = row["_monto_num"]
        if pd.isna(v):
            continue
        if c == "TOTAL ACTIVO":
            total_activo = v
        elif c == "TOTAL PASIVO":
            total_pasivo = v
        elif "UTILIDAD DEL EJERCICIO" in c or c == "UTILIDAD DEL EJERCICIO":
            utilidad_ejercicio = (utilidad_ejercicio or 0) + v
        elif "PÉRDIDA DEL EJERCICIO" in c or "PÉRDIDAS DEL EJERCICIO" in c or "PÉRDIDA DE EJERCICIOS" in c or c == "PÉRDIDA":
            perdida_ejercicio = (perdida_ejercicio or 0) + v

    return {
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "utilidad_ejercicio": utilidad_ejercicio,
        "perdida_ejercicio": perdida_ejercicio,
    }


def formato_numero_es(x, decimals=0):
    """
    Formato español: separador de miles punto (.), separador decimal coma (,).
    Ej: 1234567.89 -> "1.234.567,89" (decimals=2); 1234567 -> "1.234.567" (decimals=0).
    """
    import pandas as pd
    if pd.isna(x) or x is None:
        return ""
    try:
        v = float(x)
        if decimals == 0:
            s = f"{int(round(v)):,}"
        else:
            s = f"{v:,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(x)


# Pie de página del menú lateral (todas las páginas)
SIDEBAR_FOOTER = "Elaborado por el Prof. Angel Colmenares"
AUTHOR_EMAIL = "angelc.ucv@gmail.com"


def render_sidebar_footer():
    """Muestra el crédito del autor y correo al final del menú lateral. Llamar desde cada página."""
    import streamlit as st
    st.sidebar.markdown("---")
    st.sidebar.caption(f"**{SIDEBAR_FOOTER}**")
    st.sidebar.caption(AUTHOR_EMAIL)


# Estilo moderno para gráficos de torta (Plotly)
LAYOUT_PIE_MODERNO = {
    "template": "plotly_white",
    "font": {"family": "Inter, system-ui, -apple-system, sans-serif", "size": 12},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": {"t": 50, "b": 30, "l": 20, "r": 20},
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 11},
    },
    "hoverlabel": {"bgcolor": "white", "font_size": 12},
    "uniformtext": {"minsize": 9, "mode": "hide"},
}
# Paleta moderna para tortas (tonos suaves y diferenciados)
PALETA_PIE_MODERNA = [
    "#4A90D9", "#7B68EE", "#50C878", "#E8A87C",
    "#85CDCA", "#C38D9E", "#F7DC6F", "#BB8FCE",
    "#6BB5FF", "#A8E6CF", "#FFB347", "#DDA0DD",
]

# Subtotales / secciones en Cuadro 3 (primas por ramo) para resaltar en tabla
SUBTOTALES_CUADRO_3 = {"SEGURO DE PERSONAS", "SEGUROS PATRIMONIALES", "SEGUROS SOLIDARIOS", "TOTAL"}


def estilizar_df_numeros(df, columnas_numericas=None, decimals=0):
    """
    Devuelve un Styler del DataFrame: columnas numéricas con formato ES (miles ., decimal ,)
    y alineación a la derecha. Si columnas_numericas es None, detecta columnas numéricas.
    """
    import pandas as pd
    if df.empty:
        return df.style
    if columnas_numericas is None:
        columnas_numericas = df.select_dtypes(include=["number"]).columns.tolist()
    if not columnas_numericas:
        return df.style
    col_set = [c for c in columnas_numericas if c in df.columns]
    if not col_set:
        return df.style

    def fmt_es(v):
        return formato_numero_es(v, decimals=decimals)

    style = df.style.format({c: fmt_es for c in col_set}, na_rep="")
    style = style.set_properties(subset=col_set, **{"text-align": "right"})
    return style


def estilizar_primas_cuadro3_con_subtotales(df, col_concepto="concepto_ramo", columnas_numericas=None, decimals=0):
    """Estilo para tabla Cuadro 3: resalta filas de subtotal/sección (Personas, Patrimoniales, Solidarios, TOTAL)."""
    import pandas as pd
    style = estilizar_df_numeros(df, columnas_numericas=columnas_numericas, decimals=decimals)
    if col_concepto not in df.columns:
        return style

    def resaltar_subtotales(row):
        c = str(row.get(col_concepto, "")).strip().upper()
        if c in SUBTOTALES_CUADRO_3:
            return ["background-color: #e3f2fd; font-weight: bold"] * len(row)
        return [""] * len(row)

    return style.apply(resaltar_subtotales, axis=1)
