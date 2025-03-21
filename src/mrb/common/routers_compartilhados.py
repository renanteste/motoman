from fastapi import APIRouter

from src.mrb.common.controle_downloads.donwload_arquivos import donwload_arquivos
from src.mrb.common.security.criptografia import (
    criptografia_router,
    descriptografia_router,
)
from src.mrb.common.security.opcoes_acesso import lista_opcoes_portal_router

routers_compartilhados = APIRouter()

routers_compartilhados.include_router(criptografia_router)
routers_compartilhados.include_router(descriptografia_router)
routers_compartilhados.include_router(lista_opcoes_portal_router)
routers_compartilhados.include_router(donwload_arquivos)
