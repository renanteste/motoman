from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from datetime import datetime

Base = declarative_base()


class CallReports(Base):
    __tablename__ = "call_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj_representante = Column(String(14), nullable=False)
    cnpj_prospect = Column(String(14), nullable=False)
    data_visita = Column(DateTime, nullable=False)
    pessoa_contato = Column(String(15), nullable=False)
    cargo_pessoa_contato = Column(String(30), nullable=False)
    projeto = Column(String(50), nullable=False)
    motivo_visita = Column(String(50), nullable=False)
    processos = Column(String(300), nullable=True)
    interacoes_feedback = Column(Text, nullable=True)
    acoes_tomadas = Column(Text, nullable=True)
    proximos_passos = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    tipo_de_oferta = Column(Text, nullable=True)
    expectativa = Column(Text, nullable=True)
    valor = Column(Float, nullable=True)
    street = Column(String(40), nullable=True)
    postal_code = Column(String(8), nullable=True)
    administrative_area = Column(String(50), nullable=True)
    sub_administrative_area = Column(String(50), nullable=True)
    sub_locality = Column(String(50), nullable=True)
    sub_thoroughfare = Column(String(50), nullable=True)
    tipo_visita = Column(String(50), nullable=True)
    data_transmissao = Column(DateTime, default=datetime.now)
    chave_visita = Column(String(50), nullable=True)
