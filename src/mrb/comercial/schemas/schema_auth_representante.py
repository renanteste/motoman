from pydantic import BaseModel


class AuthRepresentante(BaseModel):
    """
    Retorno da autenticação para obtenção do token para o aplicativo do representante
    """

    cnpj: str
    email: str

    class Config:
        orm_mode = False
        from_attributes = False
