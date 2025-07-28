from fastapi import FastAPI
import uvicorn

from src.mrb.common.routers_compartilhados import routers_compartilhados
from src.mrb.common.config import ApiConfiguration
from src.mrb.coletores.api.ordens_separacao import ordens_separacao_router

app = FastAPI()
app.include_router(ordens_separacao_router)
app.include_router(routers_compartilhados)

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host=ApiConfiguration.Coletores.HOST_BACKEND,
        port=ApiConfiguration.Coletores.PORT_BACKEND,
    )
