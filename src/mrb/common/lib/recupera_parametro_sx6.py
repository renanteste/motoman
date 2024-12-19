import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased

from src.mrb.common.lib.log_httpexception_raise import log_httpexception_raise
from src.mrb.common.models.model_parametro_sx6 import parametros_sx6
from src.mrb.common.schemas.schema_parametro_sx6 import ParametroSx6
from src.mrb.common.database.db_engine import get_db
from src.mrb.common.security.auth_service import valida_token


recupera_parametro_sx6_router = APIRouter()


class RecuperaParametroSx6:
    def __init__(self, db: Session):
        self.db = db

    def retorna_parametro_sx6(self, id: str):
        try:
            sx6 = aliased(parametros_sx6, name="sx6")
            query = Select(
                sx6.c.X6_TIPO,
                sx6.c.X6_DESCRIC,
                sx6.c.X6_DESC1,
                sx6.c.X6_DESC2,
                sx6.c.X6_CONTEUD,
            ).where(sx6.c.X6_FIL >= " ", sx6.c.X6_VAR == id)

            recupera_parametro = self.db.execute(query).fetchone()

            if recupera_parametro:
                descricao_parametro = (
                    recupera_parametro.X6_DESCRIC.rstrip()
                    + " "
                    + recupera_parametro.X6_DESC1
                    + " "
                    + recupera_parametro.X6_DESC2
                )
                retorno_parametro = ParametroSx6(
                    descricao_parametro=re.sub(r"\s{2,}", " ", descricao_parametro),
                    tipo_conteudo_parametro=recupera_parametro.X6_TIPO,
                    conteudo_parametro=(recupera_parametro.X6_CONTEUD.rstrip()),
                )

            else:
                log_httpexception_raise(
                    status_code=status.HTTP_404_NOT_FOUND,
                    mensagem=f"Parâmetro '{id}' não localizado!",
                    nivel_log=3,
                )

        except HTTPException:
            raise

        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao recuperar registros no banco de dados",
                exc_info=True,
                nivel_log=1,
                excecao=e,
            )

        except Exception as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro inesperado",
                exc_info=True,
                nivel_log=1,
                excecao=e,
            )

        return retorno_parametro


@recupera_parametro_sx6_router.get("/recupera_parametro_sx6/{id}")
def recupera_parametro_sx6(
    id: str, payload: dict = Depends(valida_token), db: Session = Depends(get_db)
) -> ParametroSx6:
    recupera_parametro_sx6 = RecuperaParametroSx6(db=db)
    return recupera_parametro_sx6.retorna_parametro_sx6(id)
