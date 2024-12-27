from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
from datetime import datetime


class LiberacaoHorasExtras(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Liberações de Horas Extras
    """

    id: int
    matricula: str
    nome: str
    data_solicitacao: datetime
    data_planejada: datetime
    motivo: str
    total_horas_planejada: Decimal = Field(..., max_digits=4, decimal_places=2)
    status_aprovacao: Literal[
        "0", "1", "2", "3", "4"
    ]  # 0: Digitação, 1: Aguardando aprovação, 2: Aprovada, 3: Rejeitada, 4: Realizada
    matricula_aprovador: Optional[str] = None
    comentario_aprovador: Optional[str] = None
    data_aprovacao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ListaLiberacaoHorasExtras(BaseModel):
    """
    Modelo listagem de retorno de Liberações de Horas Extras
    """

    total_de_registros: int = 0
    pagina: int = 0
    registros_por_pagina: int = 0
    total_de_paginas: int = 0
    liberacoes_horas_extras: List[LiberacaoHorasExtras]

    model_config = ConfigDict(from_attributes=True)
