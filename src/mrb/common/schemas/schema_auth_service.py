from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DadosRepresentante(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None
    cnpj: Optional[str] = None


class DadosVendedor(DadosRepresentante):
    pass


class Acessos(BaseModel):
    lista_acesso: Optional[list[str]] = None


class DadosUsuario(BaseModel):
    id_usuario: Optional[str] = None
    nome_usuario: Optional[str] = None
    usuario_bloqueado: Optional[bool] = None
    validade_usuario: Optional[datetime] = None
    dados_representante: Optional[DadosRepresentante] = None
    dados_vendedor: Optional[DadosVendedor] = None
    acessos: Optional[Acessos] = None


class DadosAutenticacao(BaseModel):
    token: Optional[str] = None
    validade: Optional[datetime] = None


class AuthResponse(BaseModel):
    dados_usuario: Optional[DadosUsuario] = None
    dados_autenticacao: Optional[DadosAutenticacao] = None
