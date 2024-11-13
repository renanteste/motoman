import logging
from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.mrb.common.lib import configura_log
from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.common.security.auth_service import auth_router

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


# Execução do serviço REST RH
if __name__ == "__main__":
    # Inicia o serviço REST
    uvicorn.run(
        app,
        host=ApiConfiguration.rh.HOST,
        port=ApiConfiguration.rh.PORT,
        log_level="debug",
    )
