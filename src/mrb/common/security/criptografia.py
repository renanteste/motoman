import os
from fastapi import APIRouter, HTTPException, status
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from pydantic import BaseModel, Field
from typing import Dict

from src.mrb.common.config import Environment

criptografia_router = APIRouter()
descriptografia_router = APIRouter()


# Definindo os modelos de entrada e saída das requisições
class DecriptRequisicao(BaseModel):
    """Modelo de requisição para descriptografia"""

    senha: str = Field(
        ..., description="String contendo a senha criptografada em formato hexadecimal"
    )
    iv: str = Field(
        ...,
        description="Vetor de inicialização (IV) em formato hexadecimal, necessário para descriptografia.",
    )


class EncriptRequisicao(BaseModel):
    """Modelo de requisição para criptografia"""

    senha: str = Field(..., description="String contendo a senha a ser criptografada.")


class DecriptResposta(BaseModel):
    """Modelo de resposta para descriptografia"""

    senha: str = Field(..., description="String contendo a senha descriptografada.")


class EncriptResposta(BaseModel):
    """Modelo de resposta para criptografia"""

    senha: str = Field(
        ..., description="String contendo a senha criptografada em formato hexadecimal."
    )
    iv: str = Field(
        ..., description="Vetor de inicialização (IV) em formato hexadecimal."
    )


# Função de descriptografia
@descriptografia_router.post("/decript", response_model=DecriptResposta)
def decript(requisicao: DecriptRequisicao) -> DecriptResposta:
    """
    Realiza a descriptografia de uma senha criptografada usando o algoritmo AES em modo CBC.

    Parâmetros:
        requisicao (DecriptRequisicao):
            Objeto contendo os dados necessários para a descriptografia:
            - senha (str): A senha criptografada, em formato hexadecimal.
            - iv (str): O vetor de inicialização (IV) utilizado na criptografia, também em formato hexadecimal.

    Retorno:
        DecriptResposta:
            Objeto contendo a senha original (descriptografada):
            - senha (str): A senha descriptografada.

    Exceções:
        HTTPException:
            - HTTP 400: Quando a chave ou o IV são inválidos.
            - HTTP 500: Quando ocorre qualquer erro inesperado durante o processo de descriptografia.

    Detalhes:
        1. A chave AES utilizada para descriptografia é obtida da variável de ambiente `PORTAL_PY_K`.
        2. O algoritmo verifica se a chave tem comprimento válido (16, 24 ou 32 bytes).
        3. O vetor de inicialização (IV) é convertido de hexadecimal para bytes antes de ser usado.
        4. A senha criptografada é convertida de hexadecimal para bytes, e o resultado da descriptografia é removido de qualquer padding extra.
    """
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
    """
    Realiza a criptografia de uma senha usando o algoritmo AES em modo CBC.

    Parâmetros:
        requisicao (EncriptRequisicao):
            Objeto contendo os dados necessários para a criptografia:
            - senha (str): A senha que será criptografada.

    Retorno:
        EncriptResposta:
            Objeto contendo os dados da senha criptografada:
            - senha (str): A senha criptografada, em formato hexadecimal.
            - iv (str): O vetor de inicialização (IV) gerado aleatoriamente, em formato hexadecimal.

    Exceções:
        HTTPException:
            - HTTP 400: Quando a chave é inválida.
            - HTTP 500: Quando ocorre qualquer erro inesperado durante o processo de criptografia.

    Detalhes:
        1. A chave AES utilizada para criptografia é obtida da variável de ambiente `PORTAL_PY_K`.
        2. O algoritmo verifica se a chave tem comprimento válido (16, 24 ou 32 bytes).
        3. Um vetor de inicialização (IV) é gerado aleatoriamente.
        4. A senha é criptografada usando AES no modo CBC com padding.
    """

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
