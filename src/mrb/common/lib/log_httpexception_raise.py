from enum import Enum
import logging
from typing import Literal, Optional

from fastapi import HTTPException


class NivelLog(Enum):
    ERROR = 1
    WARNING = 2
    INFO = 3


def log_httpexception_raise(
    status_code: int,
    mensagem: str,
    excecao: Optional[BaseException] = None,
    exc_info: bool = False,
    nivel_log: NivelLog = NivelLog.ERROR,
):
    """
    Função registra a exceção no log e faz o raise com HTTPException.
    """
    detail = mensagem
    if excecao:
        # Se enviado o objeto do exception, concatena ao detail para o HTTPException
        detail = f"{detail}: {excecao}"

    # A mensagem de log não inclui o exception pois tem o traceback
    if nivel_log == 1:
        logging.error(mensagem, exc_info=exc_info)

    elif nivel_log == 2:
        logging.warning(mensagem, exc_info=exc_info)

    elif nivel_log == 3:
        logging.info(mensagem, exc_info=exc_info)

    raise HTTPException(status_code=status_code, detail=detail)
