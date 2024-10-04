import base64
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from src.mrb.comercial.schemas.schema_prospect import Prospect
from src.mrb.comercial.models.model_prospects import Prospects
from src.mrb.common.database.db_engine import get_db
from src.mrb.comercial.api.auth_representante_app import AutenticaRepresentanteApp
from typing import List, Union

prospect_router = APIRouter()


class ProspectApp:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cnpj_representante: str = None

    def inserir_prospects(self, prospects: List[Prospect]) -> List[Prospect]:
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
        return registros_gravados


@prospect_router.post("/prospect_app/")
def novo_prospect(
    prospects: Union[List[Prospect], Prospect],
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> List[Prospect]:
    """
    Insere novo prospect na tabela de prospects para integração com o ERP.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o representante:
    <p>O body pode conter um registro ou uma lista.

    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Autorização inválida no cabeçalho!"
        )

    prospect_app = ProspectApp(db)
    autentica_representante = AutenticaRepresentanteApp(db, None)
    if not autentica_representante.valida_token(
        base64.b64decode(authorization.replace("Bearer ", "")).decode()
    ):
        raise HTTPException(status_code=401, detail="Token inválido!")

    prospect_app.cnpj_representante = autentica_representante.cnpj

    if not isinstance(prospects, list):
        prospects = [prospects]

    return prospect_app.inserir_prospects(prospects)
