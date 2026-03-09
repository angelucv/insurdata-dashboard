-- =============================================================================
-- ANUARIO - Permisos de escritura para service_role (ETL)
-- Ejecutar en Supabase si el ETL falla con "permission denied".
-- Da a service_role INSERT, UPDATE, DELETE en todas las tablas del schema anuario.
-- =============================================================================

GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA anuario TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA anuario TO service_role;
