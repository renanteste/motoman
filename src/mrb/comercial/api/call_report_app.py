from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.mrb.common.security.auth_service import valida_token
from src.mrb.comercial.api.auth_representante_app import autentica_representante_app
from src.mrb.comercial.models.model_call_reports import CallReports
from src.mrb.common.database.db_engine import get_db
from src.mrb.comercial.schemas.schema_call_report import CallReport
from typing import List, Union

call_report_router = APIRouter()


class CallReportApp:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cnpj_representante: str = None

    def inserir_call_reports(self, call_reports: List[CallReport]) -> List[CallReport]:
        novos_call_reports = [
            CallReports(
                **call_report.model_dump(exclude={"cnpj_representante"}),
                cnpj_representante=self.cnpj_representante
            )
            for call_report in call_reports
        ]
        self.db.add_all(novos_call_reports)
        self.db.flush()
        registros_gravados = [
            CallReport.model_validate(call_report) for call_report in novos_call_reports
        ]
        self.db.commit()
        return registros_gravados


@call_report_router.post("/call_report_app")
def novo_call_report(
    call_reports: Union[List[CallReport], CallReport],
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[CallReport]:
    """
    Insere novo registro de call report na tabela de integração com o ERP
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o representante:
    <p>O body pode conter um registro ou uma lista.
    """

    # Valida se tem acesso
    auth_service = autentica_representante_app(
        db, payload.get("sub"), "call_report_app"
    )

    call_report_app = CallReportApp(db)

    call_report_app.cnpj_representante = (
        auth_service.dados_usuario.dados_representante.cnpj
    )

    if not isinstance(call_reports, list):
        call_reports = [call_reports]

    return call_report_app.inserir_call_reports(call_reports)
