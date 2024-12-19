from pydantic import BaseModel


class OpcaoPortal(BaseModel):
    codigo_rotina: str
    descricao_menu: str
    modulo: str
    url_view: str
    icone: str
    icone_selecionado: str

    class Config:
        from_attributes = True
