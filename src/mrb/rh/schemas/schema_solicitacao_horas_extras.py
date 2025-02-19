from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
from datetime import datetime


class SolicitacaoHorasExtras(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Solicitações de Banco de Horas
    """

    matricula: str = Field(
        ...,
        max_length=6,
        min_length=4,
        examples=["123456"],
        description="Matrícula do colaborador.",
    )
    data_solicitacao: datetime = Field(
        ..., description="Data da inclusão da solicitação de Banco de Horas."
    )
    data_planejada: datetime = Field(
        ..., description="Data planejada para realização das Banco de Horas."
    )
    motivo: str = Field(
        ...,
        max_length=250,
        examples=["Realização de inventário físico"],
        description="Motivo da solicitação de Banco de Horas.",
    )
    total_horas_planejada: Decimal = Field(
        ...,
        max_digits=4,
        decimal_places=2,
        examples=[2.5],
        description="Total de horas planejadas.",
    )
    status_aprovacao: Literal["0", "1", "2", "3", "4"] = Field(
        ...,
        examples=["0", "1", "2", "3", "4"],
        description="""
                    Status da aprovação da solicitação.\n
                    0: Digitação, 1: Aguardando aprovação, 2: Aprovada, 3: Rejeitada, 4: Realizada""",
    )
    id: Optional[int] = Field(
        0,
        examples=[23],
        description="ID da solicitação de Banco de Horas. Não informar ao inserir novo registro.",
    )
    comentario_aprovador: Optional[str] = Field(
        None,
        max_length=250,
        examples=["O inventário programado foi cancelado!"],
        description="Comentário do aprovador sobre a liberação ou rejeição.",
    )
    matricula_aprovador: Optional[str] = Field(
        None,
        max_length=6,
        min_length=4,
        examples=["123456"],
        description="Matrícula do usuário aprovador.",
    )
    data_aprovacao: Optional[datetime] = Field(
        None, description="Data da aprovação ou rejeição da solicitação."
    )

    model_config = ConfigDict(from_attributes=True)


class ListaSolicitacaoHorasExtras(BaseModel):
    """
    Modelo listagem de retorno de Solicitações de Banco de Horas
    """

    total_de_registros: int = Field(0, description="Total de registros encontrados.")
    pagina: int = Field(0, description="Número da página atual.")
    registros_por_pagina: int = Field(
        0, description="Quantidade de registros por página."
    )
    total_de_paginas: int = Field(0, description="Total de páginas encontradas.")
    solicitacoes_horas_extras: List[SolicitacaoHorasExtras] = Field(
        ..., description="Lista de solicitações de Banco de Horas."
    )

    model_config = ConfigDict(from_attributes=True)
