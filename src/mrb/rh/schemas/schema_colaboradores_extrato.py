from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class ColaboradorExtrato(BaseModel):
    matricula: str = Field(
        ...,
        max_length=6,
        min_length=4,
        examples=["123456"],
        description="Matrícula do colaborador.",
    )
    nome: str = Field(
        ...,
        examples=["JOSE DA SILVA"],
        description="Nome do colaborador.",
    )

    model_config = ConfigDict(from_attributes=True)


class ListaColaboradorExtrato(BaseModel):
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
    colaboradores: List[ColaboradorExtrato] = Field(
        default_factory=list,
        description="Lista contendo os colaboradores do extrato para o período.",
    )

    model_config = ConfigDict(from_attributes=True)
