from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime


class CallReport(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Call Reports
    """

    cnpj_prospect: str = Field(
        ...,
        max_length=14,
        min_length=14,
        examples=["12345678000112"],
        description="CNPJ do Prospect, sem pontos ou traços.",
    )
    data_visita: datetime = Field(
        ..., description="Data da visita realizada pelo representante."
    )
    pessoa_contato: str = Field(
        ...,
        max_length=15,
        examples=["João da Silva"],
        description="Nome da pessoa visitada.",
    )
    cargo_pessoa_contato: str = Field(
        ...,
        max_length=30,
        examples=["Gerente de Produção"],
        description="Cargo da pessoa visitada.",
    )
    projeto: str = Field(
        ...,
        max_length=50,
        examples=["Automação linha de soldagem"],
        description="Visita referete a qual projeto.",
    )
    motivo_visita: str = Field(
        ...,
        max_length=50,
        examples=["Apresentação de proposta"],
        description="Motivo da visita.",
    )
    id: Optional[int] = Field(
        None,
        examples=[9],
        description="ID do registro da call report gravado no BD. Não informar ao inserir novo registro.",
    )
    cnpj_representante: Optional[str] = Field(
        None,
        max_length=14,
        min_length=14,
        examples=["12345678000112"],
        description="""CNPJ do representante que está inserindo a Call Report, sem traços ou pontos. 
                        Preenchido automaticamente pela autenticação na API.""",
    )
    processos: Optional[str] = Field(None, max_length=250)
    interacoes_feedback: Optional[str] = Field(None)
    acoes_tomadas: Optional[str] = Field(None)
    proximos_passos: Optional[str] = Field(None)
    observacoes: Optional[str] = Field(None)
    tipo_de_oferta: Optional[str] = Field(None)
    expectativa: Optional[str] = Field(None)
    valor: Optional[float] = Field(
        None, examples=[1000.0], description="Valor estimado da oportunidade."
    )
    street: Optional[str] = Field(None, max_length=40)
    postal_code: Optional[str] = Field(
        None,
        max_length=8,
        examples=["12345678"],
        description="CEP do local da oportunidade, sem traços ou pontos.",
    )
    administrative_area: Optional[str] = Field(None, max_length=50)
    sub_administrative_area: Optional[str] = Field(None, max_length=50)
    sub_locality: Optional[str] = Field(None, max_length=50)
    sub_thoroughfare: Optional[str] = Field(None, max_length=50)
    tipo_visita: Optional[str] = Field(None, max_length=50)
    data_transmissao: Optional[datetime] = Field(
        datetime.now(),
        description="Data da transmissão do registro para a API. Não preencher na inserção.",
    )
    chave_visita: Optional[str] = Field(
        None,
        max_length=50,
        description="Chave que irá identificar o registro a partir do aplicativo de origem da informação.",
    )

    model_config = ConfigDict(from_attributes=True)


class ListagemCallReports(BaseModel):
    """
    Estrutura de retorno da listagem de call reports
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
    call_reports: List[CallReport] = Field(
        default_factory=list,
        description="Lista contendo a lista de Call Reports recuperadas.",
    )

    model_config = ConfigDict(from_attributes=True)
