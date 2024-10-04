import base64
import hashlib
from src.mrb.common.config import SqlConfiguration


def retorna_chave() -> str:
    raw_key = (
        SqlConfiguration.DATABASE
        + SqlConfiguration.SERVER
        + SqlConfiguration.USER
        + SqlConfiguration.PASSWORD
    )
    chave = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode("utf-8")).digest())
    return chave.decode("utf-8")
