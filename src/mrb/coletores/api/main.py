import base64
from decimal import InvalidOperation
from typing import List, Optional
from fastapi import FastAPI, Form, HTTPException, Path, Query, Request, status, Depends
from sqlalchemy.orm import Session
from src.mrb.common.database import get_db
from fastapi.middleware import Middleware
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import quote
import requests
import uvicorn

from src.mrb.common.lib.log_httpexception_raise import NivelLog, log_httpexception_raise
from src.mrb.common.lib.handlers_excecoes import registrar_handlers_excecoes
from src.mrb.common.lib.log_middleware import log_requests
from src.mrb.common.lib.configura_log import configura_log
from src.mrb.coletores.api.prepara_response import PreparaResponse
from src.mrb.common.lib.calcula_max_age import calcula_max_age
from src.mrb.common.security.auth_service import valida_token
from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.coletores.api.ordens_separacao import OrdensSeparacao

configura_log("coletores_frontend")

app = FastAPI(middleware=[Middleware(BaseHTTPMiddleware, dispatch=log_requests)])
registrar_handlers_excecoes(app)

templates = Jinja2Templates(directory="src\\mrb\\coletores\\templates")

LEGENDA_PRIORIDADE = [
    '<span style="color: red;">🔺🔺🔺🔺🔺</span>',
    '<span style="color: red;">🔺🔺🔺🔺</span>',
    '<span style="color: red;">🔺🔺🔺</span>',
    '<span style="color: red;">🔺🔺</span>',
    '<span style="color: red;">🔺</span>',
    '<span style="color: red;">🔻</span>',
    '<span style="color: red;">🔻🔻</span>',
    '<span style="color: red;">🔻🔻🔻</span>',
    '<span style="color: red;">🔻🔻🔻🔻</span>',
    '<span style="color: red;">🔻🔻🔻🔻🔻</span>',
]


def retorno_separacao(
    request: Request,
    retorno_separacao: dict,
    nome_usuario: str,
    endereco_coletado: str,
    ordem_separacao: str,
):
    """
    Monta o retorno para o próximo item após gravar uma separação com sucesso ou após pular um item
    """
    saldo_separar = quantidade_float(retorno_separacao["saldo_separar"])
    enderecos_alternativos = retorno_separacao.get("enderecos_alternativos") or []
    parametros = {
        "request": request,
        "ordem_separacao": ordem_separacao,
        "item": retorno_separacao["item"],
        "agrupador": retorno_separacao["agrupador"],
        "codigo_produto": retorno_separacao["codigo_produto"],
        "descricao_produto": retorno_separacao["descricao_produto"],
        "saldo_separar": saldo_separar,
        "almoxarifado": retorno_separacao["almoxarifado"],
        "pedido": retorno_separacao.get("pedido", ""),
        "sequencia_pedido": retorno_separacao.get("sequencia_pedido", ""),
        "usuario_nome": nome_usuario,
    }
    if retorno_separacao[
        "posicao"
    ] == endereco_coletado or endereco_coletado.strip() in [
        endereco.strip() for endereco in enderecos_alternativos
    ]:
        # Se a posicao do proximo item for igual a posição coletada anteriormente, ou se a posição coletada
        # anteriormente estiver entre os endereços alternativos do item atual, mandar contar o novo item
        parametros["endereco_coletado"] = endereco_coletado
        return_response = templates.TemplateResponse(
            "contagem.html",
            parametros,
        )

    else:
        # Caso contrário, se a posição for diferente, mandar o usuário bipar novo endereço
        parametros["posicao"] = retorno_separacao["posicao"]
        return_response = templates.TemplateResponse("endereco.html", parametros)

    return return_response


def quantidade_float(quantidade_string: str) -> float:
    """
    Converte a quantidade string para float, com tratamento de falha
    """
    try:
        quantidade_float = float(quantidade_string)

    except (InvalidOperation, ValueError) as e:
        log_httpexception_raise(
            status_code=status.HTTP_400_BAD_REQUEST,
            mensagem="Valor inválido para conversão float",
            exc_info=True,
            nivel_log=NivelLog.INFO,
            excecao=e,
        )

    return quantidade_float


@app.get("/", include_in_schema=False)
def tela_login(request: Request, mensagem: str = None):
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

    parametros_response = {"request": request, "ja_autenticado": autenticado}
    if mensagem:
        parametros_response["erro"] = mensagem

    response = templates.TemplateResponse("login.html", parametros_response)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/ordens/finalizada/{ordem_separacao}")
async def ordem_separacao_finalizada(request: Request, ordem_separacao: str):
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    return prepara_response.retorna_response(
        templates.TemplateResponse(
            "ordens.html",
            {
                "request": request,
                "erro": f"Ordem de separação {ordem_separacao} finalizada!",
                "usuario_nome": prepara_response.nome_usuario,
            },
            status_code=status.HTTP_302_FOUND,
        )
    )


@app.get("/ordens", include_in_schema=False)
async def lista_ordens_separacao(request: Request):
    """
    Endpoint GET que trata os dados para exibição da lista de ordens de separação na fila
    """
    try:
        prepara_response = PreparaResponse(request=request)
        if not prepara_response.valida_tokens():
            return await logout(mensagem="Token de acesso inválido / expirado!")

        # Faz a requisição da lista de ordens de separação ao endpoint do backend
        response = prepara_response.exec_request(
            url=f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/ordens_separacao",
            metodo="get",
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
        )

        if response.status_code == status.HTTP_200_OK:
            ordens = response.json()

            for ordem in ordens["ordens_separacao"]:
                # Faz a troca do conteúdo para a legenda de prioridade do card da fila
                ordem["legenda_prioridade"] = LEGENDA_PRIORIDADE[
                    int(ordem.get("prioridade", "0"))
                ]
                # Trata o conteúdo do campo origem da ordem de separação
                ordem["descricao_origem"] = (
                    "Compra Dedicada" if ordem["origem"] == "5" else "Estoque"
                )

            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "ordens": ordens["ordens_separacao"],
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            return await logout(
                mensagem=response.json().get("detail", "Não autorizado!")
            )

        else:
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": f"Erro recuperando a fila de separação: {response.status_code}",
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {
                "request": request,
                "erro": f"Falha ao recuperar fila de separação: {e}",
                "usuario_nome": prepara_response.nome_usuario,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get("/inicia_separacao/{ordem_separacao}", include_in_schema=False)
async def inicia_separacao(request: Request, ordem_separacao: str = Path(...)):
    """
    Endpoint invocado para iniciar a separação a partir da fila de separação
    """
    return await inicia_separacao_item(
        request=request, ordem_separacao=ordem_separacao, item=None
    )


@app.get("/inicia_separacao/{ordem_separacao}/{item}", include_in_schema=False)
async def inicia_separacao_item(
    request: Request, ordem_separacao: str = Path(...), item: str = Path(...)
):
    """
    Endpoint para recuperar os dados do item específico da ordem de separação.\n
    A função também pode ser chamada retornando o próximo item com saldo, sem ser item específico.
    """
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    try:
        # Recupera o item da ordem de separação
        url = f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/separar/{ordem_separacao}"
        if item:
            # Monta a url para retornar um item específico
            url += f"/{item}"

        response = prepara_response.exec_request(
            url=url,
            metodo="post",
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
        )

        if response.status_code == status.HTTP_200_OK:
            itens: List[dict] = response.json()
            if not itens:
                # Retorna mensagem quando não foram localizados itens
                return prepara_response.retorna_response(
                    templates.TemplateResponse(
                        "ordens.html",
                        {
                            "request": request,
                            "erro": f"Sem itens para a ordem {ordem_separacao}",
                            "usuario_nome": prepara_response.nome_usuario,
                        },
                    )
                )

            else:
                # Prepara os parâmetros para renderização da tela de leitura do endereço no almoxarifado
                parametros = {
                    "request": request,
                    "ordem_separacao": ordem_separacao,
                    "item": itens[0]["item"],
                    "agrupador": itens[0]["agrupador"],
                    "codigo_produto": itens[0]["codigo_produto"],
                    "descricao_produto": itens[0]["descricao_produto"],
                    "posicao": itens[0]["posicao"],
                    "saldo_separar": itens[0]["saldo_separar"],
                    "almoxarifado": itens[0]["almoxarifado"],
                    "pedido": itens[0]["pedido"],
                    "sequencia_pedido": itens[0]["sequencia_pedido"],
                    "usuario_nome": prepara_response.nome_usuario,
                    "origem": itens[0]["origem"],
                }
                if itens[0].get("enderecos_alternativos"):
                    parametros["enderecos_alternativos"] = "|".join(
                        endereco.strip()
                        for endereco in itens[0].get("enderecos_alternativos", [])
                    )

                return prepara_response.retorna_response(
                    templates.TemplateResponse("endereco.html", parametros)
                )

        elif response.status_code == status.HTTP_409_CONFLICT:
            # O retorno indica que a ordem de separação entrou para outro operador
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": response.json()["detail"],
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            # Endpoint no backend negou acesso
            return await logout(
                mensagem=response.json().get("detail", "Não autorizado!")
            )

        else:
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": f"Falha ao iniciar separação: {response.status_code} - {response.json()['detail']}",
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {
                "request": request,
                "erro": f"Erro ao inicar separação: {e}",
                "usuario_nome": prepara_response.nome_usuario,
            },
        )


@app.post("/logout", include_in_schema=False)
async def logout(mensagem: str = None):
    """
    Endpoint limpa os tokens de segurança dos cookies e retorna a interface para a tela principal
    """
    url = "/"
    if mensagem:
        url += f"?mensagem={quote(mensagem)}"

    response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@app.post("/login", include_in_schema=False)
async def processa_login(
    request: Request, usuario: str = Form(...), senha: str = Form(...)
):
    """
    Endpoint faz o processamento do login após a confirmação de usuário e senha na tela inicial
    """
    try:
        # Invoca o endpoint de autenticação
        response_auth = requests.post(
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
            url=f"http://{ApiConfiguration.auth.URL}:{ApiConfiguration.auth.PORT}/auth",
            data={
                "username": usuario,
                "password": base64.b64encode(senha.encode()).decode(),
            },
        )

        if response_auth.status_code == status.HTTP_200_OK:
            dados_autenticacao: dict = response_auth.json()["dados_autenticacao"]
            payload = valida_token(dados_autenticacao["token"])
            payload_refresh = valida_token(dados_autenticacao["refresh_token"])
            # Monta o redirecionamento para a fila de separação
            response = RedirectResponse(
                url="/ordens", status_code=status.HTTP_302_FOUND
            )
            # Cria um cookie com o token e a mesma validade dele
            response.set_cookie(
                key="access_token",
                value=dados_autenticacao["token"],
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax",
                max_age=calcula_max_age(payload.get("exp")),
            )
            # Cria um cookie com o nome do usuário logado
            response.set_cookie(
                key="nome_usuario",
                value=response_auth.json()["dados_usuario"]["nome_usuario"].title(),
                secure=request.url.scheme == "https",
                samesite="lax",
                max_age=calcula_max_age(payload.get("exp")),
            )
            # Cria um cookie com o refresh token
            response.set_cookie(
                key="refresh_token",
                value=dados_autenticacao["refresh_token"],
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax",
                max_age=calcula_max_age(payload_refresh.get("exp")),
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


@app.post("/grava_separacao", include_in_schema=False)
async def grava_separacao(
    request: Request,
    ordem_separacao: str = Form(...),
    item: str = Form(...),
    codigo_produto: str = Form(...),
    descricao_produto: str = Form(...),
    quantidade_separada: str = Form(...),
    almoxarifado: str = Form(...),
    pedido: str = Form(...),
    sequencia_pedido: str = Form(...),
    endereco_coletado: str = Form(...),
    agrupador: Optional[str] = Form(None),
):
    """
    Endpoint para receber os dados da separação registrados no frontend e invocar a gravação no backend.
    """
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    try:
        quantidade_separada_float = quantidade_float(quantidade_separada)

        # Registra a separação no endpoint registra_separacao
        response = prepara_response.exec_request(
            url=f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/registra_separacao",
            metodo="post",
            headers={
                "X-Cliente-Token": Environment.CHAVE_COLETOR,
                "Content-Type": "application/json",
            },
            dados={
                "ordem_separacao": ordem_separacao,
                "item": item,
                "agrupador": agrupador,
                "codigo_produto": codigo_produto,
                "descricao_produto": descricao_produto,
                "quantidade_separada": quantidade_separada_float,
                "almoxarifado": almoxarifado,
                "pedido": pedido,
                "sequencia_pedido": sequencia_pedido,
            },
        )

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            return await logout(
                mensagem=response.json().get("detail", "Não autorizado!")
            )

        elif response.status_code == status.HTTP_204_NO_CONTENT:
            # Ordem de separação gravada sem retornar novos itens, é ordem finalizada
            return prepara_response.retorna_response(
                RedirectResponse(
                    url=f"/ordens/finalizada/{ordem_separacao}",
                    status_code=status.HTTP_302_FOUND,
                )
            )

        elif not response.status_code == status.HTTP_200_OK:
            # No caso de erro, renderiza novamente a tela de contagem exibindo a mensagem retornada pelo backend
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "contagem.html",
                    {
                        "request": request,
                        "ordem_separacao": ordem_separacao,
                        "item": item,
                        "agrupador": agrupador,
                        "codigo_produto": codigo_produto,
                        "descricao_produto": descricao_produto,
                        "saldo_separar": quantidade_separada_float,
                        "almoxarifado": almoxarifado,
                        "pedido": pedido,
                        "sequencia_pedido": sequencia_pedido,
                        "endereco_coletado": endereco_coletado,
                        "usuario_nome": prepara_response.nome_usuario,
                        "erro": f"Não gravado: {response.status_code} - {response.json()['detail']}",
                    },
                )
            )

        # O retorno da separação gravada com sucesso é do próximo item
        return prepara_response.retorna_response(
            retorno_separacao(
                request=request,
                retorno_separacao=response.json(),
                nome_usuario=prepara_response.nome_usuario,
                endereco_coletado=endereco_coletado,
                ordem_separacao=ordem_separacao,
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha preparando para gravar separação: {e}",
        )


@app.post("/pular", include_in_schema=False)
async def pular_item(
    request: Request,
    ordem_separacao: str = Form(...),
    item: str = Form(...),
    codigo_produto: str = Form(...),
    quantidade_separada: str = Form(...),
    almoxarifado: str = Form(...),
    pedido: str = Form(...),
    sequencia_pedido: str = Form(...),
    endereco_coletado: str = Form(...),
    agrupador: Optional[str] = Form(None),
):
    """
    Endpoint acionado ao clicar no botão Pular na interface de registro da separação.
    """
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    try:
        # Aciona o endpoint pular_item e se retornar algum item, redireciona para a contagem
        response = prepara_response.exec_request(
            url=f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/pular_item/{ordem_separacao}/{item}",
            metodo="post",
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
        )

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            return await logout(
                mensagem=response.json().get("detail", "Não autorizado!")
            )

        elif response.status_code == status.HTTP_204_NO_CONTENT:
            # Ordem de separação gravada sem retornar novos itens, é que chegou ao final
            return prepara_response.retorna_response(
                RedirectResponse(url="/ordens", status_code=status.HTTP_302_FOUND)
            )

        elif not response.status_code == status.HTTP_200_OK:
            # Em caso de falha ao pular o item, retorna os dados anteriores
            quantidade_separada_float = quantidade_float(quantidade_separada)

            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "contagem.html",
                    {
                        "request": request,
                        "ordem_separacao": ordem_separacao,
                        "item": item,
                        "agrupador": agrupador,
                        "codigo_produto": codigo_produto,
                        "saldo_separar": quantidade_separada_float,
                        "almoxarifado": almoxarifado,
                        "pedido": pedido,
                        "sequencia_pedido": sequencia_pedido,
                        "endereco_coletado": endereco_coletado,
                        "usuario_nome": prepara_response.nome_usuario,
                        "erro": f"Falha ao pular {response.status_code} - {response.json()['detail']}",
                    },
                )
            )

        return prepara_response.retorna_response(
            retorno_separacao(
                request=request,
                retorno_separacao=response.json()[0],
                nome_usuario=prepara_response.nome_usuario,
                endereco_coletado=endereco_coletado,
                ordem_separacao=ordem_separacao,
            )
        )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {
                "request": request,
                "erro": f"Erro ao pular item: {e}",
                "usuario_nome": prepara_response.nome_usuario,
            },
        )


@app.get("/contagem_view", include_in_schema=False)
async def contagem_view(
    request: Request,
    ordem_separacao: str = Query(...),
    item: str = Query(...),
    codigo_produto: str = Query(...),
    descricao_produto: str = Query(...),
    saldo_separar: str = Query(...),
    almoxarifado: str = Query(...),
    pedido: str = Query(...),
    sequencia_pedido: str = Query(...),
    endereco_coletado: str = Query(...),
    agrupador: Optional[str] = Query(None),
):
    """
    Endpoint criado para acionar a renderização da tela de contagem pelo método GET.\n
    A chamada direta via POST provoca erro no navegador na atualização da tela pelo browser.
    """
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    try:
        saldo_float = quantidade_float(saldo_separar)

        return templates.TemplateResponse(
            "contagem.html",
            {
                "request": request,
                "ordem_separacao": ordem_separacao,
                "item": item,
                "agrupador": agrupador,
                "codigo_produto": codigo_produto,
                "descricao_produto": descricao_produto,
                "saldo_separar": saldo_float,
                "almoxarifado": almoxarifado,
                "pedido": pedido,
                "sequencia_pedido": sequencia_pedido,
                "endereco_coletado": endereco_coletado,
                "usuario_nome": prepara_response.nome_usuario,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha montando contagem: {e}",
        )


@app.post("/contagem", include_in_schema=False)
async def contagem(
    request: Request,
    ordem_separacao: str = Form(...),
    item: str = Form(...),
    codigo_produto: str = Form(...),
    descricao_produto: str = Form(...),
    saldo_separar: str = Form(...),
    almoxarifado: str = Form(...),
    pedido: str = Form(...),
    sequencia_pedido: str = Form(...),
    endereco_coletado: str = Form(...),
    agrupador: Optional[str] = Form(None),
):
    """
    Endpoint para receber os dados da contagem via POST do formulário de endereço.
    Após atualizar o item no backend, verifica se ainda existem itens pendentes.
    Se não houver, redireciona para a tela de itens com o botão "Encerrar".
    """
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    # ✅ Função de proteção local
    def safe_quote(valor):
        """Evita erro de quote_from_bytes() expected bytes"""
        if valor is None:
            return ""
        if isinstance(valor, (int, float)):
            valor = str(valor)
        if not isinstance(valor, str):
            valor = str(valor)
        return quote(valor)

    try:
        # 🔹 1. Atualiza contagem no backend
        url_backend = f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/atualiza_contagem"
        dados = {
            "ordem_separacao": ordem_separacao,
            "item": item,
            "saldo_separar": saldo_separar,
            "endereco": endereco_coletado,
            "usuario": prepara_response.nome_usuario,
        }

        response = requests.post(
            url_backend,
            json=dados,
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
        )

        # Se o backend retornar erro, dispara exceção
        if response.status_code not in (200, 204):
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erro ao atualizar contagem: {response.text}",
            )

        # 🔹 2. Verifica se ainda há itens pendentes
        url_check = f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/itens_pendentes/{ordem_separacao}"
        check = requests.get(url_check, headers={"X-Cliente-Token": Environment.CHAVE_COLETOR})

        if check.status_code != 200:
            raise HTTPException(
                status_code=check.status_code,
                detail=f"Erro ao verificar pendentes: {check.text}",
            )

        dados_check = check.json()
        pendentes = dados_check.get("pendentes", 0)

        # 🔹 3. Redirecionamento final
        if pendentes == 0:
            # ✅ Todos os itens foram separados → volta para tela de itens (mostra botão Encerrar)
            redirect_url = f"/itens_ordem_separacao_view?ordem_separacao={safe_quote(ordem_separacao)}"
        else:
            # 🔁 Ainda há itens pendentes → permanece no fluxo de contagem
            redirect_url = (
                f"/contagem_view"
                + f"?ordem_separacao={safe_quote(ordem_separacao)}"
                + f"&item={safe_quote(item)}"
                + f"&codigo_produto={safe_quote(codigo_produto)}"
                + f"&descricao_produto={safe_quote(descricao_produto)}"
                + f"&saldo_separar={safe_quote(saldo_separar)}"
                + f"&almoxarifado={safe_quote(almoxarifado)}"
                + f"&pedido={safe_quote(pedido)}"
                + f"&sequencia_pedido={safe_quote(sequencia_pedido)}"
                + f"&endereco_coletado={safe_quote(endereco_coletado)}"
                + f"&agrupador={safe_quote(agrupador)}"
            )

        return prepara_response.retorna_response(
            RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha redirecionando contagem: {e}",
        )



@app.post("/pausar", include_in_schema=False)
async def pausar(request: Request, ordem_separacao: str = Form(...)):
    """
    Endpoint para receber o comando do botão pausar acionado na interface.
    """
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    try:
        # Envia a instrução de pausar a separação ao backend
        response = prepara_response.exec_request(
            url=f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/pausar_separacao/{ordem_separacao}",
            metodo="post",
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
        )

        if response.status_code == status.HTTP_200_OK:
            # Retorna para a fila de separação no caso de sucesso
            return prepara_response.retorna_response(
                RedirectResponse(url="/ordens", status_code=status.HTTP_302_FOUND)
            )

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            # Backend não autorizou a transação
            return await logout(
                mensagem=response.json().get("detail", "Não autorizado!")
            )

        elif response.status_code == status.HTTP_409_CONFLICT:
            # A ordem de separação está direcionada a outro operador
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": response.json()["detail"],
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

        else:
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": f"Falha ao pausar a separação: {response.status_code} - {response.json()['detail']}",
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {
                "request": request,
                "erro": f"Erro ao pausar separação: {e}",
                "usuario_nome": prepara_response.nome_usuario,
            },
        )
@app.get("/itens_ordem_separacao/{ordem_separacao}", include_in_schema=False)
async def tela_itens_ordem_separacao(request: Request, ordem_separacao: str = Path(...)):
    """
    Endpoint para exibir todos os itens de uma ordem de separação em uma tela específica.
    """
    prepara_response = PreparaResponse(request=request)
    if not prepara_response.valida_tokens():
        return await logout(mensagem="Token de acesso inválido / expirado!")

    try:
        # Faz a requisição para o backend para obter todos os itens da ordem de separação
        response = prepara_response.exec_request(
            url=f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/itens_ordem_separacao/{ordem_separacao}",
            metodo="get",
            headers={"X-Cliente-Token": Environment.CHAVE_COLETOR},
        )

        if response.status_code == status.HTTP_200_OK:
            itens = response.json()
            # ⚙️ Obtém a origem da ordem (se vier nos itens)
            origem = itens[0].get("origem") if itens and "origem" in itens[0] else None
            
            # Processa os dados para a exibição na tela
            itens_processados = []
            itens_separados = 0
            itens_pendentes = 0
            
            for item in itens:
                try:
                    # Converte os campos numéricos para float de forma segura
                    saldo_separar = item.get("saldo_separar", "0")
                    quantidade_original = item.get("quantidade_original", "0")
                    
                    # Usa a função quantidade_float para conversão segura
                    saldo_separar_float = quantidade_float(saldo_separar)
                    quantidade_original_float = quantidade_float(quantidade_original)
                    
                    # Determina o status baseado no saldo
                    if saldo_separar_float == 0:
                        status_display = '<span style="color: green;">✓ Separado</span>'
                        itens_separados += 1
                    else:
                        status_display = '<span style="color: orange;">⏳ Pendente</span>'
                        itens_pendentes += 1
                    
                    # Cria uma cópia do item com os valores processados
                    item_processado = {
                        "item": item.get("item"),
                        "codigo_produto": item.get("codigo_produto"),
                        "descricao_produto": item.get("descricao_produto"),
                        "posicao": item.get("posicao"),
                        "quantidade_original": item.get("quantidade_original"),
                        "saldo_separar": item.get("saldo_separar"),
                        "quantidade_original_float": quantidade_original_float,
                        "saldo_separar_float": saldo_separar_float,
                        "status_display": status_display
                    }
                    
                    # Adiciona campos opcionais se existirem
                    if "agrupador" in item:
                        item_processado["agrupador"] = item.get("agrupador")
                    if "pedido" in item:
                        item_processado["pedido"] = item.get("pedido")
                    if "sequencia_pedido" in item:
                        item_processado["sequencia_pedido"] = item.get("sequencia_pedido")
                    if "almoxarifado" in item:
                        item_processado["almoxarifado"] = item.get("almoxarifado")
                    
                    itens_processados.append(item_processado)
                    
                except Exception as e:
                    # Log do erro e continua processando outros itens
                    print(f"Erro processando item {item.get('item', 'N/A')}: {e}")
                    continue

            total_itens = len(itens_processados)
            
            # Calcula o percentual
            percentual = round((itens_separados / total_itens * 100), 1) if total_itens > 0 else 0
            print(origem)
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "itens_ordem_separacao.html",
                    {
                        "request": request,
                        "itens": itens_processados,
                        "ordem_separacao": ordem_separacao,
                        "total_itens": total_itens,
                        "itens_pendentes": itens_pendentes,
                        "itens_separados": itens_separados,
                        "percentual": percentual, 
                        "usuario_nome": prepara_response.nome_usuario,
                        "origem": origem,  # ✅ adiciona aqui
                    },
                )
            )

        elif response.status_code == status.HTTP_404_NOT_FOUND:
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": f"Ordem de separação {ordem_separacao} não encontrada ou sem itens",
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            return await logout(
                mensagem=response.json().get("detail", "Não autorizado!")
            )

        else:
            return prepara_response.retorna_response(
                templates.TemplateResponse(
                    "ordens.html",
                    {
                        "request": request,
                        "erro": f"Erro ao carregar itens: {response.status_code} - {response.json().get('detail', 'Erro desconhecido')}",
                        "usuario_nome": prepara_response.nome_usuario,
                    },
                )
            )

    except requests.RequestException as e:
        return templates.TemplateResponse(
            "ordens.html",
            {
                "request": request,
                "erro": f"Falha ao conectar com o serviço: {e}",
                "usuario_nome": prepara_response.nome_usuario,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@app.post("/encerrar_separacao/{ordem_separacao}", include_in_schema=False)
async def encerrar_separacao(ordem_separacao: str):
    """
    Endpoint responsável por encerrar a separação da OS.
    Atualiza status no banco e prepara para impressão da etiqueta.
    """
    try:
        # Chama o backend para encerrar no banco (ou faz o update direto se o main tiver acesso ao DB)
        url = f"http://localhost:{ApiConfiguration.Coletores.PORT_BACKEND}/encerrar/{ordem_separacao}"
        response = requests.post(url, headers={"X-Cliente-Token": Environment.CHAVE_COLETOR})

        if response.status_code == 200:
            return Response(status_code=status.HTTP_200_OK)
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao encerrar separação: {e}")

@app.get("/itens_pendentes/{ordem_separacao}", include_in_schema=False)
def itens_pendentes(ordem_separacao: str, db: Session = Depends(get_db)):
    """
    Retorna a contagem de itens ainda pendentes de separação para a OS informada.
    """
    try:
        ordens = OrdensSeparacao(db=db)
        itens = ordens.obter_todos_itens_os(ordem_separacao)

        # Conta quantos ainda têm saldo a separar
        pendentes = sum(
            1 for item in itens
            if hasattr(item, "saldo_separar") and float(item.saldo_separar) > 0
        )

        return {"pendentes": pendentes}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao contar itens pendentes: {e}",
        )





if __name__ == "__main__":
    argumentos_uvicorn = {
        "app": "main:app",
        "host": ApiConfiguration.Coletores.HOST,
        "port": ApiConfiguration.Coletores.PORT,
        "workers": ApiConfiguration.Coletores.QUANTIDADE_WORKERS,
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

    def safe_quote(valor):
        """Garante que o valor é string antes de aplicar quote()."""
        if valor is None:
            return ""
        if isinstance(valor, (int, float)):
            valor = str(valor)
        if not isinstance(valor, str):
            valor = str(valor)
        return quote(valor)
