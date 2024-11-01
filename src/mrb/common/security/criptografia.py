import os
from fastapi import APIRouter, HTTPException, status
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from pydantic import BaseModel
from typing import Dict

from src.mrb.common.config import Environment

criptografia_router = APIRouter()
descriptografia_router = APIRouter()


# Definindo os modelos de entrada e saída das requisições
class DecriptRequisicao(BaseModel):
    senha: str
    iv: str


class EncriptRequisicao(BaseModel):
    senha: str


class DecriptResposta(BaseModel):
    senha: str


class EncriptResposta(BaseModel):
    senha: str
    iv: str


# Função de descriptografia
@descriptografia_router.post("/decript", response_model=DecriptResposta)
def decript(requisicao: DecriptRequisicao) -> DecriptResposta:
    try:
        chave = Environment.PORTAL_PY_K.encode()

        if len(chave) not in [16, 24, 32]:
            raise ValueError("Chave AES deve ter 16, 24 ou 32 bytes.")
        cipher = AES.new(chave, AES.MODE_CBC, bytes.fromhex(requisicao.iv))

        senha_descriptografada = unpad(
            cipher.decrypt(bytes.fromhex(requisicao.senha)), AES.block_size
        ).decode()

        return DecriptResposta(senha=senha_descriptografada)

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chave ou iv iválidos na descriptografia: {ve}",
        )

    except UnicodeDecodeError as ude:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chave ou iv iválidos na decodificação da senha: {ude}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Função de criptografia
@criptografia_router.post("/encript", response_model=EncriptResposta)
def encript(requisicao: EncriptRequisicao) -> EncriptResposta:
    try:
        chave = Environment.PORTAL_PY_K.encode()

        if len(chave) not in [16, 24, 32]:
            raise ValueError("Chave AES deve ter 16, 24 ou 32 bytes.")

        iv = os.urandom(16)
        cipher = AES.new(chave, AES.MODE_CBC, iv)

        senha_criptografada = cipher.encrypt(
            pad(requisicao.senha.encode(), AES.block_size)
        ).hex()

        return EncriptResposta(senha=senha_criptografada, iv=iv.hex())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
