from typing import Optional
from pydantic import BaseModel


class OpcaoPortal(BaseModel):
    codigo_rotina: str
    descricao_menu: str
    modulo: str
    url_view: Optional[str] = None
    icone: Optional[str] = None
    icone_selecionado: Optional[str] = None
    disponivel_menu: bool

    class Config:
        from_attributes = True
