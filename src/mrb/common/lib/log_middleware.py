import logging
from fastapi import Request, Response

IGNORAR_PATHS_LOG = {
    "/.well-known/appspecific/com.chrome.devtools.json",
    "/favicon.ico",
}

PALAVRAS_SENSIVEIS = ["password=", "senha="]


async def log_requests(request: Request, call_next):
    try:
        if request.url.path in IGNORAR_PATHS_LOG:
            return await call_next(request)

        logging.info(f"Request: {request.method} {request.url}")
        logging.info(f"Headers: {request.headers}")

        body = await request.body()
        body_decoded = body.decode("utf-8", errors="replace")

        for palavra in PALAVRAS_SENSIVEIS:
            if palavra in body_decoded:
                body_decoded = body_decoded.replace(
                    body_decoded.split(palavra)[1].split("&")[0], "***"
                )

        if body_decoded and not body_decoded == "":
            logging.info(f"Body: {body_decoded}")

        response: Response = await call_next(request)
        logging.info(f"Response status: {response.status_code}")
        return response

    except Exception as e:
        logging.error(f"Exception during request processing: {e}", exc_info=True)
        raise
