from typing import Optional
from pydantic import BaseModel, ConfigDict


class OpcaoPortal(BaseModel):
    codigo_rotina: str
    descricao_menu: str
    modulo: str
    url_view: Optional[str] = None
    icone: Optional[str] = None
    icone_selecionado: Optional[str] = None
    disponivel_menu: bool

    model_config = ConfigDict(from_attributes=True)
