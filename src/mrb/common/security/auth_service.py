from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import Select
from sqlalchemy.orm import Session, aliased
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from src.mrb.common.database.db_engine import get_db
from src.mrb.common.models.model_usuarios_portal import usuarios_szk
from src.mrb.common.config import Environment

auth_router = APIRouter()


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.id_usuario: str
        self.nome_usuario: str
        self.usuario_bloqueado: bool
        self.validade_usuario: datetime
        self.senha_usuario: str
        self.sal_senha_usuario: str
        self.usuario_autenticado: bool

    def senha_valida(self, senha_digitada: str) -> bool:
        try:
            print(f"Primeira conversão: {self.sal_senha_usuario}")
            iv_bytes = self.sal_senha_usuario.encode("windows-1252")
            print(f"Segunda conversão: {self.senha_usuario}")
            senha_bytes = bytes(self.senha_usuario, "latin1")
            cipher = AES.new(Environment.PORTAL_PY_K, AES.MODE_CBC, iv_bytes)
            senha_descriptografada = unpad(cipher.decrypt(senha_bytes), AES.block_size)
            return senha_descriptografada.decode("windows-1252") == senha_digitada

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{e}",
            )

    def get_user(self, conta_usuario: str, senha_informada: str):
        szk = aliased(usuarios_szk, name="szk")
        query = Select(
            szk.c.ZK_ID,
            szk.c.ZK_NOME,
            szk.c.ZK_MSBLQL,
            szk.c.ZK_MSBLQD,
            szk.c.ZK_SENHA,
            szk.c.ZK_SAL,
        ).where(
            szk.c.D_E_L_E_T_ == " ",
            szk.c.ZK_FILIAL == " ",
            szk.c.ZK_EMAIL == conta_usuario,
        )
        dados_usuario = self.db.execute(query).fetchone()
        if dados_usuario:
            self.id_usuario = dados_usuario.ZK_ID
            self.nome_usuario = dados_usuario.ZK_NOME.strip()
            self.usuario_bloqueado = dados_usuario.ZK_MSBLQL == "1"
            if not dados_usuario.ZK_MSBLQD.strip() == "":
                self.validade_usuario = datetime.strptime(
                    dados_usuario.ZK_MSBLQD, "%Y%m%d"
                )
            else:
                self.validade_usuario = datetime.now()

            self.senha_usuario = dados_usuario.ZK_SENHA.strip()
            self.sal_senha_usuario = dados_usuario.ZK_SAL.strip()

            if self.validade_usuario < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Cadastro de usuário vencido!",
                )
            elif self.usuario_bloqueado:
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

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não existe!"
            )


@auth_router.post("/auth")
async def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    resultado_autenticacao = {}
    conta_usuario = form_data.username.lower()
    senha_informada = form_data.password

    auth_service = AuthService(db)
    auth_service.get_user(conta_usuario, senha_informada)
    if auth_service.usuario_autenticado:
        resultado_autenticacao = {"token": "Autenticado"}

    return resultado_autenticacao
