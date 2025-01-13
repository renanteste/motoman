from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.mrb.common.lib.log_httpexception_raise import log_httpexception_raise
from src.mrb.common.security.auth_service import valida_token
from src.mrb.comercial.schemas.schema_prospect import Prospect
from src.mrb.comercial.models.model_prospects import Prospects
from src.mrb.common.database.db_engine import get_db
from src.mrb.comercial.api.auth_representante_app import autentica_representante_app
from typing import List, Union

prospect_router = APIRouter()


class ProspectApp:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cnpj_representante: str = None

    def inserir_prospects(self, prospects: List[Prospect]) -> List[Prospect]:
        try:
            novos_prospects = [
                Prospects(
                    **prospect.model_dump(exclude={"cnpj_representante"}),
                    cnpj_representante=self.cnpj_representante,
                )
                for prospect in prospects
            ]
            self.db.add_all(novos_prospects)
            self.db.flush()
            registros_gravados = [
                Prospect.model_validate(prospect) for prospect in novos_prospects
            ]
            self.db.commit()

        except HTTPException:
            raise

        except SQLAlchemyError as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao inserir registros no banco de dados",
                exc_info=True,
                nivel_log=1,
                excecao=e,
            )

        except Exception as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro inesperado",
                exc_info=True,
                nivel_log=1,
                excecao=e,
            )

        return registros_gravados


@prospect_router.post("/prospect_app")
def novo_prospect(
    prospects: Union[List[Prospect], Prospect],
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[Prospect]:
    """
    Insere novo prospect na tabela de prospects para integração com o ERP.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o representante:
    <p>O body pode conter um registro ou uma lista.

    """
    # Valida se tem acesso
    auth_service = autentica_representante_app(db, payload.get("sub"), "PROSPECT_APP")

    # Instanciamento da classe para inserir prospects
    prospect_app = ProspectApp(db)

    prospect_app.cnpj_representante = (
        auth_service.dados_usuario.dados_representante.cnpj
    )

    if not isinstance(prospects, list):
        prospects = [prospects]

    return prospect_app.inserir_prospects(prospects)
