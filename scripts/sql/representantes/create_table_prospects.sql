CREATE TABLE prospects (
    id INTEGER IDENTITY(1,1) PRIMARY KEY,
    cnpj_representante VARCHAR(14),
    cnpj VARCHAR(14),
    empresa VARCHAR(40),
    contato VARCHAR(15),
    departamento VARCHAR(50),
    cargo VARCHAR(30),
    endereco VARCHAR(40),
    complemento VARCHAR(50),
    bairro VARCHAR(50),
    cidade VARCHAR(50),
    estado VARCHAR(2),
    cep VARCHAR(8),
    telefone VARCHAR(15),
    ramal VARCHAR(6),
    celular VARCHAR(15),
    data_inclusao DATETIME,
    data_transmissao DATETIME,
    data_erp DATETIME,
    chave_prospect VARCHAR(50)
);
CREATE UNIQUE INDEX idx_prospects_id ON prospects (id);
CREATE INDEX idx_prospects_cnpj_id ON prospects (cnpj_representante, cnpj, id);
