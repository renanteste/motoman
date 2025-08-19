import logging
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from src.mrb.common.lib.log_middleware import log_requests
from src.mrb.common.lib.handlers_excecoes import registrar_handlers_excecoes
from src.mrb.common.database.atualiza_tabelas import atualiza_tabelas
from src.mrb.common.lib import configura_log
from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.rh.api.solicitacao_horas_extras import solicitacao_horas_extras_router
from src.mrb.common.lib.recupera_parametro_sx6 import recupera_parametro_sx6_router
from src.mrb.common.routers_compartilhados import routers_compartilhados
from src.mrb.rh.api.extrato_horas_extras import extrato_horas_extras_router


async def life_span(app: FastAPI):
    try:
        atualiza_tabelas()

    except Exception as e:
        logging.error(f"Erro ao verificar ou criar tabelas: {e}")

    yield

    logging.info("Encerrando a aplicação...")


configura_log("api_rh")

app = FastAPI(
    lifespan=life_span,
    middleware=[Middleware(BaseHTTPMiddleware, dispatch=log_requests)],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)
registrar_handlers_excecoes(app)
app.mount("/images", StaticFiles(directory=Environment.IMAGES_PATH), name="images")
app.include_router(solicitacao_horas_extras_router)
app.include_router(recupera_parametro_sx6_router)
app.include_router(routers_compartilhados)
app.include_router(extrato_horas_extras_router)


# Execução do serviço REST RH
if __name__ == "__main__":
    # Inicia o serviço REST
    uvicorn.run(
        app,
        host=ApiConfiguration.rh.HOST,
        port=ApiConfiguration.rh.PORT,
        log_level="debug",
    )
