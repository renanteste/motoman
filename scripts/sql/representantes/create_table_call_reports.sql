CREATE TABLE call_reports (
    id INTEGER IDENTITY(1,1) PRIMARY KEY,
    cnpj_representante VARCHAR(14),
    cnpj_prospect VARCHAR(14),
    data_visita DATETIME,
    pessoa_contato VARCHAR(15),
    cargo_pessoa_contato VARCHAR(30),
    projeto VARCHAR(50),
    motivo_visita VARCHAR(50),
    processos VARCHAR(250),
    interacoes_feedback TEXT,
    acoes_tomadas TEXT,
    proximos_passos TEXT,
    observacoes TEXT,
    tipo_de_oferta TEXT,
    expectativa TEXT,
    valor FLOAT,
    street VARCHAR(40),
    postal_code VARCHAR(8),
    administrative_area VARCHAR(50),
    sub_administrative_area VARCHAR(50),
    sub_locality VARCHAR(50),
    sub_thoroughfare VARCHAR(50),
    tipo_visita VARCHAR(50),
    data_transmissao DATETIME,
    data_erp DATETIME,
    chave_visita VARCHAR(50)
);
CREATE UNIQUE INDEX idx_call_reports_id ON call_reports (id);
CREATE INDEX idx_call_reports_cnpj_representante_cnpj_prospect_data_visita 
ON call_reports (cnpj_representante, cnpj_prospect, data_visita);

