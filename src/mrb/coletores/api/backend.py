from fastapi import FastAPI
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from src.mrb.common.lib.handlers_excecoes import registrar_handlers_excecoes
from src.mrb.common.lib.log_middleware import log_requests
from src.mrb.common.lib.configura_log import configura_log
from src.mrb.common.routers_compartilhados import routers_compartilhados
from src.mrb.common.config import ApiConfiguration
from src.mrb.coletores.api.ordens_separacao import ordens_separacao_router

configura_log("coletores_backend")

app = FastAPI(middleware=[Middleware(BaseHTTPMiddleware, dispatch=log_requests)])
registrar_handlers_excecoes(app)
app.include_router(ordens_separacao_router)
app.include_router(routers_compartilhados)

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host=ApiConfiguration.Coletores.HOST_BACKEND,
        port=ApiConfiguration.Coletores.PORT_BACKEND,
    )
