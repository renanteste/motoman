from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import CHAR, DECIMAL, Column, Integer, String, DateTime

Base = declarative_base()


class SolicitacaoHorasExtras(Base):
    __tablename__ = "solicitacao_horas_extras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    matricula = Column(CHAR(6), nullable=False)
    data_solicitacao = Column(DateTime, nullable=False)
    data_planejada = Column(DateTime, nullable=False)
    motivo = Column(String(250), nullable=False)
    total_horas_planejada = Column(DECIMAL(4, 2), nullable=False)
    status_aprovacao = Column(CHAR(1), nullable=False)
    comentario_aprovador = Column(String(250), nullable=True)
    matricula_aprovador = Column(CHAR(6), nullable=True)
    data_aprovacao = Column(DateTime, nullable=True)
