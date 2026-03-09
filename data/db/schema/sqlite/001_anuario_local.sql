-- =============================================================================
-- ANUARIO "SEGURO EN CIFRAS" - RÉPLICA LOCAL (SQLite)
-- Misma estructura lógica que PostgreSQL (001 + 002). Sin schema; tablas con
-- prefijo anuario_ . JSONB -> TEXT. SERIAL -> INTEGER PRIMARY KEY AUTOINCREMENT.
-- Ejecutar contra data/db/local/anuario_tematico.db (o el archivo que uses).
--
-- ALCANCE: Solo datos de anuarios PDF "Seguro en Cifras". Otras fuentes (Excel, etc.)
-- tendrán estructura y documentación propias (ver docs/FUENTES_DE_DATOS.md).
-- =============================================================================

-- Catálogo de cuadros (dimension)
CREATE TABLE IF NOT EXISTS anuario_cuadros (
    cuadro_id   TEXT PRIMARY KEY,
    nombre      TEXT,
    sector      TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- Seed cuadros 1 a 58 (omitir si ya existe)
INSERT OR IGNORE INTO anuario_cuadros (cuadro_id, nombre, sector) VALUES
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
('58', 'Indicadores financieros 2023 medicina prepagada', 'medicina_prepagada');

-- 23 tablas temáticas (datos -> TEXT en lugar de JSONB)
CREATE TABLE IF NOT EXISTS anuario_primas_por_ramo (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), origen_archivo TEXT, concepto_ramo TEXT, seguro_directo TEXT, reaseguro_aceptado TEXT, total TEXT, pct TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_primas_por_ramo_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_siniestros_por_ramo (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), origen_archivo TEXT, concepto_ramo TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_reservas_tecnicas_agregado (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto TEXT, monto TEXT, tipo TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_reservas_prima_por_ramo (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto_ramo TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_reservas_prima_por_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_reservas_prestaciones_por_ramo (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto_ramo TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_reservas_prestaciones_por_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_reservas_detalle_por_ramo_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), origen_archivo TEXT, fila_orden INTEGER, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_inversiones_reservas_tecnicas (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto TEXT, monto TEXT, tipo TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_gastos_vs_primas (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), origen_archivo TEXT, concepto_ramo_o_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_balances_condensados (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto TEXT, monto TEXT, tipo TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_estados_ingresos_egresos (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto TEXT, monto TEXT, tipo TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_gestion_general (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto TEXT, monto TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_datos_por_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_indicadores_financieros_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_suficiencia_patrimonio (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_series_historicas_primas (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), tipo_serie TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_reservas_hospitalizacion (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_cantidad_polizas_siniestros (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto_ramo_o_empresa TEXT, polizas TEXT, siniestros TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_capital_garantia_por_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), inscripcion_numero TEXT, inscripcion_anio TEXT, nombre_empresa TEXT, capital_social_suscrito TEXT, garantia_operaciones_seguros TEXT, garantia_operaciones_fideicomiso TEXT, garantia_total TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_listados_empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), numero_orden INTEGER, nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_balance_por_empresa_reaseguros (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), concepto TEXT, nombre_empresa TEXT, monto TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS anuario_ingresos_egresos_por_empresa_reaseguros (id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, cuadro_id TEXT NOT NULL REFERENCES anuario_cuadros(cuadro_id), nombre_empresa TEXT, datos TEXT, created_at TEXT DEFAULT (datetime('now')));

-- Índices (réplica de los de PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_anuario_primas_por_ramo_anio ON anuario_primas_por_ramo(anio);
CREATE INDEX IF NOT EXISTS idx_anuario_primas_por_ramo_empresa_anio ON anuario_primas_por_ramo_empresa(anio);
CREATE INDEX IF NOT EXISTS idx_anuario_balances_condensados_anio ON anuario_balances_condensados(anio);
CREATE INDEX IF NOT EXISTS idx_anuario_datos_por_empresa_anio ON anuario_datos_por_empresa(anio);
CREATE INDEX IF NOT EXISTS idx_anuario_indicadores_financieros_empresa_anio ON anuario_indicadores_financieros_empresa(anio);
CREATE INDEX IF NOT EXISTS idx_anuario_listados_empresas_anio ON anuario_listados_empresas(anio);
CREATE INDEX IF NOT EXISTS idx_anuario_balance_por_empresa_reaseguros_anio ON anuario_balance_por_empresa_reaseguros(anio);