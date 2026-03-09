-- Permitir INSERT y UPDATE con la clave anon/publishable (para scripts de carga SUDEASEG)
-- Ejecutar en Supabase SQL Editor una vez

DROP POLICY IF EXISTS "Allow anon insert entities" ON entities;
DROP POLICY IF EXISTS "Allow anon insert primas" ON primas_mensuales;
DROP POLICY IF EXISTS "Allow anon update primas" ON primas_mensuales;

CREATE POLICY "Allow anon insert entities" ON entities FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow anon insert primas" ON primas_mensuales FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow anon update primas" ON primas_mensuales FOR UPDATE TO anon USING (true) WITH CHECK (true);
