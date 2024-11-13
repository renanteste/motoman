CREATE TABLE solicitacao_horas_extras (
    id INTEGER IDENTITY(1,1) PRIMARY KEY,
    matricula CHAR(6),
	data_solicitacao DATETIME,
    data_planejada DATETIME,
    motivo VARCHAR(250),
    total_horas_planejada DECIMAL(4,2),
	status_aprovacao CHAR(1),
	comentario_aprovador VARCHAR(250),
	matricula_aprovador CHAR(6),
	data_aprovacao DATETIME
);
CREATE UNIQUE INDEX idx_solicitacao_horas_extras_id ON solicitacao_horas_extras (id);
CREATE INDEX idx_solicitacao_horas_extras_matricula_status_aprovacao_matricula_aprovador 
ON solicitacao_horas_extras (matricula, status_aprovacao, matricula_aprovador);
