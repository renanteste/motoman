import jwt
import pytz
from datetime import datetime, timedelta

from src.mrb.common.config import Environment

# Tempo de expiração do token (minutos)
EXPIRACAO_MINUTOS = 5


def gera_token_downloads(id_requisicao: str, codigo_usuario: str) -> str:
    """
    Gera um token JWT contendo ID da requisição e código do usuário.
    """
    payload = {
        "id": id_requisicao,
        "codigo_usuario": codigo_usuario,
        "exp": datetime.now(pytz.UTC) + timedelta(minutes=EXPIRACAO_MINUTOS),
    }

    return jwt.encode(payload, Environment.PORTAL_PY_K, algorithm="HS256")


def decode_token_downloads(token: str, id_usuario: str) -> dict:
    """
    Decodifica o token de downloads de arquivos
    """
    try:
        payload = jwt.decode(token, Environment.PORTAL_PY_K, algorithms=["HS256"])

        if payload["codigo_usuario"] == id_usuario:
            return payload

        else:
            raise ValueError("Código de usuário inválido!")

    except jwt.ExpiredSignatureError as e:
        raise ValueError(f"Token expirado: {e}")

    except jwt.InvalidTokenError as e:
        raise ValueError(f"Token inválido: {e}")
