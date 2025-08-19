import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc}")
    return await request_validation_exception_handler(request, exc)


def registrar_handlers_excecoes(app: FastAPI):
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
