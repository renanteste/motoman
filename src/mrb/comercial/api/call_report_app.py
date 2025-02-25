from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import INT, DateTime, Select, String, and_, func
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError
from src.mrb.common.lib.log_httpexception_raise import log_httpexception_raise
from src.mrb.comercial.models.model_clientes import clientes_sa1
from src.mrb.comercial.models.model_vendedores import vendedores_sa3
from src.mrb.comercial.models.model_call_reports_protheus import call_reports_z03
from src.mrb.common.security.auth_service import valida_token
from src.mrb.comercial.api.auth_representante_app import autentica_representante_app
from src.mrb.comercial.models.model_call_reports import CallReports
from src.mrb.common.database.db_engine import get_db
from src.mrb.comercial.schemas.schema_call_report import CallReport, ListagemCallReports
from typing import List, Union

call_report_router = APIRouter()


class CallReportApp:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cnpj_representante: str = None

    def inserir_call_reports(self, call_reports: List[CallReport]) -> List[CallReport]:
        try:
            novos_call_reports = [
                CallReports(
                    **call_report.model_dump(exclude={"cnpj_representante"}),
                    cnpj_representante=self.cnpj_representante,
                )
                for call_report in call_reports
            ]
            self.db.add_all(novos_call_reports)
            self.db.flush()
            registros_gravados = [
                CallReport.model_validate(call_report)
                for call_report in novos_call_reports
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

    def lista_call_reports(
        self, pagina: int = 1, registros: int = 10
    ) -> ListagemCallReports:
        try:
            listagem_call_reports = ListagemCallReports()
            z03 = aliased(call_reports_z03, name="z03")
            sa3 = aliased(vendedores_sa3, name="sa3")
            sa1 = aliased(clientes_sa1, name="sa1")
            query_base = (
                Select(
                    func.cast(z03.c.Z03_CODIGO, INT).label("id"),
                    sa3.c.A3_CGC.label("cnpj_representante"),
                    sa1.c.A1_CGC.label("cnpj_prospect"),
                    func.cast(z03.c.Z03_DATA, DateTime).label("data_visita"),
                    z03.c.Z03_CONTAT.label("pessoa_contato"),
                    z03.c.Z03_CARGO.label("cargo_pessoa_contato"),
                    z03.c.Z03_PROJET.label("projeto"),
                    z03.c.Z03_MOTIVO.label("motivo_visita"),
                    z03.c.Z03_PROCES.label("processos"),
                    z03.c.Z03_INTERA.label("interacoes_feedback"),
                    z03.c.Z03_ACOEST.label("acoes_tomadas"),
                    z03.c.Z03_PROXIM.label("proximos_passos"),
                    z03.c.Z03_OBSERV.label("observacoes"),
                    z03.c.Z03_TPOFER.label("tipo_de_oferta"),
                    z03.c.Z03_EXPECT.label("expectativa"),
                    z03.c.Z03_VALOR.label("valor"),
                    z03.c.Z03_STREET.label("street"),
                    z03.c.Z03_POSTAL.label("postal_code"),
                    z03.c.Z03_ADMARE.label("administrative_area"),
                    z03.c.Z03_SUBADM.label("sub_administrative_area"),
                    z03.c.Z03_SUBLOC.label("sub_locality"),
                    z03.c.Z03_SUBTHO.label("sub_thoroughfare"),
                    z03.c.Z03_TIPOVI.label("tipo_visita"),
                    z03.c.Z03_KAPLIC.label("chave_visita"),
                )
                .join(
                    sa3,
                    and_(
                        sa3.c.D_E_L_E_T_ == " ",
                        sa3.c.A3_FILIAL == " ",
                        sa3.c.A3_COD == z03.c.Z03_VENDED,
                        sa3.c.A3_CGC == self.cnpj_representante,
                    ),
                )
                .join(
                    sa1,
                    and_(
                        sa1.c.D_E_L_E_T_ == " ",
                        sa1.c.A1_FILIAL == " ",
                        sa1.c.A1_COD == z03.c.Z03_CLIENT,
                        sa1.c.A1_LOJA == z03.c.Z03_LOJA,
                    ),
                )
                .where(
                    and_(
                        z03.c.D_E_L_E_T_ == " ",
                        z03.c.Z03_FILIAL == " ",
                        z03.c.Z03_CODIGO >= " ",
                        z03.c.Z03_VENDED >= " ",
                    )
                )
            )
            query = Select(func.count()).select_from(query_base.subquery())
            listagem_call_reports.total_de_registros = self.db.execute(
                query
            ).scalar_one()
            listagem_call_reports.registros_por_pagina = registros
            listagem_call_reports.total_de_paginas = (
                listagem_call_reports.total_de_registros // registros
            ) + (
                1
                if not listagem_call_reports.total_de_registros // registros
                == listagem_call_reports.total_de_registros / registros
                else 0
            )
            query = (
                query_base.order_by(z03.c.Z03_DATA)
                .offset((pagina - 1) * registros)
                .limit(registros)
            )
            resultado = self.db.execute(query).fetchall()

            if resultado:
                listagem_call_reports.pagina = pagina
                listagem_call_reports.call_reports = [
                    CallReport.model_validate(
                        {
                            chave: (
                                valor.decode("windows-1252").strip("\x00").rstrip()
                                if isinstance(valor, bytes)
                                else valor.rstrip() if isinstance(valor, str) else valor
                            )
                            for chave, valor in linha._mapping.items()
                        }
                    )
                    for linha in resultado
                ]

            return listagem_call_reports

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


@call_report_router.get("/call_report_app")
def lista_call_report(
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
    pagina: int = Query(
        default=1, ge=1, description="Número da página (maior que zero)"
    ),
    registros: int = Query(
        default=10,
        ge=1,
        description="Quantidade de registros por página (maior que zero)",
    ),
) -> ListagemCallReports:
    """
    Lista as call reports de um representante.
    """
    # Valida se tem acesso
    auth_service = autentica_representante_app(
        db, payload.get("sub"), "call_report_app"
    )

    call_report_app = CallReportApp(db=db)

    call_report_app.cnpj_representante = (
        auth_service.dados_usuario.dados_representante.cnpj
    )
    listagem_call_reports = call_report_app.lista_call_reports(
        pagina=pagina, registros=registros
    )

    # Removendo os caracteres nulos ao final dos campos memo
    for call_report in listagem_call_reports.call_reports:
        for campo, valor in call_report.__dict__.items():
            if isinstance(valor, str) and "\x00" in valor:
                setattr(call_report, campo, valor.replace("\x00", "").strip())

    return listagem_call_reports


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
