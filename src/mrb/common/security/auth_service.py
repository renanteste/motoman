import base64
import secrets
import string
import jwt
import pytz
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Select, and_, update
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError
from jwt import ExpiredSignatureError, InvalidTokenError

from src.mrb.common.email.email_service import EmailService
from src.mrb.common.database.db_engine import get_db
from src.mrb.common.models.model_usuarios_portal import usuarios_szk
from src.mrb.common.models.model_acessos_portal import usuarios_szl
from src.mrb.common.models.model_recursos_protheus import recursos_ae8
from src.mrb.comercial.models.model_vendedores import vendedores_sa3
from src.mrb.common.config import Environment
from src.mrb.common.security.criptografia import (
    DecriptRequisicao,
    EncriptRequisicao,
    decript,
    encript,
)
from src.mrb.common.schemas.schema_auth_service import (
    Acessos,
    AuthResponse,
    DadosAutenticacao,
    DadosCadastroRecursos,
    DadosUsuario,
    DadosVendedor,
)

auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")
TAMANHO_SENHA = usuarios_szk.columns["ZK_SENHA"].type.length
TAMANHO_IV = usuarios_szk.columns["ZK_SAL"].type.length


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.dados_usuario = DadosUsuario()
        self.senha_usuario: str
        self.sal_senha_usuario: str
        self.usuario_autenticado: bool
        self.autenticacao = DadosAutenticacao()

    def gera_token(self) -> DadosAutenticacao:
        dados_autenticacao = DadosAutenticacao()
        try:
            dados_autenticacao.validade = datetime.now(pytz.UTC) + timedelta(minutes=15)
            payload = {
                "sub": self.dados_usuario.id_usuario,
                "exp": dados_autenticacao.validade,
            }
            dados_autenticacao.token = jwt.encode(
                payload, Environment.PORTAL_PY_K, algorithm="HS256"
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro gerando token: {e}",
            )

        return dados_autenticacao

    def senha_valida(self, senha_digitada: str) -> bool:
        try:
            senha_descriptografada = decript(
                DecriptRequisicao(senha=self.senha_usuario, iv=self.sal_senha_usuario)
            ).senha
            return senha_descriptografada == senha_digitada

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{e}",
            )

    def valida_acesso(self, id_usuario: str, ponto_acesso: str) -> bool:
        tem_acesso = False

        # Obtém a conta do usuário pelo id
        szk = aliased(usuarios_szk, name="szk")
        query = Select(szk.c.ZK_EMAIL).where(
            szk.c.D_E_L_E_T_ == " ", szk.c.ZK_FILIAL == " ", szk.c.ZK_ID == id_usuario
        )
        recupera_conta = self.db.execute(query).fetchone()

        # Se recuperou a conta, recupera os dados do usuário e verifica se tem acesso ao end point
        if recupera_conta:
            self.recupera_dados_usuario(recupera_conta.ZK_EMAIL.strip())
            if (
                self.dados_usuario.acessos
                and ponto_acesso.upper() in self.dados_usuario.acessos.lista_acesso
            ):
                tem_acesso = True
            else:
                # Zera os dados do usuário por segurança
                self.dados_usuario = DadosUsuario()

        return tem_acesso

    def recupera_dados_usuario(self, conta_usuario: str):
        szk = aliased(usuarios_szk, name="szk")
        szl = aliased(usuarios_szl, name="szl")
        sa3 = aliased(vendedores_sa3, name="sa3")
        ae8 = aliased(recursos_ae8, name="ae8")
        query = (
            Select(
                szk.c.ZK_ID,
                szk.c.ZK_NOME,
                szk.c.ZK_MSBLQL,
                szk.c.ZK_MSBLQD,
                szk.c.ZK_SENHA,
                szk.c.ZK_SAL,
                szk.c.ZK_NVSENHA,
                sa3.c.A3_COD,
                sa3.c.A3_NOME,
                sa3.c.A3_CGC,
                sa3.c.A3_YTPREP,
                ae8.c.AE8_RECURS,
                ae8.c.AE8_ATIVO,
                ae8.c.AE8_EQUIP,
                ae8.c.AE8_XLIDER,
                ae8.c.AE8_XCUSTO,
                ae8.c.AE8_TERCEI,
                ae8.c.AE8_CODFUN,
                ae8.c.AE8_USER,
                ae8.c.AE8_XHREXT,
                ae8.c.AE8_FUNCAO,
                ae8.c.AE8_XFORNE,
                ae8.c.AE8_XFORLO,
                ae8.c.AE8_XCPF,
                ae8.c.AE8_DTBLOQ,
            )
            .join(
                sa3,
                and_(
                    sa3.c.D_E_L_E_T_ == " ",
                    sa3.c.A3_FILIAL == " ",
                    sa3.c.A3_COD == szk.c.ZK_VEND,
                ),
                isouter=True,
            )
            .join(
                ae8,
                and_(
                    ae8.c.D_E_L_E_T_ == " ",
                    ae8.c.AE8_FILIAL == "01",
                    ae8.c.AE8_RECURS == szk.c.ZK_CDRECUR,
                    ae8.c.AE8_DESCRI >= " ",
                ),
                isouter=True,
            )
            .where(
                szk.c.D_E_L_E_T_ == " ",
                szk.c.ZK_FILIAL == " ",
                szk.c.ZK_EMAIL == conta_usuario,
            )
        )
        dados_usuario = self.db.execute(query).fetchone()
        if dados_usuario:
            self.dados_usuario.id_usuario = dados_usuario.ZK_ID
            self.dados_usuario.nome_usuario = dados_usuario.ZK_NOME.strip()
            self.dados_usuario.email_usuario = conta_usuario
            self.dados_usuario.usuario_bloqueado = dados_usuario.ZK_MSBLQL == "1"
            self.dados_usuario.solicitada_nova_senha = dados_usuario.ZK_NVSENHA == "1"
            if not dados_usuario.ZK_MSBLQD.strip() == "":
                self.dados_usuario.validade_usuario = datetime.strptime(
                    dados_usuario.ZK_MSBLQD, "%Y%m%d"
                )

            self.senha_usuario = dados_usuario.ZK_SENHA.strip()
            self.sal_senha_usuario = dados_usuario.ZK_SAL.strip()

            # Se tem relacionamento com o cadastro de vendedores
            if dados_usuario.A3_COD:
                dados_vendedor = DadosVendedor()
                dados_vendedor.codigo = dados_usuario.A3_COD
                dados_vendedor.nome = dados_usuario.A3_NOME.strip()
                dados_vendedor.cnpj = dados_usuario.A3_CGC.strip()
                if dados_usuario.A3_YTPREP == "1":
                    self.dados_usuario.dados_representante = dados_vendedor
                else:
                    self.dados_usuario.dados_vendedor = dados_vendedor

            # Caso possua relacionamento com o cadastro de recursos
            if dados_usuario.AE8_RECURS:
                self.dados_usuario.dados_cadastro_recursos = DadosCadastroRecursos()
                self.dados_usuario.dados_cadastro_recursos.codigo = (
                    dados_usuario.AE8_RECURS.strip()
                )
                self.dados_usuario.dados_cadastro_recursos.ativo = (
                    dados_usuario.AE8_ATIVO == "1"
                )
                self.dados_usuario.dados_cadastro_recursos.codigo_equipe = (
                    dados_usuario.AE8_EQUIP.strip()
                )
                self.dados_usuario.dados_cadastro_recursos.lider = (
                    dados_usuario.AE8_XLIDER == "1"
                )
                self.dados_usuario.dados_cadastro_recursos.centro_custo = (
                    dados_usuario.AE8_XCUSTO.strip()
                )
                self.dados_usuario.dados_cadastro_recursos.custo_terceiro_apontamento = (
                    dados_usuario.AE8_TERCEI.strip()
                )
                self.dados_usuario.dados_cadastro_recursos.matricula = (
                    dados_usuario.AE8_CODFUN.strip()
                )
                self.dados_usuario.dados_cadastro_recursos.codigo_usuario_protheus = (
                    dados_usuario.AE8_USER.strip()
                )
                self.dados_usuario.dados_cadastro_recursos.permite_hora_extra = (
                    dados_usuario.AE8_XHREXT == "S"
                )
                self.dados_usuario.dados_cadastro_recursos.codigo_funcao = (
                    dados_usuario.AE8_FUNCAO.strip()
                )
                self.dados_usuario.dados_cadastro_recursos.codigo_fornecedor = f"{dados_usuario.AE8_XFORNE.strip()}-{dados_usuario.AE8_XFORLO.strip()}"
                self.dados_usuario.dados_cadastro_recursos.cpf = (
                    dados_usuario.AE8_XCPF.strip()
                )
                if not dados_usuario.AE8_DTBLOQ.strip() == "":
                    self.dados_usuario.dados_cadastro_recursos.data_bloqueio = (
                        datetime.strptime(dados_usuario.AE8_DTBLOQ, "%Y%m%d")
                    )

            # Recupera os acessos
            query = Select(szl.c.ZL_ACESSO).where(
                szl.c.D_E_L_E_T_ == " ",
                szl.c.ZL_FILIAL == " ",
                szl.c.ZL_IDUSUAR == self.dados_usuario.id_usuario,
            )
            acessos = self.db.execute(query).fetchall()
            if acessos:
                self.dados_usuario.acessos = Acessos()
                self.dados_usuario.acessos.lista_acesso = [
                    row.ZL_ACESSO.strip() for row in acessos
                ]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não existe!"
            )

    def autentica_usuario(self, conta_usuario: str, senha_informada: str):
        self.recupera_dados_usuario(conta_usuario)
        if self.dados_usuario.validade_usuario:
            validade_usuario = self.dados_usuario.validade_usuario
        else:
            validade_usuario = datetime.now()

        if validade_usuario < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cadastro de usuário vencido!",
            )
        elif self.dados_usuario.usuario_bloqueado:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cadastro de usuário bloqueado!",
            )
        elif self.dados_usuario.solicitada_nova_senha:
            self.gera_nova_senha()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enviada nova senha para o e-mail do usuário.",
            )
        elif not self.senha_valida(senha_informada):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Não autenticado!",
            )
        else:
            self.usuario_autenticado = True
            self.autenticacao = self.gera_token()

    def gera_nova_senha(self):
        szk = usuarios_szk

        # Gera nova senha com dígitos e letras maiúsculas
        nova_senha = "".join(
            secrets.choice(string.digits + string.ascii_uppercase) for _ in range(8)
        )
        # Criptografa a nova senha
        senha_criptografada = encript(requisicao=EncriptRequisicao(senha=nova_senha))
        # Grava a senha criptografada e o iv no banco de dados
        try:
            query = (
                update(szk)
                .where(
                    szk.c.D_E_L_E_T_ == " ",
                    szk.c.ZK_FILIAL == " ",
                    szk.c.ZK_ID == self.dados_usuario.id_usuario,
                )
                .values(
                    ZK_SENHA=senha_criptografada.senha.ljust(TAMANHO_SENHA),
                    ZK_SAL=senha_criptografada.iv.ljust(TAMANHO_IV),
                    ZK_NVSENHA="2",
                )
            )
            self.db.execute(query)
            self.db.commit()

        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha na gravação da senha: {e}",
            )

        # Envia e-mail ao usuário com a senha descriptografada gerada
        body = f"""
            <html>
                <body>
                    <p>Sua nova senha de acesso é <b>{nova_senha}</b>.</p>
                </body>
            </html>
            """
        envio_email = EmailService()
        if not envio_email.send_email(
            self.dados_usuario.email_usuario, "Acesso Portal MRB", body
        ):
            # Se o e-mail não foi enviado, retorna o flag de envio de e-mail na conta do usuário
            try:
                query = (
                    update(szk)
                    .where(
                        szk.c.D_E_L_E_T_ == " ",
                        szk.c.ZK_FILIAL == " ",
                        szk.c.ZK_ID == self.dados_usuario.id_usuario,
                    )
                    .values(
                        ZK_SENHA=self.senha_usuario.ljust(TAMANHO_SENHA),
                        ZK_SAL=self.sal_senha_usuario.ljust(TAMANHO_IV),
                        ZK_NVSENHA="1",
                    )
                )
                self.db.execute(query)
                self.db.commit()

            except SQLAlchemyError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Falha atualizando flag de envio de e-mail na conta do usuário: {e}",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=envio_email.mensagem,
            )


@auth_router.post("/auth")
async def login_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> AuthResponse:
    agente_requisicao = request.headers.get("User-Agent", default="indefinido")
    resultado_autenticacao = AuthResponse()
    conta_usuario = form_data.username.lower()
    senha_informada = base64.b64decode(form_data.password).decode("utf-8")

    auth_service = AuthService(db)
    auth_service.autentica_usuario(conta_usuario, senha_informada)
    if auth_service.usuario_autenticado:
        resultado_autenticacao.dados_autenticacao = auth_service.autenticacao
        resultado_autenticacao.dados_usuario = auth_service.dados_usuario

    return resultado_autenticacao.model_dump(
        exclude=(
            None if agente_requisicao == "PortalPy" else {"dados_usuario": {"acessos"}}
        )
    )


def valida_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, Environment.PORTAL_PY_K, algorithms=["HS256"])

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido!",
            headers={"WWW-Authenticate": "Bearer"},
        )
