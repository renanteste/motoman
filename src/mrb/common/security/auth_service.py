import jwt
import pytz
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Select, and_
from sqlalchemy.orm import Session, aliased
from jwt import ExpiredSignatureError, InvalidTokenError

from src.mrb.common.database.db_engine import get_db
from src.mrb.common.models.model_usuarios_portal import usuarios_szk
from src.mrb.common.models.model_acessos_portal import usuarios_szl
from src.mrb.comercial.models.model_vendedores import vendedores_sa3
from src.mrb.common.config import Environment
from src.mrb.common.security.criptografia import decript
from src.mrb.common.schemas.schema_auth_service import (
    Acessos,
    AuthResponse,
    DadosAutenticacao,
    DadosUsuario,
    DadosVendedor,
)

auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


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
                {"senha": self.senha_usuario, "iv": self.sal_senha_usuario}
            )["senha"]
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
            if ponto_acesso.upper() in self.dados_usuario.acessos.lista_acesso:
                tem_acesso = True
            else:
                # Zera os dados do usuário por segurança
                self.dados_usuario = DadosUsuario()

        return tem_acesso

    def recupera_dados_usuario(self, conta_usuario: str):
        szk = aliased(usuarios_szk, name="szk")
        szl = aliased(usuarios_szl, name="szl")
        sa3 = aliased(vendedores_sa3, name="sa3")
        query = (
            Select(
                szk.c.ZK_ID,
                szk.c.ZK_NOME,
                szk.c.ZK_MSBLQL,
                szk.c.ZK_MSBLQD,
                szk.c.ZK_SENHA,
                szk.c.ZK_SAL,
                sa3.c.A3_COD,
                sa3.c.A3_NOME,
                sa3.c.A3_CGC,
                sa3.c.A3_YTPREP,
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
            self.dados_usuario.usuario_bloqueado = dados_usuario.ZK_MSBLQL == "1"
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
        elif not self.senha_valida(senha_informada):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Não autenticado!",
            )
        else:
            self.usuario_autenticado = True
            self.autenticacao = self.gera_token()


@auth_router.post("/auth")
async def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> AuthResponse:
    resultado_autenticacao = AuthResponse()
    conta_usuario = form_data.username.lower()
    senha_informada = form_data.password

    auth_service = AuthService(db)
    auth_service.autentica_usuario(conta_usuario, senha_informada)
    if auth_service.usuario_autenticado:
        resultado_autenticacao.dados_autenticacao = auth_service.autenticacao
        resultado_autenticacao.dados_usuario = auth_service.dados_usuario

    return resultado_autenticacao.model_dump(exclude={"dados_usuario": {"acessos"}})


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
