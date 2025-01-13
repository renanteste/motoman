from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DadosCadastroRecursos(BaseModel):
    """Dados recuperados do cadastro de recursos do Protheus através do víncuo com o cadastro de usuário do portal."""

    codigo: Optional[str] = Field(None, description="Código do recurso.")
    ativo: Optional[bool] = Field(None, description="Indica se o recurso está ativo.")
    codigo_equipe: Optional[str] = Field(
        None, description="Código da equipe a qual o recurso está vinculado."
    )
    lider: Optional[bool] = Field(
        None, description="Indica se o recurso é líder de equipe."
    )
    centro_custo: Optional[str] = Field(
        None, description="Código do centro de custo do recurso."
    )
    custo_terceiro_apontamento: Optional[str] = Field(
        None, description="Código de vínculo do recurso com contrato de terceiro."
    )
    matricula: Optional[str] = Field(
        None,
        description="Matrícula do recurso que estabelece vínculo com o cadastro de funcionários.",
    )
    codigo_usuario_protheus: Optional[str] = Field(
        None, description="Vincula o recurso com o cadatro de usuários do Protheus."
    )
    permite_hora_extra: Optional[bool] = Field(
        None, description="Indica se o recurso pode fazer hora extra."
    )
    codigo_funcao: Optional[str] = Field(
        None, description="Código da função do recurso."
    )
    codigo_fornecedor: Optional[str] = Field(
        None, description="Código que vincula o recurso ao cadastro de fornecedores."
    )
    cpf: Optional[str] = Field(None, description="CPF do recurso.")
    data_bloqueio: Optional[datetime] = Field(
        None, description="Data de bloqueio do recurso."
    )


class DadosRepresentante(BaseModel):
    """Classe apresenta os dados quando o usuário é um representante comercial."""

    codigo: Optional[str] = Field(None, description="Código do cadastro de vendedores.")
    nome: Optional[str] = Field(None, description="Nome do representante / vendedor.")
    cnpj: Optional[str] = Field(None, description="CNPJ do representante / vendedor.")


class DadosVendedor(DadosRepresentante):
    """Classe apresenta os dados quando o usuário é um vendedor."""

    pass


class Acessos(BaseModel):
    """Lista de acessos ao portal do usuário logado."""

    lista_acesso: Optional[list[str]] = None


class DadosUsuario(BaseModel):
    """Dados do usuário logado no portal, obtidos a partir da tabela SZK no Protheus."""

    id_usuario: Optional[str] = Field(None, description="Identificador do usuário.")
    nome_usuario: Optional[str] = Field(None, description="Nome do usuário.")
    email_usuario: Optional[str] = Field(None, description="E-mail do usuário.")
    usuario_bloqueado: Optional[bool] = Field(
        None, description="Indica se o usuário está bloqueado."
    )
    validade_usuario: Optional[datetime] = Field(
        None, description="Data de validade do usuário."
    )
    solicitada_nova_senha: Optional[bool] = Field(
        None,
        description="Se true, indica que será enviada nova senha no próximo acesso.",
    )
    dados_representante: Optional[DadosRepresentante] = Field(
        None, description="Preenchido quando o usuário é um representante."
    )
    dados_vendedor: Optional[DadosVendedor] = Field(
        None, description="Preenchido quando o usuário é um vendedor."
    )
    dados_cadastro_recursos: Optional[DadosCadastroRecursos] = Field(
        None,
        description="Dados do cadastro de recursos vinculado ao usuário do portal.",
    )
    acessos: Optional[Acessos] = Field(
        None, description="Lista de acessos do usuário no portal."
    )


class DadosAutenticacao(BaseModel):
    token: Optional[str] = Field(
        None, description="Token de autenticação para acessar às rotinas da API."
    )
    validade: Optional[datetime] = Field(
        None, description="Data e hora de validade do token."
    )


class AuthResponse(BaseModel):
    dados_usuario: Optional[DadosUsuario] = Field(
        None, description="Dados do usuário autenticado."
    )
    dados_autenticacao: Optional[DadosAutenticacao] = Field(
        None, description="Informações para autenticação na API."
    )
