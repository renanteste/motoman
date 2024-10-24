from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.mrb.common.security.auth_service import AuthService
from src.mrb.common.database.db_engine import get_db
from src.mrb.comercial.models.model_vendedores import vendedores_sa3

# from src.mrb.common.email.email_service import EmailService


def autentica_representante_app(
    db: Session, id_usuario: str, ponto_acesso: str
) -> AuthService:
    # Valida se tem acesso
    auth_service = AuthService(db)
    if not auth_service.valida_acesso(id_usuario, ponto_acesso):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sem acesso ao endpoint!"
        )

    # Valida se é representante
    if not auth_service.dados_usuario.dados_representante:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não está cadastrado como representante!",
        )

    return auth_service


# class AutenticaRepresentanteApp:
#     def __init__(self, db: Session, cnpj: chr) -> None:
#         self.db = db
#         self.cnpj = cnpj
#         self.exception: str = None

#     def retorna_exception(self) -> str:
#         retorno_exception = self.exception
#         self.exception = None
#         return retorno_exception

#     # Valida se o token enviado como parâmetro existe no cadastro de representante
#     def valida_token(self, token: str) -> bool:
#         token_valido = False
#         if len(token) == 8:
#             sa3 = aliased(vendedores_sa3, name="sa3")
#             query = Select(sa3.c.A3_CGC).where(
#                 sa3.c.D_E_L_E_T_ == " ",
#                 sa3.c.A3_FILIAL == " ",
#                 sa3.c.A3_COD >= " ",
#                 sa3.c.A3_XTKNAPP == token,
#                 sa3.c.A3_MSBLQL != "1",
#             )
#             resultado = self.db.execute(query).fetchone()
#             if resultado:
#                 token_valido = True
#                 self.cnpj = resultado.A3_CGC
#         return token_valido

#     # Verifica se existe o cadastro do representante na base
#     def existe_representante(self) -> tuple[bool, str, str]:
#         sa3 = aliased(vendedores_sa3, name="sa3")
#         query = Select(sa3.c.A3_EMAIL, sa3.c.A3_XTKNAPP).where(
#             sa3.c.D_E_L_E_T_ == " ",
#             sa3.c.A3_FILIAL == " ",
#             sa3.c.A3_COD >= " ",
#             sa3.c.A3_YTPREP == "1",
#             sa3.c.A3_MSBLQL != "1",
#             sa3.c.A3_CGC == self.cnpj,
#         )
#         retorno = (False, "", "")
#         try:
#             resultado = self.db.execute(query).fetchone()
#             if resultado:
#                 retorno = (
#                     True,
#                     resultado.A3_EMAIL.strip(),
#                     resultado.A3_XTKNAPP.strip(),
#                 )
#             else:
#                 self.exception = "Representante não localizado"

#         except SQLAlchemyError as e:
#             self.exception = f"Erro na query: {e}"

#         return retorno

#     # Busca o token do representante pelo CNPJ, criando um caso não exista
#     def retorna_token(self) -> str:
#         novo_token = None
#         sa3 = aliased(vendedores_sa3, name="sa3")

#         try:
#             while not novo_token:
#                 novo_token = "".join(secrets.choice(string.digits) for _ in range(8))
#                 query = Select(sa3.c.A3_XTKNAPP).where(
#                     sa3.c.D_E_L_E_T_ == " ",
#                     sa3.c.A3_FILIAL == " ",
#                     sa3.c.A3_COD >= " ",
#                     sa3.c.A3_XTKNAPP == novo_token,
#                 )
#                 resultado = self.db.execute(query).fetchone()
#                 if resultado:
#                     novo_token = None
#         except SQLAlchemyError as e:
#             self.exception = f"Erro na query: {e}"
#             novo_token = None

#         if novo_token:
#             try:
#                 query = (
#                     update(vendedores_sa3)
#                     .where(
#                         vendedores_sa3.c.D_E_L_E_T_ == " ",
#                         vendedores_sa3.c.A3_FILIAL == " ",
#                         vendedores_sa3.c.A3_COD >= " ",
#                         vendedores_sa3.c.A3_CGC == self.cnpj,
#                     )
#                     .values(A3_XTKNAPP=novo_token)
#                 )
#                 self.db.execute(query)
#                 self.db.commit()
#             except SQLAlchemyError as e:
#                 self.exception = f"Erro no update: {e}"
#                 novo_token = None

#         return novo_token

#     def auth_representante(self) -> AuthRepresentante:
#         if len(self.cnpj) < 14:
#             raise HTTPException(status_code=400, detail="CNPJ Inválido")

#         representante_existe, email, token = (
#             self.existe_representante()
#         )  # Incluir o nome do representante

#         if not representante_existe:
#             raise HTTPException(status_code=400, detail=self.retorna_exception())

#         if not email:
#             raise HTTPException(
#                 status_code=400, detail="Representante sem e-mail cadastrado"
#             )

#         if not token:
#             token = self.retorna_token()
#             if not token:
#                 raise HTTPException(status_code=400, detail=self.retorna_exception())

#         body = f"""
#             <html>
#                 <body>
#                     <p>Seu token para ativar o aplicativo é {token}.</p>
#                 </body>
#             </html>
#             """
#         envio_email = EmailService()
#         if not envio_email.send_email(
#             to_address=email,
#             subject="Acesso aplicativo de representantes Motoman",
#             body=body,
#         ):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Falha no envio do e-mail com o token: {envio_email.mensagem}",
#             )

#         return AuthRepresentante(cnpj=self.cnpj, email=email)
