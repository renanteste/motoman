from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DadosCadastroRecursos(BaseModel):
    codigo: Optional[str] = None
    ativo: Optional[bool] = None
    codigo_equipe: Optional[str] = None
    lider: Optional[bool] = None
    centro_custo: Optional[str] = None
    custo_terceiro_apontamento: Optional[str] = None
    matricula: Optional[str] = None
    codigo_usuario_protheus: Optional[str] = None
    permite_hora_extra: Optional[bool] = None
    codigo_funcao: Optional[str] = None
    codigo_fornecedor: Optional[str] = None
    cpf: Optional[str] = None
    data_bloqueio: Optional[datetime] = None


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
    email_usuario: Optional[str] = None
    usuario_bloqueado: Optional[bool] = None
    validade_usuario: Optional[datetime] = None
    solicitada_nova_senha: Optional[bool] = None
    dados_representante: Optional[DadosRepresentante] = None
    dados_vendedor: Optional[DadosVendedor] = None
    dados_cadastro_recursos: Optional[DadosCadastroRecursos] = None
    acessos: Optional[Acessos] = None


class DadosAutenticacao(BaseModel):
    token: Optional[str] = None
    validade: Optional[datetime] = None


class AuthResponse(BaseModel):
    dados_usuario: Optional[DadosUsuario] = None
    dados_autenticacao: Optional[DadosAutenticacao] = None
