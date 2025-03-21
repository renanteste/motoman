import base64
import os
import mimetypes
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from src.mrb.common.security.gera_token_downloads import decode_token_downloads


donwload_arquivos = APIRouter()


def apagar_arquivo(caminho_completo: str):
    try:
        os.remove(caminho_completo)

    except:
        pass


@donwload_arquivos.get("/download/{pasta_origem}")
def donwload_arquivo(
    pasta_origem: str,
    id_usuario: str = Query(
        ...,
        title="Id do usuário",
        description="Código do usuário proprietário do arquivo para download.",
        examples=["000001"],
    ),
    token_arquivo: str = Query(..., title="Token de acesso ao arquivo"),
    extencao_arquivo: str = Query(
        ..., title="Extensão do arquivo para donwload", examples=["pdf", "txt"]
    ),
):
    payload: dict = None

    try:
        payload = decode_token_downloads(token_arquivo, id_usuario)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"{e}")

    # Verifica se existe o arquivo na pasta
    nome_da_pasta = base64.urlsafe_b64decode(pasta_origem).decode()
    nome_arquivo = f"{payload['id']}.{extencao_arquivo}"
    caminho_completo = os.path.join(nome_da_pasta, nome_arquivo)

    if os.path.exists(caminho_completo):
        tipo_mime, _ = mimetypes.guess_type(caminho_completo)
        if not tipo_mime:
            tipo_mime = "application/octet-stream"

        return FileResponse(
            caminho_completo,
            media_type=tipo_mime,
            filename=nome_arquivo,
            background=BackgroundTask(apagar_arquivo, caminho_completo),
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não localizado!"
        )
