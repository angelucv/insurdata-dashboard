-- Esquema PostgreSQL para SUDEASEG Dashboard
-- Ejecutar en Supabase SQL Editor o via migraciones

-- Catálogo de entidades (aseguradoras, reaseguradoras, etc.)
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized_name TEXT UNIQUE NOT NULL,
    canonical_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasas de cambio BCV (cache para normalización VES -> USD)
CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    rate_date DATE NOT NULL UNIQUE,
    ves_per_usd NUMERIC(18, 6) NOT NULL,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Primas netas y métricas mensuales por entidad
CREATE TABLE IF NOT EXISTS primas_mensuales (
    id SERIAL PRIMARY KEY,
    entity_id UUID REFERENCES entities(id),
    periodo DATE NOT NULL,
    primas_netas_ves NUMERIC(18, 2),
    primas_netas_usd NUMERIC(18, 2),
    siniestros_pagados_ves NUMERIC(18, 2),
    siniestros_pagados_usd NUMERIC(18, 2),
    gastos_operativos_ves NUMERIC(18, 2),
    gastos_operativos_usd NUMERIC(18, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (entity_id, periodo)
);

-- Margen de solvencia (trimestral)
CREATE TABLE IF NOT EXISTS margen_solvencia (
    id SERIAL PRIMARY KEY,
    entity_id UUID REFERENCES entities(id),
    trimestre INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    margen NUMERIC(18, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (entity_id, anio, trimestre)
);

-- Series históricas agregadas (para KPIs del dashboard)
CREATE TABLE IF NOT EXISTS series_historicas (
    id SERIAL PRIMARY KEY,
    periodo DATE NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC(18, 4) NOT NULL,
    unit TEXT DEFAULT 'USD',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para consultas del dashboard
CREATE INDEX IF NOT EXISTS idx_primas_entity_period ON primas_mensuales(entity_id, periodo);
CREATE INDEX IF NOT EXISTS idx_primas_periodo ON primas_mensuales(periodo);
CREATE INDEX IF NOT EXISTS idx_margen_entity ON margen_solvencia(entity_id, anio);
CREATE INDEX IF NOT EXISTS idx_series_periodo ON series_historicas(periodo, metric_name);

-- RLS (Row-Level Security) para Supabase Auth
ALTER TABLE entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE primas_mensuales ENABLE ROW LEVEL SECURITY;
ALTER TABLE margen_solvencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE series_historicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE exchange_rates ENABLE ROW LEVEL SECURITY;

-- Lectura para anon (dashboard sin login cuando REQUIRE_AUTH=false)
CREATE POLICY "Allow anon read" ON entities FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON primas_mensuales FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON margen_solvencia FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON series_historicas FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON exchange_rates FOR SELECT TO anon USING (true);

-- Lectura para usuarios autenticados (cuando REQUIRE_AUTH=true)
CREATE POLICY "Allow read for authenticated" ON entities
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read for authenticated" ON primas_mensuales
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read for authenticated" ON margen_solvencia
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read for authenticated" ON series_historicas
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read for authenticated" ON exchange_rates
    FOR SELECT TO authenticated USING (true);
