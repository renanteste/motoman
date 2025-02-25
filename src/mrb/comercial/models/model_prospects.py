from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

Base = declarative_base()


class Prospects(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj_representante = Column(String(14), nullable=False)
    cnpj = Column(String(14), nullable=False)
    empresa = Column(String(40), nullable=False)
    contato = Column(String(15), nullable=False)
    departamento = Column(String(50), nullable=False)
    cargo = Column(String(30), nullable=False)
    endereco = Column(String(40), nullable=False)
    complemento = Column(String(50), nullable=True)
    bairro = Column(String(50), nullable=False)
    cidade = Column(String(50), nullable=False)
    estado = Column(String(2), nullable=False)
    cep = Column(String(8), nullable=False)
    telefone = Column(String(15), nullable=False)
    ramal = Column(String(6), nullable=True)
    celular = Column(String(15), nullable=False)
    data_inclusao = Column(DateTime, nullable=False)
    data_transmissao = Column(DateTime, default=datetime.now)
    chave_prospect = Column(String(50), nullable=True)
