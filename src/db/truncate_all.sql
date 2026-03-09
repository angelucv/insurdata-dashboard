-- Vaciar todas las tablas de datos para cargar desde cero.
-- Ejecutar en Supabase SQL Editor.
-- Orden: primero tablas con FK hacia entities, luego entities.

TRUNCATE TABLE primas_mensuales CASCADE;
TRUNCATE TABLE margen_solvencia CASCADE;
TRUNCATE TABLE series_historicas CASCADE;
TRUNCATE TABLE exchange_rates CASCADE;
TRUNCATE TABLE entities CASCADE;

-- Reiniciar secuencias si las hay
ALTER SEQUENCE IF EXISTS primas_mensuales_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS margen_solvencia_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS series_historicas_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS exchange_rates_id_seq RESTART WITH 1;
