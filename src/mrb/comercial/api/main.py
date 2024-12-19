import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from src.mrb.common.lib import configura_log
from src.mrb.common.config import ApiConfiguration
from src.mrb.common.security.auth_service import auth_router
from src.mrb.comercial.api.prospect_app import prospect_router
from src.mrb.comercial.api.call_report_app import call_report_router
from src.mrb.common.routers_compartilhados import routers_compartilhados

configura_log("api_comercial")

app = FastAPI()
app.include_router(prospect_router)
app.include_router(call_report_router)
app.include_router(auth_router)
app.include_router(routers_compartilhados)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc}")
    return await request_validation_exception_handler(request, exc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Request: {request.method} {request.url}")
    logging.info(f"Headers: {request.headers}")

    body = await request.body()
    logging.info(f"Body: {body.decode('utf-8', errors='replace')}")

    response = await call_next(request)
    logging.info(f"Response status: {response.status_code}")
    return response


# Execução do serviço REST Comercial
if __name__ == "__main__":
    # Inicia o serviço REST Comercial
    uvicorn.run(
        app,
        host=ApiConfiguration.comercial.HOST,
        port=ApiConfiguration.comercial.PORT,
        log_level="debug",
    )
