-- Migración: tabla siniestros_por_ramo_empresa (Cuadro 7)
-- Ejecutar en Supabase SQL Editor si la tabla no existe.

CREATE TABLE IF NOT EXISTS anuario.siniestros_por_ramo_empresa (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    cuadro_id       TEXT NOT NULL REFERENCES anuario.cuadros(cuadro_id),
    nombre_empresa  TEXT,
    datos           JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_siniestros_por_ramo_empresa_anio ON anuario.siniestros_por_ramo_empresa(anio);
CREATE INDEX IF NOT EXISTS idx_siniestros_por_ramo_empresa_empresa ON anuario.siniestros_por_ramo_empresa(nombre_empresa);

ALTER TABLE anuario.siniestros_por_ramo_empresa ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "anuario_siniestros_por_ramo_empresa_read_anon" ON anuario.siniestros_por_ramo_empresa;
DROP POLICY IF EXISTS "anuario_siniestros_por_ramo_empresa_read_auth" ON anuario.siniestros_por_ramo_empresa;
CREATE POLICY "anuario_siniestros_por_ramo_empresa_read_anon" ON anuario.siniestros_por_ramo_empresa FOR SELECT TO anon USING (true);
CREATE POLICY "anuario_siniestros_por_ramo_empresa_read_auth" ON anuario.siniestros_por_ramo_empresa FOR SELECT TO authenticated USING (true);
GRANT SELECT ON anuario.siniestros_por_ramo_empresa TO anon, authenticated, service_role;
GRANT INSERT, UPDATE, DELETE ON anuario.siniestros_por_ramo_empresa TO service_role;
GRANT USAGE, SELECT ON SEQUENCE anuario.siniestros_por_ramo_empresa_id_seq TO service_role;
