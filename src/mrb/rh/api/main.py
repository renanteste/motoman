import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.mrb.common.lib import configura_log
from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.common.security.auth_service import auth_router
from src.mrb.rh.api.solicitacao_horas_extras import solicitacao_horas_extras_router
from src.mrb.common.lib.recupera_parametro_sx6 import recupera_parametro_sx6_router
from src.mrb.common.routers_compartilhados import routers_compartilhados

configura_log("api_rh")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)
app.mount("/images", StaticFiles(directory=Environment.IMAGES_PATH), name="images")
app.include_router(auth_router)
app.include_router(solicitacao_horas_extras_router)
app.include_router(recupera_parametro_sx6_router)
app.include_router(routers_compartilhados)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        # Não logar exceções HTTP tratadas
        return await request_validation_exception_handler(request, exc)

    # Loga informações da requisição
    logging.error(
        f"Unhandled exception: {exc}\n"
        f"Method: {request.method}\n"
        f"URL: {request.url}\n"
        f"Headers: {dict(request.headers)}",
        exc_info=True,
    )

    # Tenta capturar o corpo da requisição
    try:
        body = await request.body()
        logging.error(f"Body: {body.decode('utf-8', errors='replace')}")

    except Exception as body_error:
        logging.error(f"Failed to capture request body: {body_error}")

    # Retorna uma resposta amigável ao cliente
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno no servidor."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logging.warning(
        f"HTTPException: {exc.detail}\n"
        f"Status Code: {exc.status_code}\n"
        f"Method: {request.method}\n"
        f"URL: {request.url}\n"
        f"Headers: {dict(request.headers)}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc}")
    return await request_validation_exception_handler(request, exc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        logging.info(f"Request: {request.method} {request.url}")
        logging.info(f"Headers: {request.headers}")

        body = await request.body()
        body_decoded = body.decode("utf-8", errors="replace")

        if "password=" in body_decoded:
            body_decoded = body_decoded.replace(
                body_decoded.split("password=")[1].split("&")[0], "***"
            )

        logging.info(f"Body: {body_decoded}")

        response = await call_next(request)
        logging.info(f"Response status: {response.status_code}")
        return response

    except Exception as e:
        logging.error(f"Exception during request processing: {e}", exc_info=True)
        raise


# Execução do serviço REST RH
if __name__ == "__main__":
    # Inicia o serviço REST
    uvicorn.run(
        app,
        host=ApiConfiguration.rh.HOST,
        port=ApiConfiguration.rh.PORT,
        log_level="debug",
    )
