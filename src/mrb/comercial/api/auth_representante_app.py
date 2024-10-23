import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, aliased
from sqlalchemy import Select, update
from sqlalchemy.exc import SQLAlchemyError

from src.mrb.common.database.db_engine import get_db
from src.mrb.comercial.models.model_vendedores import vendedores_sa3
from src.mrb.common.email.email_service import EmailService
from src.mrb.comercial.schemas.schema_auth_representante import AuthRepresentante

# Cria o APIRouter para autenticação
auth_router = APIRouter()


class AutenticaRepresentanteApp:
    def __init__(self, db: Session, cnpj: chr) -> None:
        self.db = db
        self.cnpj = cnpj
        self.exception: str = None

    def retorna_exception(self) -> str:
        retorno_exception = self.exception
        self.exception = None
        return retorno_exception

    # Valida se o token enviado como parâmetro existe no cadastro de representante
    def valida_token(self, token: str) -> bool:
        token_valido = False
        if len(token) == 8:
            sa3 = aliased(vendedores_sa3, name="sa3")
            query = Select(sa3.c.A3_CGC).where(
                sa3.c.D_E_L_E_T_ == " ",
                sa3.c.A3_FILIAL == " ",
                sa3.c.A3_COD >= " ",
                sa3.c.A3_XTKNAPP == token,
                sa3.c.A3_MSBLQL != "1",
            )
            resultado = self.db.execute(query).fetchone()
            if resultado:
                token_valido = True
                self.cnpj = resultado.A3_CGC
        return token_valido

    # Verifica se existe o cadastro do representante na base
    def existe_representante(self) -> tuple[bool, str, str]:
        sa3 = aliased(vendedores_sa3, name="sa3")
        query = Select(sa3.c.A3_EMAIL, sa3.c.A3_XTKNAPP).where(
            sa3.c.D_E_L_E_T_ == " ",
            sa3.c.A3_FILIAL == " ",
            sa3.c.A3_COD >= " ",
            sa3.c.A3_YTPREP == "1",
            sa3.c.A3_MSBLQL != "1",
            sa3.c.A3_CGC == self.cnpj,
        )
        retorno = (False, "", "")
        try:
            resultado = self.db.execute(query).fetchone()
            if resultado:
                retorno = (
                    True,
                    resultado.A3_EMAIL.strip(),
                    resultado.A3_XTKNAPP.strip(),
                )
            else:
                self.exception = "Representante não localizado"

        except SQLAlchemyError as e:
            self.exception = f"Erro na query: {e}"

        return retorno

    # Busca o token do representante pelo CNPJ, criando um caso não exista
    def retorna_token(self) -> str:
        novo_token = None
        sa3 = aliased(vendedores_sa3, name="sa3")

        try:
            while not novo_token:
                novo_token = "".join(secrets.choice(string.digits) for _ in range(8))
                query = Select(sa3.c.A3_XTKNAPP).where(
                    sa3.c.D_E_L_E_T_ == " ",
                    sa3.c.A3_FILIAL == " ",
                    sa3.c.A3_COD >= " ",
                    sa3.c.A3_XTKNAPP == novo_token,
                )
                resultado = self.db.execute(query).fetchone()
                if resultado:
                    novo_token = None
        except SQLAlchemyError as e:
            self.exception = f"Erro na query: {e}"
            novo_token = None

        if novo_token:
            try:
                query = (
                    update(vendedores_sa3)
                    .where(
                        vendedores_sa3.c.D_E_L_E_T_ == " ",
                        vendedores_sa3.c.A3_FILIAL == " ",
                        vendedores_sa3.c.A3_COD >= " ",
                        vendedores_sa3.c.A3_CGC == self.cnpj,
                    )
                    .values(A3_XTKNAPP=novo_token)
                )
                self.db.execute(query)
                self.db.commit()
            except SQLAlchemyError as e:
                self.exception = f"Erro no update: {e}"
                novo_token = None

        return novo_token

    def auth_representante(self) -> AuthRepresentante:
        if len(self.cnpj) < 14:
            raise HTTPException(status_code=400, detail="CNPJ Inválido")

        representante_existe, email, token = (
            self.existe_representante()
        )  # Incluir o nome do representante

        if not representante_existe:
            raise HTTPException(status_code=400, detail=self.retorna_exception())

        if not email:
            raise HTTPException(
                status_code=400, detail="Representante sem e-mail cadastrado"
            )

        if not token:
            token = self.retorna_token()
            if not token:
                raise HTTPException(status_code=400, detail=self.retorna_exception())

        body = f"""
            <html>
                <body>
                    <p>Seu token para ativar o aplicativo é {token}.</p>
                </body>
            </html>
            """
        envio_email = EmailService()
        if not envio_email.send_email(
            to_address=email,
            subject="Acesso aplicativo de representantes Motoman",
            body=body,
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Falha no envio do e-mail com o token: {envio_email.mensagem}",
            )

        return AuthRepresentante(cnpj=self.cnpj, email=email)


@auth_router.put("/authrepresentante/{cnpj}", response_model=AuthRepresentante)
def auth_representante(cnpj: str, db: Session = Depends(get_db)) -> AuthRepresentante:
    # Receber cnpj + token para ativar o aplicativo
    # Em cada transação, validar o token + cnpj
    """
    Endpoint para autenticação do aplicativo do representante comercial.
    <p>Recebe na URL o número do CNPJ previamente cadastrado (Cadastro de Vendedores do ERP) e gera um token de 8 dígitos
    que servirá para autenticar as transações enviadas nos demais endpoints.
    <p>O token é enviado para o e-mail principal do cadastro do representante e deve ser digitado por ele no aplicativo
    para ativá-lo.
    <p>Se o cadastro do representante estiver bloqueado no ERP, o token não será validado.
    """
    autentica_representante_app = AutenticaRepresentanteApp(db, cnpj)
    return autentica_representante_app.auth_representante()
