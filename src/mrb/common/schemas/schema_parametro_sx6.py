from pydantic import BaseModel


class ParametroSx6(BaseModel):
    descricao_parametro: str
    tipo_conteudo_parametro: str
    conteudo_parametro: str
