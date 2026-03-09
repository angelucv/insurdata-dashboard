-- =============================================================================
-- ANUARIO "SEGURO EN CIFRAS" - DIMENSIONES (PostgreSQL / Supabase)
-- Ejecutar primero. Misma estructura para réplica local (PostgreSQL) y Supabase.
--
-- ALCANCE: Este schema y todas las tablas anuario.* son SOLO para datos
-- provenientes de los anuarios PDF "Seguro en Cifras" (CSV en staged/.../verificadas).
-- Otras fuentes (Excel, etc.) deben usar otro schema o documentación propia.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS anuario;

-- Catálogo de cuadros del anuario (3 a 58). Todas las tablas temáticas referencian este catálogo.
CREATE TABLE anuario.cuadros (
    cuadro_id   TEXT PRIMARY KEY,
    nombre      TEXT,
    sector      TEXT,  -- seguro_directo | reaseguro | financiadoras_primas | medicina_prepagada
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE anuario.cuadros IS 'Catálogo de cuadros del anuario; cuadro_id usado como FK en tablas temáticas.';

-- Seed: cuadros 1 a 58
INSERT INTO anuario.cuadros (cuadro_id, nombre, sector) VALUES
('1', 'Empresas de seguro autorizadas', 'seguro_directo'),
('2', 'Capital y garantía por empresa', 'seguro_directo'),
('3', 'Primas por ramo', 'seguro_directo'),
('4', 'Primas por ramo y empresa', 'seguro_directo'),
('5-A', 'Primas Personas (por ramo)', 'seguro_directo'),
('5-B', 'Primas Patrimoniales (por ramo)', 'seguro_directo'),
('5-C', 'Primas Obligacionales (por ramo)', 'seguro_directo'),
('6', 'Siniestros pagados por ramo', 'seguro_directo'),
('7', 'Siniestros por ramo y empresa', 'seguro_directo'),
('8-A', 'Siniestros Personas (por ramo)', 'seguro_directo'),
('8-B', 'Siniestros Patrimoniales (por ramo)', 'seguro_directo'),
('8-C', 'Siniestros Obligacionales (por ramo)', 'seguro_directo'),
('9', 'Reservas técnicas', 'seguro_directo'),
('10', 'Reservas de prima por ramo', 'seguro_directo'),
('11', 'Reservas de prima por empresa', 'seguro_directo'),
('12', 'Reservas de prima Personas por empresa', 'seguro_directo'),
('13', 'Reservas de prima Patrimoniales por empresa', 'seguro_directo'),
('14', 'Reservas de prima Obligacionales por empresa', 'seguro_directo'),
('15', 'Reservas prestaciones/siniestros por ramo', 'seguro_directo'),
('16', 'Reservas prestaciones/siniestros por empresa', 'seguro_directo'),
('17', 'Reservas prestaciones Personas por empresa', 'seguro_directo'),
('18', 'Reservas prestaciones Patrimoniales por empresa', 'seguro_directo'),
('19', 'Reservas prestaciones Obligacionales por empresa', 'seguro_directo'),
('20-A', 'Reservas prima Personas por ramo/empresa', 'seguro_directo'),
('20-B', 'Reservas prima Patrimoniales por ramo/empresa', 'seguro_directo'),
('20-C', 'Reservas prima Obligacionales por ramo/empresa', 'seguro_directo'),
('20-D', 'Reservas prestaciones Personas por ramo/empresa', 'seguro_directo'),
('20-E', 'Reservas prestaciones Patrimoniales por ramo/empresa', 'seguro_directo'),
('20-F', 'Reservas prestaciones Obligacionales por ramo/empresa', 'seguro_directo'),
('21', 'Inversiones reservas técnicas', 'seguro_directo'),
('22', 'Gastos administración vs primas por empresa', 'seguro_directo'),
('23', 'Gastos producción vs primas por ramo', 'seguro_directo'),
('23-A', 'Comisiones Personas por ramo', 'seguro_directo'),
('23-B', 'Comisiones Patrimoniales por ramo', 'seguro_directo'),
('23-C', 'Comisiones Obligacionales por ramo', 'seguro_directo'),
('23-D', 'Gastos adm Personas por ramo', 'seguro_directo'),
('23-E', 'Gastos adm Patrimoniales por ramo', 'seguro_directo'),
('23-F', 'Gastos adm Obligacionales por ramo', 'seguro_directo'),
('24', 'Balance condensado', 'seguro_directo'),
('25-A', 'Estado ganancias y pérdidas - Ingresos', 'seguro_directo'),
('25-B', 'Estado ganancias y pérdidas - Egresos', 'seguro_directo'),
('26', 'Gestión general', 'seguro_directo'),
('27', 'Rentabilidad inversiones por empresa', 'seguro_directo'),
('28', 'Resultados ejercicio 2019-2023 por empresa', 'seguro_directo'),
('29', 'Indicadores financieros 2023 por empresa', 'seguro_directo'),
('30', 'Suficiencia patrimonio/solvencia 2022-2023', 'seguro_directo'),
('31-A', 'Primas netas cobradas 2023 vs 2022', 'seguro_directo'),
('31-B', 'Primas / Prestaciones y siniestros 1990-2023', 'seguro_directo'),
('32', 'Reservas hospitalización individual', 'seguro_directo'),
('33', 'Reservas hospitalización colectivo', 'seguro_directo'),
('34', 'Primas brutas Personas/Generales por empresa', 'seguro_directo'),
('35', 'Devolución primas Personas/Generales por empresa', 'seguro_directo'),
('36', 'Reservas prestaciones pendientes y no notificados por empresa', 'seguro_directo'),
('37', 'Cantidad pólizas y siniestros por ramo', 'seguro_directo'),
('38', 'Cantidad pólizas y siniestros por empresa', 'seguro_directo'),
('39', 'Empresas de reaseguro autorizadas', 'reaseguro'),
('40', 'Balance condensado reaseguros', 'reaseguro'),
('41-A', 'Estado ganancias y pérdidas - Ingresos reaseguros', 'reaseguro'),
('41-B', 'Estado ganancias y pérdidas - Egresos reaseguros', 'reaseguro'),
('42', 'Balance condensado por empresa reaseguros', 'reaseguro'),
('43-A', 'Ingresos por empresa reaseguros', 'reaseguro'),
('43-B', 'Egresos por empresa reaseguros', 'reaseguro'),
('44', 'Indicadores financieros 2023 reaseguros', 'reaseguro'),
('45', 'Suficiencia patrimonio reaseguros 2022-2023', 'reaseguro'),
('46', 'Empresas financiadoras de primas autorizadas', 'financiadoras_primas'),
('47', 'Balance condensado financiadoras de primas', 'financiadoras_primas'),
('48', 'Estado ganancias y pérdidas financiadoras de primas', 'financiadoras_primas'),
('49', 'Ingresos por empresa financiadoras de primas', 'financiadoras_primas'),
('50', 'Circulante (Activo) por empresa financiadoras de primas', 'financiadoras_primas'),
('51', 'Gastos operativos/administrativos/financieros por empresa financiadoras', 'financiadoras_primas'),
('52', 'Indicadores financieros 2023 financiadoras de primas', 'financiadoras_primas'),
('53', 'Empresas medicina prepagada autorizadas', 'medicina_prepagada'),
('54', 'Balance condensado medicina prepagada', 'medicina_prepagada'),
('55-A', 'Estado ganancias y pérdidas - Ingresos medicina prepagada', 'medicina_prepagada'),
('55-B', 'Estado ganancias y pérdidas - Egresos medicina prepagada', 'medicina_prepagada'),
('56', 'Ingresos netos por empresa medicina prepagada', 'medicina_prepagada'),
('57', 'Reservas técnicas por empresa medicina prepagada', 'medicina_prepagada'),
('58', 'Indicadores financieros 2023 medicina prepagada', 'medicina_prepagada')
ON CONFLICT (cuadro_id) DO NOTHING;
