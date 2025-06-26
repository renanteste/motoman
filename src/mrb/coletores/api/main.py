import base64
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List
from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import requests
import uvicorn

from src.mrb.common.security.auth_service import valida_token
from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.coletores.api.ordens_separacao import ordens_separacao_router

app = FastAPI()
app.include_router(ordens_separacao_router)
templates = Jinja2Templates(directory="src\\mrb\\coletores\\templates")


@app.get("/", include_in_schema=False)
def tela_login(request: Request):
    """
    Abertura do template login.html para interface de identificação do usuário
    """
    token = request.cookies.get("access_token")
    autenticado = False
    if token:
        try:
            valida_token(token)
            autenticado = True

        except:
            pass

    response = templates.TemplateResponse(
        "login.html", {"request": request, "ja_autenticado": autenticado}
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/ordens", include_in_schema=False)
def lista_ordens_separacao(request: Request):
    try:
        token = request.cookies.get("access_token")

        if not token:
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        response = requests.get(
            f"http://localhost:{ApiConfiguration.Coletores.PORT}/ordens_separacao",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Cliente-Token": Environment.CHAVE_COLETOR,
            },
        )

        if response.status_code == status.HTTP_200_OK:
            ordens = response.json()
            return templates.TemplateResponse(
                "ordens.html",
                {
                    "request": request,
                    "ordens": ordens["ordens_separacao"],
                    "usuario_nome": request.cookies.get("nome_usuario", ""),
                },
            )

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            return logout()

        else:
            return templates.TemplateResponse(
                "ordens.html",
                {
                    "request": request,
                    "erro": f"Erro recuperando a fila de separação: {response.status_code}",
                },
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {"request": request, "erro": f"Falha ao recuperar fila de separação: {e}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get("/inicia_separacao/{ordem_separacao}")
def inicia_separacao(request: Request, ordem_separacao: str):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    try:
        # Recupera o item da ordem de separação
        response = requests.post(
            url=f"http://localhost:{ApiConfiguration.Coletores.PORT}/separar/{ordem_separacao}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Cliente-Token": Environment.CHAVE_COLETOR,
            },
        )

        if response.status_code == status.HTTP_200_OK:
            itens: List[dict] = response.json()
            if not itens:
                return templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": f"Sem itens para a ordem {ordem_separacao}",
                    },
                )

            else:
                parametros = {
                    "request": request,
                    "ordem_separacao": ordem_separacao,
                    "item": itens[0]["item"],
                    "codigo_produto": itens[0]["codigo_produto"],
                    "posicao": itens[0]["posicao"],
                    "saldo_separar": itens[0]["saldo_separar"],
                    "almoxarifado": itens[0]["almoxarifado"],
                    "pedido": itens[0]["pedido"],
                    "sequencia_pedido": itens[0]["sequencia_pedido"],
                    "usuario_nome": request.cookies.get("nome_usuario", ""),
                }
                if itens[0].get("enderecos_alternativos"):
                    parametros["enderecos_alternativos"] = "|".join(
                        endereco.strip()
                        for endereco in itens[0].get("enderecos_alternativos", [])
                    )

                return templates.TemplateResponse(
                    "endereco.html",
                    parametros,
                )

        elif response.status_code == status.HTTP_409_CONFLICT:
            return templates.TemplateResponse(
                "ordens.html", {"request": request, "erro": response.json()["detail"]}
            )

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            return logout()

        else:
            return templates.TemplateResponse(
                "ordens.html",
                {
                    "request": request,
                    "erro": f"Falha ao iniciar separação: {response.status_code}",
                },
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {"request": request, "erro": f"Erro ao inicar separação: {e}"},
        )


@app.post("/logout", include_in_schema=False)
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response


@app.post("/login", include_in_schema=False)
async def processa_login(
    request: Request, usuario: str = Form(...), senha: str = Form(...)
):
    try:
        response_auth = requests.post(
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
            url=f"http://{ApiConfiguration.auth.URL}:{ApiConfiguration.auth.PORT}/auth",
            data={
                "username": usuario,
                "password": base64.b64encode(senha.encode()).decode(),
            },
        )

        if response_auth.status_code == status.HTTP_200_OK:
            token = response_auth.json()["dados_autenticacao"]["token"]
            payload = valida_token(token)
            response = RedirectResponse(
                url="/ordens", status_code=status.HTTP_302_FOUND
            )
            # Cria um cookie com o token e a mesma validade dele
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax",
                max_age=max(
                    0, int(payload.get("exp") - datetime.now(timezone.utc).timestamp())
                ),
            )
            # Cria um cookie com o nome do usuário logado
            response.set_cookie(
                key="nome_usuario",
                value=response_auth.json()["dados_usuario"]["nome_usuario"].title(),
                secure=request.url.scheme == "https",
                samesite="lax",
                max_age=max(
                    0, int(payload.get("exp") - datetime.now(timezone.utc).timestamp())
                ),
            )
            return response

        else:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "erro": response_auth.json()["detail"]},
                status_code=response_auth.status_code,
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "erro": "Erro ao conectar com o serviço de autenticação",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.post("/contagem", include_in_schema=False)
async def contagem(
    request: Request,
    ordem_separacao: str = Form(...),
    item: str = Form(...),
    codigo_produto: str = Form(...),
    posicao: str = Form(...),
    saldo_separar: str = Form(...),
    almoxarifado: str = Form(...),
    pedido: str = Form(...),
    sequencia_pedido: str = Form(...),
    endereco_coletado: str = Form(...),
):
    try:
        try:
            saldo_decimal = Decimal(saldo_separar)

        except InvalidOperation as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valor inválido para 'saldo_separar': {e}",
            )

        return templates.TemplateResponse(
            "contagem.html",
            {
                "request": request,
                "ordem_separacao": ordem_separacao,
                "item": item,
                "codigo_produto": codigo_produto,
                "posicao": posicao,
                "saldo_separar": saldo_decimal,
                "almoxarifado": almoxarifado,
                "pedido": pedido,
                "sequencia_pedido": sequencia_pedido,
                "endereco_coletado": endereco_coletado,
                "usuario_nome": request.cookies.get("nome_usuario", ""),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha montando contagem: {e}",
        )


@app.post("/pausar", include_in_schema=False)
async def pausar(request: Request, ordem_separacao: str = Form(...)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    try:
        response = requests.post(
            url=f"http://localhost:{ApiConfiguration.Coletores.PORT}/pausar_separacao/{ordem_separacao}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Cliente-Token": Environment.CHAVE_COLETOR,
            },
        )

        if response.status_code == status.HTTP_200_OK:
            return RedirectResponse(url="/ordens", status_code=status.HTTP_302_FOUND)

        elif response.status_code == status.HTTP_409_CONFLICT:
            return templates.TemplateResponse(
                "ordens.html", {"request": request, "erro": response.json()["detail"]}
            )

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            return logout()

        else:
            return templates.TemplateResponse(
                "ordens.html",
                {
                    "request": request,
                    "erro": f"Falha ao iniciar separação: {response.status_code}",
                },
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {"request": request, "erro": f"Erro ao pausar separação: {e}"},
        )


if __name__ == "__main__":
    argumentos_uvicorn = {
        "app": "main:app",
        "host": ApiConfiguration.Coletores.HOST,
        "port": ApiConfiguration.Coletores.PORT,
    }

    # Sobe o serviço como https apenas se o certificado digital estiver configurado no config.py
    if (
        ApiConfiguration.Coletores.Certificado.ARQUIVO_CERTIFICADO
        and ApiConfiguration.Coletores.Certificado.ARQUIVO_CHAVE_CERTIFICADO
    ):
        argumentos_uvicorn["ssl_certfile"] = (
            ApiConfiguration.Coletores.Certificado.ARQUIVO_CERTIFICADO
        )
        argumentos_uvicorn["ssl_keyfile"] = (
            ApiConfiguration.Coletores.Certificado.ARQUIVO_CHAVE_CERTIFICADO
        )

    uvicorn.run(**argumentos_uvicorn)
