from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class PeriodoBancoDeHoras(BaseModel):
    codigo_do_periodo: str = Field(
        ..., description="Código do período de acúmulo de horas extras."
    )
    data_inicial_periodo: date = Field(
        ..., description="Data inicial do período dos movimentos."
    )
    data_final_periodo: date = Field(
        ..., description="Data final do período dos movimentos."
    )

    model_config = ConfigDict(from_attributes=True)


class ListaPeriodosBancoHoras(BaseModel):
    """
    Modelo do retorno de periodos para acúmulo de banco de horas.
    """

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
    periodos: List[PeriodoBancoDeHoras] = Field(
        default_factory=list,
        description="Lista contendo os períodos de computação de banco de horas.",
    )

    model_config = ConfigDict(from_attributes=True)
