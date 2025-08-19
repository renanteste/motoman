import logging
from fastapi.middleware import Middleware
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from starlette.middleware.base import BaseHTTPMiddleware

from src.mrb.common.lib.handlers_excecoes import registrar_handlers_excecoes
from src.mrb.common.lib.log_middleware import log_requests
from src.mrb.common.lib import configura_log
from src.mrb.common.config import ApiConfiguration
from src.mrb.comercial.api.prospect_app import prospect_router
from src.mrb.comercial.api.call_report_app import call_report_router
from src.mrb.common.routers_compartilhados import routers_compartilhados

configura_log("api_comercial")

app = FastAPI(middleware=[Middleware(BaseHTTPMiddleware, dispatch=log_requests)])
app.include_router(prospect_router)
app.include_router(call_report_router)
app.include_router(routers_compartilhados)


registrar_handlers_excecoes(app)

# Execução do serviço REST Comercial
if __name__ == "__main__":
    # Inicia o serviço REST Comercial
    uvicorn.run(
        app,
        host=ApiConfiguration.comercial.HOST,
        port=ApiConfiguration.comercial.PORT,
        log_level="debug",
    )
