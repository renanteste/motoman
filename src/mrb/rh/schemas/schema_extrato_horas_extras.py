from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field


class MovimentoExtratoHorasExtras(BaseModel):
    """
    Modelo do registro de movimento do Extrato de Horas Extras.
    """

    id: int = Field(..., examples=[99], description="Identificador único do registro.")
    matricula: str = Field(
        ...,
        max_length=6,
        min_length=4,
        examples=["123456"],
        description="Matrícula do colaborador.",
    )
    dia: date = Field(..., description="Data da movimentação de horas no extrato.")
    carga_horaria_dia: Decimal = Field(
        ...,
        max_digits=4,
        decimal_places=2,
        examples=[2.5],
        description="Quantidade de horas que compõem a carga horária para a data do movimento.",
    )
    tipo_registro: Literal[1, 2, 3] = Field(
        ...,
        examples=[1, 2, 3],
        description="""
                    Tipo do movimento no extrato.\n
                    1: Crédito, 2: Débito, 3: Encerramento de período""",
    )
    quantidade_horas_apontadas: Decimal = Field(
        ...,
        max_digits=4,
        decimal_places=2,
        examples=[2.5],
        description="Somatório dos apontamentos de horas na data.",
    )
    quantidade_horas_aprovadas: Decimal = Field(
        ...,
        max_digits=4,
        decimal_places=2,
        examples=[2.5],
        description="Total de horas extras aprovadas pelo Líder para a data.",
    )
    quantidade_horas_computadas: Decimal = Field(
        ...,
        max_digits=4,
        decimal_places=2,
        examples=[2.5],
        description="Quantidade de horas consideradas para o movimento do extrato.",
    )
    data_inclusao: datetime = Field(
        ...,
        description="Data e hora da inclusão do movimento no extrato.",
        examples=["2025-01-29T14:30:00"],
    )

    model_config = ConfigDict(from_attributes=True)


class ExtratoHorasExtras(BaseModel):
    """
    Modelo do retorno do extrato de horas extras.
    """

    matricula_do_lider: str = Field(
        ...,
        description="Matrícula do líder dos colaboradores com horas listadas no extrato.",
    )
    codigo_do_periodo: str = Field(
        ..., description="Código do período de acúmulo de horas extras."
    )
    data_inicial_movimentos: date = Field(
        ..., description="Data inicial do período dos movimentos."
    )
    data_final_movimentos: date = Field(
        ..., description="Data final do período dos movimentos."
    )
    total_de_registros: int = Field(
        default=0,
        examples=[100],
        description="Total de registros existentes para o critério de seleção.",
    )
    registros_por_pagina: int = Field(
        default=0,
        examples=[10],
        description="Tamanho definido para a página no retorno atual.",
    )
    pagina: int = Field(
        default=0,
        examples=[2],
        description="Número da página retornada.",
    )
    total_de_paginas: int = Field(
        default=0,
        examples=[20],
        description="Total de paginas calculado levando em consideração a quantidade de registros e o total de registros por página.",
    )
    movimentos: List[MovimentoExtratoHorasExtras] = Field(
        default_factory=list,
        description="Lista contendo os movimentos do extrato para o período.",
    )
