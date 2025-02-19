from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class OpcaoPortal(BaseModel):
    """Schema para opções de menu do portal."""

    codigo_rotina: str = Field(
        ...,
        examples=["SOLICITA_HE", "PROSPECT_APP"],
        description="Código de rotina do portal.",
    )
    descricao_menu: str = Field(
        ...,
        examples=["Solicitações Banco de Horas", "Aprovação Banco de Horas"],
        description="Descrição da rotina quando disponível no menu do portal.",
    )
    modulo: str = Field(
        ...,
        examples=["RH", "Comercial"],
        description="Módulo do portal ao qual a rotina pertence.",
    )
    url_view: Optional[str] = Field(
        None,
        examples=["/solicita_he", "/aprova_he"],
        description="Url de acesso a view que recupera a interface vinculada a rotina.",
    )
    icone: Optional[str] = Field(None, description="Ícone da rotina no menu do portal.")
    icone_selecionado: Optional[str] = Field(
        None, description="Ícone selecionado da rotina no menu do portal."
    )
    disponivel_menu: bool = Field(
        ..., description="Indica se a rotina está disponível no menu."
    )

    model_config = ConfigDict(from_attributes=True)
