-- =============================================================================
-- ANUARIO "SEGURO EN CIFRAS" - 23 TABLAS TEMÁTICAS (PostgreSQL / Supabase)
-- Ejecutar después de 001_anuario_dimensiones.sql.
-- PK: id. FK: cuadro_id -> anuario.cuadros. Índices: anio, cuadro_id, nombre_empresa.
-- ALCANCE: Solo anuarios (PDF). Otras fuentes (Excel, etc.) → ver docs/FUENTES_DE_DATOS.md.
-- =============================================================================

-- 1. Primas por ramo (cuadros 3, 5-A, 5-B, 5-C)
CREATE TABLE anuario.primas_por_ramo (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    origen_archivo   TEXT,
    concepto_ramo    TEXT,
    seguro_directo  TEXT,
    reaseguro_aceptado TEXT,
    total           TEXT,
    pct             TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_primas_por_ramo_anio ON anuario.primas_por_ramo(anio);
CREATE INDEX idx_primas_por_ramo_cuadro ON anuario.primas_por_ramo(cuadro_id);

-- 2. Primas por ramo y empresa (cuadro 4)
CREATE TABLE anuario.primas_por_ramo_empresa (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_primas_por_ramo_empresa_anio ON anuario.primas_por_ramo_empresa(anio);
CREATE INDEX idx_primas_por_ramo_empresa_empresa ON anuario.primas_por_ramo_empresa(nombre_empresa);

-- 3. Siniestros por ramo (cuadros 6, 7, 8-A, 8-B, 8-C)
CREATE TABLE anuario.siniestros_por_ramo (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    origen_archivo   TEXT,
    concepto_ramo    TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_siniestros_por_ramo_anio ON anuario.siniestros_por_ramo(anio);

-- 4. Reservas técnicas agregado (cuadro 9)
CREATE TABLE anuario.reservas_tecnicas_agregado (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto        TEXT,
    monto           TEXT,
    tipo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reservas_tecnicas_agregado_anio ON anuario.reservas_tecnicas_agregado(anio);

-- 5. Reservas prima por ramo (cuadro 10)
CREATE TABLE anuario.reservas_prima_por_ramo (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto_ramo   TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reservas_prima_por_ramo_anio ON anuario.reservas_prima_por_ramo(anio);

-- 6. Reservas prima por empresa (cuadros 11, 12, 13, 14)
CREATE TABLE anuario.reservas_prima_por_empresa (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reservas_prima_por_empresa_anio ON anuario.reservas_prima_por_empresa(anio);
CREATE INDEX idx_reservas_prima_por_empresa_empresa ON anuario.reservas_prima_por_empresa(nombre_empresa);

-- 7. Reservas prestaciones por ramo (cuadro 15)
CREATE TABLE anuario.reservas_prestaciones_por_ramo (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto_ramo   TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reservas_prestaciones_por_ramo_anio ON anuario.reservas_prestaciones_por_ramo(anio);

-- 8. Reservas prestaciones por empresa (cuadros 16, 17, 18, 19)
CREATE TABLE anuario.reservas_prestaciones_por_empresa (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reservas_prestaciones_por_empresa_anio ON anuario.reservas_prestaciones_por_empresa(anio);
CREATE INDEX idx_reservas_prestaciones_por_empresa_empresa ON anuario.reservas_prestaciones_por_empresa(nombre_empresa);

-- 9. Reservas detalle por ramo/empresa (cuadros 20-A a 20-F)
CREATE TABLE anuario.reservas_detalle_por_ramo_empresa (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    origen_archivo   TEXT,
    fila_orden      INTEGER,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reservas_detalle_anio ON anuario.reservas_detalle_por_ramo_empresa(anio);

-- 10. Inversiones reservas técnicas (cuadro 21)
CREATE TABLE anuario.inversiones_reservas_tecnicas (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto        TEXT,
    monto           TEXT,
    tipo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_inversiones_reservas_anio ON anuario.inversiones_reservas_tecnicas(anio);

-- 11. Gastos vs primas (cuadros 22, 23, 23-A a 23-F)
CREATE TABLE anuario.gastos_vs_primas (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    origen_archivo   TEXT,
    concepto_ramo_o_empresa TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_gastos_vs_primas_anio ON anuario.gastos_vs_primas(anio);

-- 12. Balances condensados (cuadros 24, 40, 47, 54)
CREATE TABLE anuario.balances_condensados (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto        TEXT,
    monto           TEXT,
    tipo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_balances_condensados_anio ON anuario.balances_condensados(anio);
CREATE INDEX idx_balances_condensados_cuadro ON anuario.balances_condensados(cuadro_id);

-- 13. Estados ingresos y egresos (cuadros 25-A, 25-B, 41-A, 41-B, 48, 55-A, 55-B)
CREATE TABLE anuario.estados_ingresos_egresos (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto        TEXT,
    monto           TEXT,
    tipo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_estados_ingresos_egresos_anio ON anuario.estados_ingresos_egresos(anio);

-- 14. Gestión general (cuadro 26)
CREATE TABLE anuario.gestion_general (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto        TEXT,
    monto           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_gestion_general_anio ON anuario.gestion_general(anio);

-- 15. Datos por empresa (cuadros 27, 28, 34, 35, 36, 49, 50, 51, 56, 57)
CREATE TABLE anuario.datos_por_empresa (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_datos_por_empresa_anio ON anuario.datos_por_empresa(anio);
CREATE INDEX idx_datos_por_empresa_empresa ON anuario.datos_por_empresa(nombre_empresa);

-- 16. Indicadores financieros por empresa (cuadros 29, 44, 52, 58)
CREATE TABLE anuario.indicadores_financieros_empresa (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_indicadores_financieros_anio ON anuario.indicadores_financieros_empresa(anio);
CREATE INDEX idx_indicadores_financieros_empresa ON anuario.indicadores_financieros_empresa(nombre_empresa);

-- 17. Suficiencia patrimonio (cuadros 30, 45)
CREATE TABLE anuario.suficiencia_patrimonio (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_suficiencia_patrimonio_anio ON anuario.suficiencia_patrimonio(anio);

-- 18. Series históricas primas (cuadros 31-A, 31-B)
CREATE TABLE anuario.series_historicas_primas (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    tipo_serie      TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_series_historicas_anio ON anuario.series_historicas_primas(anio);

-- 19. Reservas hospitalización (cuadros 32, 33)
CREATE TABLE anuario.reservas_hospitalizacion (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reservas_hospitalizacion_anio ON anuario.reservas_hospitalizacion(anio);

-- 20. Cantidad pólizas y siniestros (cuadros 37, 38)
CREATE TABLE anuario.cantidad_polizas_siniestros (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto_ramo_o_empresa TEXT,
    polizas         TEXT,
    siniestros      TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_cantidad_polizas_anio ON anuario.cantidad_polizas_siniestros(anio);

-- 20b. Capital y garantía por empresa (cuadro 2): Inscripción (número, año), Empresa, Capital Social Suscrito, Garantía (Seguros, Fideicomiso, Total)
CREATE TABLE anuario.capital_garantia_por_empresa (
    id                          SERIAL PRIMARY KEY,
    anio                        INTEGER NOT NULL,
    cuadro_id                   TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    inscripcion_numero          TEXT,
    inscripcion_anio           TEXT,
    nombre_empresa             TEXT,
    capital_social_suscrito     TEXT,
    garantia_operaciones_seguros TEXT,
    garantia_operaciones_fideicomiso TEXT,
    garantia_total             TEXT,
    datos                       JSONB,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_capital_garantia_anio ON anuario.capital_garantia_por_empresa(anio);
CREATE INDEX idx_capital_garantia_empresa ON anuario.capital_garantia_por_empresa(nombre_empresa);

-- 21. Listados empresas (cuadros 1, 39, 46, 53)
CREATE TABLE anuario.listados_empresas (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    numero_orden    INTEGER,
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_listados_empresas_anio ON anuario.listados_empresas(anio);
CREATE INDEX idx_listados_empresas_cuadro ON anuario.listados_empresas(cuadro_id);

-- 22. Balance por empresa reaseguros (cuadro 42, normalizado a filas)
CREATE TABLE anuario.balance_por_empresa_reaseguros (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    concepto        TEXT,
    nombre_empresa  TEXT,
    monto           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_balance_por_empresa_reaseguros_anio ON anuario.balance_por_empresa_reaseguros(anio);
CREATE INDEX idx_balance_por_empresa_reaseguros_empresa ON anuario.balance_por_empresa_reaseguros(nombre_empresa);

-- 23. Ingresos y egresos por empresa reaseguros (cuadros 43-A, 43-B)
CREATE TABLE anuario.ingresos_egresos_por_empresa_reaseguros (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ingresos_egresos_reaseguros_anio ON anuario.ingresos_egresos_por_empresa_reaseguros(anio);
CREATE INDEX idx_ingresos_egresos_reaseguros_empresa ON anuario.ingresos_egresos_por_empresa_reaseguros(nombre_empresa);
