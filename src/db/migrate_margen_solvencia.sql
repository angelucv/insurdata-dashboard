-- Crear solo la tabla margen_solvencia (ejecutar en Supabase SQL Editor)
-- Requiere que la tabla entities exista (entity_id REFERENCES entities(id))

CREATE TABLE IF NOT EXISTS margen_solvencia (
    id SERIAL PRIMARY KEY,
    entity_id UUID REFERENCES entities(id),
    trimestre INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    margen NUMERIC(18, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (entity_id, anio, trimestre)
);

CREATE INDEX IF NOT EXISTS idx_margen_entity ON margen_solvencia(entity_id, anio);

ALTER TABLE margen_solvencia ENABLE ROW LEVEL SECURITY;

-- Eliminar políticas si ya existían (evita error "already exists")
DROP POLICY IF EXISTS "Allow anon read" ON margen_solvencia;
DROP POLICY IF EXISTS "Allow read for authenticated" ON margen_solvencia;

CREATE POLICY "Allow anon read" ON margen_solvencia FOR SELECT TO anon USING (true);
CREATE POLICY "Allow read for authenticated" ON margen_solvencia
    FOR SELECT TO authenticated USING (true);
