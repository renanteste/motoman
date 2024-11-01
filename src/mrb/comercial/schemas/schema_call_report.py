from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CallReport(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Call Reports
    """

    cnpj_prospect: str
    data_visita: datetime
    pessoa_contato: str
    cargo_pessoa_contato: str
    projeto: str
    motivo_visita: str
    id: Optional[int] = None
    cnpj_representante: Optional[str] = None
    processos: Optional[str] = None
    interacoes_feedback: Optional[str] = None
    acoes_tomadas: Optional[str] = None
    proximos_passos: Optional[str] = None
    observacoes: Optional[str] = None
    tipo_de_oferta: Optional[str] = None
    expectativa: Optional[str] = None
    valor: Optional[float] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    administrative_area: Optional[str] = None
    sub_administrative_area: Optional[str] = None
    sub_locality: Optional[str] = None
    sub_thoroughfare: Optional[str] = None
    tipo_visita: Optional[str] = None
    data_transmissao: Optional[datetime] = datetime.now()

    class Config:
        from_attributes = True
