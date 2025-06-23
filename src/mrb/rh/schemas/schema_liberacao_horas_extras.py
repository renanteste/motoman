from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
from datetime import datetime


class LiberacaoHorasExtras(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Liberações de Banco de Horas
    """

    id: int = Field(
        ...,
        examples=[23],
        description="ID da solicitação de liberação de Banco de Horas.",
    )
    matricula: str = Field(
        ..., examples=["123456"], description="Matrícula do colaborador."
    )
    nome: str = Field(
        ..., examples=["João da Silva"], description="Nome do colaborador."
    )
    data_solicitacao: datetime = Field(
        ..., description="Data da solicitação de liberação de Banco de Horas."
    )
    data_planejada: datetime = Field(
        ..., description="Data planejada para realização das Banco de Horas."
    )
    motivo: str = Field(
        ...,
        examples=["Realização de inventário físico"],
        description="Motivo da solicitação de liberação de Banco de Horas.",
    )
    total_horas_planejada: Decimal = Field(
        ..., max_digits=4, decimal_places=2, description="Total de horas planejadas."
    )
    status_aprovacao: Literal["0", "1", "2", "3", "4"] = Field(
        ...,
        examples=["0", "1", "2", "3", "4"],
        description="""
                    Status da aprovação da solicitação.\n
                    0: Digitação, 1: Aguardando aprovação, 2: Aprovada, 3: Rejeitada, 4: Realizada""",
    )
    tipo_registro: Literal[1, 2] = Field(
        ...,
        examples=[1, 2],
        description="""
                    Tipo do movimento da solicitação.\n
                    1: Crédito, 2: Débito""",
    )
    matricula_aprovador: Optional[str] = Field(
        ..., examples=["123456"], description="Matrícula do usuário aprovador."
    )
    comentario_aprovador: Optional[str] = Field(
        None,
        examples=["O inventário programado foi cancelado!"],
        description="Comentário do aprovador sobre a liberação ou rejeição.",
    )
    data_aprovacao: Optional[datetime] = Field(
        None, description="Data da aprovação ou rejeição da solicitação."
    )

    model_config = ConfigDict(from_attributes=True)


class ListaLiberacaoHorasExtras(BaseModel):
    """
    Modelo listagem de retorno de Liberações de Banco de Horas
    """

    total_de_registros: int = Field(0, description="Total de registros encontrados.")
    pagina: int = Field(0, description="Número da página atual.")
    registros_por_pagina: int = Field(
        0, description="Quantidade de registros por página."
    )
    total_de_paginas: int = Field(0, description="Total de páginas encontradas.")
    liberacoes_horas_extras: List[LiberacaoHorasExtras] = Field(
        None, description="Lista de liberações de Banco de Horas."
    )

    model_config = ConfigDict(from_attributes=True)
