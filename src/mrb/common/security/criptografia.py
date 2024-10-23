import os
from fastapi import APIRouter, HTTPException, status
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from src.mrb.common.config import Environment


criptografia_router = APIRouter()
descriptografia_router = APIRouter()


@descriptografia_router.post("/decript")
def decript(requisicao: dict):
    try:
        senha_criptografada_hexa = requisicao.get("senha")
        iv_hexa = requisicao.get("iv")

        senha_criptografada_bytes = bytes.fromhex(senha_criptografada_hexa)
        iv_bytes = bytes.fromhex(iv_hexa)

        cipher = AES.new(Environment.PORTAL_PY_K.encode(), AES.MODE_CBC, iv_bytes)

        senha_bytes = unpad(cipher.decrypt(senha_criptografada_bytes), AES.block_size)

        senha = senha_bytes.decode()

        return {"senha": senha}

    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"{e}")


@criptografia_router.post("/encript")
def encript(senha: dict):
    try:
        iv = os.urandom(16)
        senha_bytes = senha.get("senha").encode()
        cipher = AES.new(Environment.PORTAL_PY_K.encode(), AES.MODE_CBC, iv)
        senha_criptografada_bytes = cipher.encrypt(pad(senha_bytes, AES.block_size))
        senha_criptografada_hexa = senha_criptografada_bytes.hex()
        iv_hexa = iv.hex()
        return {"senha_criptografada": senha_criptografada_hexa, "iv": iv_hexa}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}"
        )
