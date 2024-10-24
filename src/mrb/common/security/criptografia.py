import os
from fastapi import APIRouter, HTTPException, status
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from pydantic import BaseModel

from src.mrb.common.config import Environment


criptografia_router = APIRouter()
descriptografia_router = APIRouter()


class DecriptRequisicao(BaseModel):
    senha: str
    iv: str


class EncriptRequisicao(BaseModel):
    senha: str


@descriptografia_router.post("/decript")
def decript(requisicao: DecriptRequisicao) -> EncriptRequisicao:
    try:
        cipher = AES.new(
            Environment.PORTAL_PY_K.encode(),
            AES.MODE_CBC,
            bytes.fromhex(requisicao.get("iv")),
        )

        return {
            "senha": unpad(
                cipher.decrypt(bytes.fromhex(requisicao.get("senha"))), AES.block_size
            ).decode()
        }

    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"{e}")


@criptografia_router.post("/encript")
def encript(senha: EncriptRequisicao) -> DecriptRequisicao:
    try:
        iv = os.urandom(16)
        cipher = AES.new(Environment.PORTAL_PY_K.encode(), AES.MODE_CBC, iv)
        return {
            "senha": cipher.encrypt(
                pad(senha.get("senha").encode(), AES.block_size)
            ).hex(),
            "iv": iv.hex(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}"
        )
