from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class SolicitacaoHorasExtras(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Solicitações de Horas Extras
    """

    matricula: str
    data_solicitacao: datetime
    data_planejada: datetime
    motivo: str
    total_horas_planejada: Decimal = Field(..., max_digits=4, decimal_places=2)
    status_aprovacao: Literal[
        "0", "1", "2", "3"
    ]  # 0: Digitação, 1: Aguardando aprovação, 2: Aprovada, 3: Rejeitada
    id: Optional[int] = None
    comentario_aprovador: Optional[str]
    matricula_aprovador: Optional[str]
    data_aprovacao: Optional[datetime]

    class Config:
        from_attributes = True
