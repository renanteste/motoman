from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Prospect(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Prospects
    """

    cnpj: str
    empresa: str
    contato: str
    departamento: str
    cargo: str
    endereco: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    telefone: str
    celular: str
    data_inclusao: datetime
    id: Optional[int] = None
    complemento: Optional[str] = None
    ramal: Optional[str] = None
    data_transmissao: Optional[datetime] = datetime.now()
    cnpj_representante: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
