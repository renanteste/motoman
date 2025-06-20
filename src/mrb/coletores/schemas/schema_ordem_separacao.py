from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrdemSeparacao(BaseModel):
    """
    Modelo da estrutura da ordem de separação
    """

    ordem_separacao: str = Field(
        ...,
        max_length=6,
        min_length=6,
        examples=["012345"],
        description="Número da ordem de separação",
    )
    projeto: str = Field(
        ...,
        max_length=10,
        min_length=1,
        examples=["PMS012124A"],
        description="Código do projeto para qual as peças se destinam ou ao qual o pedido se relaciona",
    )
    celula: str = Field(
        ...,
        max_length=15,
        min_length=1,
        examples=["CELNAC012124A"],
        description="Código do produto resultado do projeto",
    )
    pedido_vendas: Optional[str] = Field(
        None,
        max_length=6,
        examples=["123456"],
        description="Número do pedido de vendas que deu origem à ordem de separação",
    )
    nome_cliente: Optional[str] = Field(
        None,
        max_length=50,
        examples=["TOYOTA BOSHOKU DO BRASIL LTDA"],
        description="Nome do cliente do pedido ou do projeto",
    )
    conteiner: Optional[str] = Field(
        None,
        max_length=15,
        examples=["COMPRADOS"],
        description="Código que identifica o contêiner relacionado à ordem de separação",
    )

    model_config = ConfigDict(from_attributes=True)


class ItemOrdemSeparacao(BaseModel):
    item: str = Field(
        ...,
        max_length=2,
        min_length=2,
        examples=["01"],
        description="Código do item da ordem de separação",
    )
    pedido: str = Field(
        ...,
        max_length=6,
        min_length=2,
        examples=["01", "035999"],
        description="Número do pedido de vendas ou repete item da separação",
    )
    codigo_produto: str = Field(
        ...,
        max_length=15,
        min_length=1,
        examples=["158105-1"],
        description="Código do material que será separado",
    )
    almoxarifado: str = Field(
        ...,
        max_length=2,
        min_length=2,
        examples=["03"],
        description="Código do almoxarifado da ordem de separação",
    )
    posicao: str = Field(
        ...,
        max_length=15,
        min_length=1,
        examples=["3RI11E"],
        description="Código da posição de armazenamento do produto",
    )
    total_posicoes: int = Field(
        ...,
        examples=[1],
        description="Quantidade de posições possíveis para o item no almoxarifado",
    )
    quantidade_original: Decimal = Field(..., description="Quantidade original do item")
    saldo_separar: Decimal = Field(..., description="Saldo restante a separar")
    sequencia_pedido: Optional[str] = Field(
        None,
        max_length=2,
        examples=["01"],
        description="Sequencial de liberação do pedido de vendas",
    )
    enderecos_alternativos: Optional[List[str]] = Field(
        None,
        description="Lista de endereços alternativos para armazenamento do produto no armazém",
    )

    model_config = ConfigDict(from_attributes=True)


class ListaOrdensSeparacao(BaseModel):
    total_de_registros: int = Field(
        0, description="Total de ordens de separação listadas"
    )
    ordens_separacao: List[OrdemSeparacao] = Field(
        ..., description="Lista das ordens de separação"
    )

    model_config = ConfigDict(from_attributes=True)


class RegistraSeparacao(BaseModel):
    ordem_separacao: str = Field(
        ...,
        max_length=6,
        min_length=6,
        examples=["012345"],
        description="Número da ordem de separação",
    )
    item: str = Field(
        ...,
        max_length=2,
        min_length=2,
        examples=["01"],
        description="Código do item da ordem de separação",
    )
    codigo_produto: str = Field(
        ...,
        max_length=15,
        min_length=1,
        examples=["158105-1"],
        description="Código do material que será separado",
    )
    quantidade_separada: Decimal = Field(
        ..., description="Quantidade contada a separar"
    )
    almoxarifado: str = Field(
        ...,
        max_length=2,
        min_length=2,
        examples=["03"],
        description="Código do almoxarifado da ordem de separação",
    )
    pedido: Optional[str] = Field(
        None,
        max_length=6,
        examples=["123456"],
        description="Número do pedido de vendas que deu origem à ordem de separação",
    )
    sequencia_pedido: Optional[str] = Field(
        None,
        max_length=2,
        examples=["02"],
        description="Número sequencial de liberação do item do pedido de vendas",
    )

    model_config = ConfigDict(from_attributes=True)
