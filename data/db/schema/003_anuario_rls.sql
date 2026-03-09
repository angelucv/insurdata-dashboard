-- =============================================================================
-- ANUARIO - RLS (Row-Level Security) para Supabase
-- Ejecutar en Supabase después de 001 y 002. Opcional para réplica local.
-- =============================================================================

ALTER TABLE anuario.cuadros ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.primas_por_ramo ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.primas_por_ramo_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.siniestros_por_ramo ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.reservas_tecnicas_agregado ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.reservas_prima_por_ramo ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.reservas_prima_por_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.reservas_prestaciones_por_ramo ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.reservas_prestaciones_por_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.reservas_detalle_por_ramo_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.inversiones_reservas_tecnicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.gastos_vs_primas ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.balances_condensados ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.estados_ingresos_egresos ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.gestion_general ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.datos_por_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.indicadores_financieros_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.suficiencia_patrimonio ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.series_historicas_primas ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.reservas_hospitalizacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.cantidad_polizas_siniestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.listados_empresas ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.balance_por_empresa_reaseguros ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.ingresos_egresos_por_empresa_reaseguros ENABLE ROW LEVEL SECURITY;
ALTER TABLE anuario.capital_garantia_por_empresa ENABLE ROW LEVEL SECURITY;

-- Lectura para anon y authenticated (nombres de política únicos por tabla)
DO $$
DECLARE
  t TEXT;
  tables TEXT[] := ARRAY['cuadros','primas_por_ramo','primas_por_ramo_empresa','siniestros_por_ramo','reservas_tecnicas_agregado','reservas_prima_por_ramo','reservas_prima_por_empresa','reservas_prestaciones_por_ramo','reservas_prestaciones_por_empresa','reservas_detalle_por_ramo_empresa','inversiones_reservas_tecnicas','gastos_vs_primas','balances_condensados','estados_ingresos_egresos','gestion_general','datos_por_empresa','indicadores_financieros_empresa','suficiencia_patrimonio','series_historicas_primas','reservas_hospitalizacion','cantidad_polizas_siniestros','listados_empresas','capital_garantia_por_empresa','balance_por_empresa_reaseguros','ingresos_egresos_por_empresa_reaseguros'];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format('CREATE POLICY "anuario_%s_read_anon" ON anuario.%I FOR SELECT TO anon USING (true)', t, t);
    EXECUTE format('CREATE POLICY "anuario_%s_read_auth" ON anuario.%I FOR SELECT TO authenticated USING (true)', t, t);
  END LOOP;
END $$;
