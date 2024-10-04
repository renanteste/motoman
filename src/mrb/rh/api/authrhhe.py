from fastapi import FastAPI, HTTPException
from src.mrb.rh.api.authkey import retorna_chave
from src.mrb.common.database.sql_connection import get_connection
from src.mrb.common.email.email_service import EmailService
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from src.mrb.common.config import Environment, ApiConfiguration
import os
import json

app = FastAPI()


def envia_email_acesso(email_destino: str, token: str, matricula: str) -> bool:
    token_link = f"http://{ApiConfiguration.rh.HOST}:{ApiConfiguration.rh.PORT}/acessorhhe/{token}/{matricula}"
    body = f"""
    <html>
        <body>
            <p>Para acessar o sistema, clique <a href="{token_link}">aqui</a>.</p>
        </body>
    </html>
    """
    envio_email = EmailService()
    envio_email.send_email(
        to_address=email_destino,
        subject="Acesso Sistema RH HE",
        body=body,
    )
    return envio_email.enviado


def generate_token(matricula: str) -> str:
    # Conecta no banco de dados e busca a matrícula
    conexao_sgbd = get_connection()
    if isinstance(conexao_sgbd, str):
        resultado = {"sucesso": False, "mensagem": conexao_sgbd}
    elif conexao_sgbd:
        sql = """
                SELECT
                    RA_NOME,
                    RA_EMAIL
                FROM
                    SRA010 SRA
                WHERE
                    SRA.D_E_L_E_T_ = ' '
                    AND RA_FILIAL = '01'
                    AND RA_MAT = %s
                """
        cursor = conexao_sgbd.cursor(as_dict=True)
        cursor.execute(sql, (matricula))
        dados_matricula = cursor.fetchone()
        if dados_matricula == None:
            resultado = {"sucesso": False, "mensagem": "Matrícula não localizada!"}
        elif len(dados_matricula["RA_EMAIL"].rstrip()) == 0:
            resultado = {
                "sucesso": False,
                "mensagem": f"E-mail não configurado para a matrícula {matricula}!",
            }
        else:
            criptografia = Fernet(retorna_chave())
            data_agora = datetime.now()
            # Token composto pela data e hora atual, validade, matrícula e endereço de e-mail
            token = (
                data_agora.strftime("%Y-%m-%d %H:%M:%S")
                + "|"
                + (data_agora + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
                + "|"
                + matricula
                + "|"
                + dados_matricula["RA_EMAIL"].rstrip()
            )
            token_criptografado = criptografia.encrypt(token.encode()).decode()

            resultado = {
                "sucesso": True,
                "mensagem": "",
                "matricula": matricula,
                "nome": dados_matricula["RA_NOME"].rstrip(),
                "email": dados_matricula["RA_EMAIL"].rstrip(),
                "token": token_criptografado,  # Remover depois o token, não pode retornar para o solicitante
            }

            cursor.close()

            if not os.path.exists(Environment.DIR_TOKENS):
                os.makedirs(Environment.DIR_TOKENS)
            with open(
                os.path.join(Environment.DIR_TOKENS, token_criptografado), "w"
            ) as arquivo:
                json.dump(resultado, arquivo)

            # Envia o email contendo o link com o token
            if not envia_email_acesso(
                resultado["email"], token_criptografado, matricula
            ):
                resultado["sucesso"] = False
                resultado["mensagem"] = "Falha no envio do e-mail com o token."
    return resultado


@app.get("/authrhhe/{matricula}")
def auth_rhhe(matricula: str):
    if len(matricula) < 4 or not matricula.isdigit():
        raise HTTPException(status_code=400, detail="Matrícula inválida!")

    resultado_token = generate_token(matricula)

    if not resultado_token["sucesso"]:
        raise HTTPException(status_code=400, detail=resultado_token["mensagem"])

    return resultado_token


@app.get("/acessorhhe/{token}/{matricula}")
def acesso_rhhe(token: str, matricula: str):
    arquivo_token = os.path.join(Environment.DIR_TOKENS, token)

    # Verifica se o arquivo do token existe
    if not os.path.exists(arquivo_token):
        raise HTTPException(status_code=400, detail="Token inexistente!")

    # Valida se o arquivo do token pode ser aberto em modo exclusivo
    try:
        with open(arquivo_token, "r+"):
            pass

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token em uso! {e}!")

    os.remove(arquivo_token)

    # Descriptografa o token e verifica a validade
    criptografia = Fernet(retorna_chave())
    token_descriptografado = (criptografia.decrypt(token.encode()).decode()).split("|")

    if len(token_descriptografado) != 4:
        raise HTTPException(status_code=400, detail="Token inválido!")

    try:
        validade = datetime.strptime(token_descriptografado[1], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Token sem data de validade!")

    if validade < datetime.now():
        raise HTTPException(status_code=400, detail="Token vencido!")

    return {"mensagem": "Acesso autorizado"}
