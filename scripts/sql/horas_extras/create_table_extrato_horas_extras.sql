CREATE TABLE extrato_horas_extras (
	id INTEGER IDENTITY(1,1) PRIMARY KEY,
	matricula CHAR(6),
	dia DATETIME,
	carga_horaria_dia DECIMAL(4,2),
	tipo_registro TINYINT,
	quantidade_horas_apontadas DECIMAL(4,2),
	quantidade_horas_aprovadas DECIMAL(4,2),
	quantidade_horas_computadas DECIMAL(4,2),
	data_inclusao DATETIME2 DEFAULT GETDATE()
);
CREATE UNIQUE INDEX idx_extrato_horas_extras_id ON extrato_horas_extras (id);
CREATE INDEX idx_extrato_horas_extras_matricula_dia
ON extrato_horas_extras (matricula, dia, data_inclusao);
