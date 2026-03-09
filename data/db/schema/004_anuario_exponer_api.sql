-- =============================================================================
-- ANUARIO - Exponer schema a la API de Supabase
-- Ejecutar en Supabase después de 001, 002 y 003. Necesario para que el
-- cliente (Streamlit, scripts) pueda leer tablas anuario.* desde la API.
-- Luego: en Dashboard → Settings → API → "Exposed schemas" añadir "anuario".
-- =============================================================================

GRANT USAGE ON SCHEMA anuario TO anon, authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA anuario TO anon, authenticated, service_role;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA anuario TO anon, authenticated, service_role;

-- service_role: permisos de escritura para ETL (INSERT/DELETE). anon/authenticated solo lectura.
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA anuario TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA anuario TO service_role;

-- Para que futuras tablas del schema también tengan SELECT por defecto
ALTER DEFAULT PRIVILEGES IN SCHEMA anuario
    GRANT SELECT ON TABLES TO anon, authenticated, service_role;
