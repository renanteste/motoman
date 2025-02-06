from sqlalchemy import (
    CHAR,
    DECIMAL,
    Column,
    Date,
    DateTime,
    Integer,
    SmallInteger,
    func,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MovimentosHorasExtras(Base):
    """
    Classe com a estrutura da tabela extrato_horas_extras no modelo do SQL Alchemy
    """

    __tablename__ = "extrato_horas_extras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    matricula = Column(CHAR(6), nullable=False)
    dia = Column(Date, nullable=False)
    carga_horaria_dia = Column(DECIMAL(4, 2), nullable=False)
    tipo_registro = Column(SmallInteger, nullable=False)
    quantidade_horas_apontadas = Column(DECIMAL(4, 2), nullable=False)
    quantidade_horas_aprovadas = Column(DECIMAL(4, 2), nullable=False)
    quantidade_horas_computadas = Column(DECIMAL(4, 2), nullable=False)
    data_inclusao = Column(DateTime, server_default=func.now(), nullable=False)
