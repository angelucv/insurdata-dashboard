-- =============================================================================
-- Migración: Cuadros 1 y 2 + tabla capital_garantia_por_empresa (para instalaciones existentes)
-- Ejecutar en Supabase si ya tenías el schema anuario sin cuadros 1/2 ni tabla capital_garantia.
-- =============================================================================

-- Añadir cuadros 1 y 2 al catálogo (ignorar si ya existen)
INSERT INTO anuario.cuadros (cuadro_id, nombre, sector) VALUES
('1', 'Empresas de seguro autorizadas', 'seguro_directo'),
('2', 'Capital y garantía por empresa', 'seguro_directo')
ON CONFLICT (cuadro_id) DO NOTHING;

-- Tabla Capital y garantía por empresa (Cuadro 2) — crear solo si no existe
CREATE TABLE IF NOT EXISTS anuario.capital_garantia_por_empresa (
    id                          SERIAL PRIMARY KEY,
    anio                        INTEGER NOT NULL,
    cuadro_id                   TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    inscripcion_numero          TEXT,
    inscripcion_anio            TEXT,
    nombre_empresa              TEXT,
    capital_social_suscrito    TEXT,
    garantia_operaciones_seguros TEXT,
    garantia_operaciones_fideicomiso TEXT,
    garantia_total              TEXT,
    datos                       JSONB,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_capital_garantia_anio ON anuario.capital_garantia_por_empresa(anio);
CREATE INDEX IF NOT EXISTS idx_capital_garantia_empresa ON anuario.capital_garantia_por_empresa(nombre_empresa);

-- RLS y políticas (si la tabla ya tenía RLS, puede dar error "policy already exists" — ignorar)
ALTER TABLE anuario.capital_garantia_por_empresa ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "anuario_capital_garantia_por_empresa_read_anon" ON anuario.capital_garantia_por_empresa;
DROP POLICY IF EXISTS "anuario_capital_garantia_por_empresa_read_auth" ON anuario.capital_garantia_por_empresa;
CREATE POLICY "anuario_capital_garantia_por_empresa_read_anon" ON anuario.capital_garantia_por_empresa FOR SELECT TO anon USING (true);
CREATE POLICY "anuario_capital_garantia_por_empresa_read_auth" ON anuario.capital_garantia_por_empresa FOR SELECT TO authenticated USING (true);

-- Permisos para la API y ETL
GRANT SELECT ON anuario.capital_garantia_por_empresa TO anon, authenticated, service_role;
GRANT INSERT, UPDATE, DELETE ON anuario.capital_garantia_por_empresa TO service_role;
GRANT USAGE, SELECT ON SEQUENCE anuario.capital_garantia_por_empresa_id_seq TO service_role;
