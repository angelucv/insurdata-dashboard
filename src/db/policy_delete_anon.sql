-- Permitir DELETE para poder vaciar tablas con scripts (truncate_supabase.py)
-- Ejecutar en Supabase SQL Editor si quieres que el script borre sin usar TRUNCATE.

DROP POLICY IF EXISTS "Allow anon delete primas" ON primas_mensuales;
DROP POLICY IF EXISTS "Allow anon delete margen" ON margen_solvencia;
DROP POLICY IF EXISTS "Allow anon delete series" ON series_historicas;
DROP POLICY IF EXISTS "Allow anon delete rates" ON exchange_rates;
DROP POLICY IF EXISTS "Allow anon delete entities" ON entities;

CREATE POLICY "Allow anon delete primas" ON primas_mensuales FOR DELETE TO anon USING (true);
CREATE POLICY "Allow anon delete margen" ON margen_solvencia FOR DELETE TO anon USING (true);
CREATE POLICY "Allow anon delete series" ON series_historicas FOR DELETE TO anon USING (true);
CREATE POLICY "Allow anon delete rates" ON exchange_rates FOR DELETE TO anon USING (true);
CREATE POLICY "Allow anon delete entities" ON entities FOR DELETE TO anon USING (true);
