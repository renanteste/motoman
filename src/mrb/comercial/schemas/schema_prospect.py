from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class Prospect(BaseModel):
    """
    Modelo da estrutura de recebimento e retorno de Prospects
    """

    cnpj: str = Field(
        ...,
        max_length=14,
        min_length=14,
        examples=["12345678000112"],
        description="CNPJ do Prospect, sem pontos ou traços.",
    )
    empresa: str = Field(
        ...,
        max_length=40,
        examples=["Toyota do Brasil"],
        description="Nome do Prospect.",
    )
    contato: str = Field(
        ...,
        max_length=15,
        examples=["João da Silva"],
        description="Nome da pessoa de contato.",
    )
    departamento: str = Field(
        ..., max_length=50, examples=["Compras"], description="Departamento do contato."
    )
    cargo: str = Field(
        ..., max_length=30, examples=["Gerente"], description="Cargo do contato."
    )
    endereco: str = Field(
        ..., max_length=40, examples=["Rua A, 670"], description="Endereço do Prospect."
    )
    bairro: str = Field(
        ..., max_length=50, examples=["Centro"], description="Bairro do Prospect."
    )
    cidade: str = Field(
        ..., max_length=50, examples=["São Paulo"], description="Cidade do Prospect."
    )
    estado: str = Field(
        ...,
        max_length=2,
        min_length=2,
        examples=["SP"],
        description="Sigla da UF do Prospect.",
    )
    cep: str = Field(
        ...,
        max_length=8,
        min_length=8,
        examples=["12345678"],
        description="CEP do Prospect, sem traços ou pontos.",
    )
    telefone: str = Field(
        ...,
        max_length=15,
        min_length=8,
        examples=["11 2222-3333", "11 39998888"],
        description="Telefone do Prospect.",
    )
    celular: str = Field(
        ...,
        max_length=15,
        min_length=9,
        examples=["11 99999-8888"],
        description="Celular do contato.",
    )
    data_inclusao: datetime = Field(..., description="Data de inclusão do Prospect.")
    id: Optional[int] = Field(
        None,
        examples=[1],
        description="ID do Prospect no banco de dados. Não preencher na inserção.",
    )
    complemento: Optional[str] = Field(
        None, max_length=50, examples=["Sala 2"], description="Complemento do endereço."
    )
    ramal: Optional[str] = Field(
        None,
        max_length=6,
        examples=["1234"],
        description="Ramal do telefone do contato.",
    )
    data_transmissao: Optional[datetime] = Field(
        datetime.now(),
        description="Data da transmissão do registro para a API. Não preencher na inserção.",
    )
    cnpj_representante: Optional[str] = Field(
        None,
        max_length=14,
        min_length=14,
        examples=["12345678000112"],
        description="""CNPJ do representante que está inserindo o Prospect, sem traços ou pontos. 
                        Preenchido automaticamente pela autenticação na API.""",
    )

    model_config = ConfigDict(from_attributes=True)
