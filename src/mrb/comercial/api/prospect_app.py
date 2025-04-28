from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, and_, asc, func, or_, union
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError
from src.mrb.common.lib.log_httpexception_raise import log_httpexception_raise
from src.mrb.common.security.auth_service import valida_token
from src.mrb.comercial.schemas.schema_prospect import (
    GetProspect,
    ListaProspects,
    Prospect,
)
from src.mrb.comercial.models.model_prospects import Prospects
from src.mrb.comercial.models.model_pedidos_venda import cabecalho_pedidos_venda_sc5
from src.mrb.comercial.models.model_clientes import clientes_sa1
from src.mrb.common.database.db_engine import get_db
from src.mrb.comercial.api.auth_representante_app import autentica_representante_app
from typing import List, Union

prospect_router = APIRouter()


class ProspectApp:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cnpj_representante: str = None
        self.codigo_representante: str = None

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

    def listar_prospects(self, pagina: int = 1, registros: int = 10) -> ListaProspects:
        try:
            sc5 = aliased(cabecalho_pedidos_venda_sc5, name="sc5")
            query_pedidos = (
                Select(
                    sc5.c.C5_CLIENTE.label("A1_COD"), sc5.c.C5_LOJACLI.label("A1_LOJA")
                )
                .where(
                    and_(
                        sc5.c.D_E_L_E_T_ == " ",
                        sc5.c.C5_FILIAL == "01",
                        sc5.c.C5_NUM >= " ",
                        or_(
                            sc5.c.C5_VEND1 == self.codigo_representante,
                            sc5.c.C5_VEND2 == self.codigo_representante,
                            sc5.c.C5_VEND3 == self.codigo_representante,
                            sc5.c.C5_VEND4 == self.codigo_representante,
                            sc5.c.C5_VEND5 == self.codigo_representante,
                        ),
                    )
                )
                .group_by(sc5.c.C5_CLIENTE, sc5.c.C5_LOJACLI)
            )
            sa1 = aliased(clientes_sa1, name="sa1")
            query_clientes = Select(sa1.c.A1_COD, sa1.c.A1_LOJA).where(
                sa1.c.D_E_L_E_T_ == " ",
                sa1.c.A1_FILIAL == " ",
                sa1.c.A1_COD >= " ",
                sa1.c.A1_LOJA >= "01",
                or_(
                    sa1.c.A1_VEND == self.codigo_representante,
                    sa1.c.A1_REP == self.codigo_representante,
                ),
            )

            # Obtém a contagem de registros
            query = Select(func.count()).select_from(
                union(query_pedidos, query_clientes).subquery()
            )
            retorno = {}
            retorno["total_de_registros"] = self.db.execute(query).scalar_one()

            # Busca os registros com controle de paginação
            clientes_union = union(query_pedidos, query_clientes).subquery("CLIENTES")

            query = (
                Select(
                    clientes_union.c.A1_COD,
                    clientes_union.c.A1_LOJA,
                    sa1.c.A1_CGC,
                    sa1.c.A1_NOME,
                    sa1.c.A1_CONTATO,
                    sa1.c.A1_XDEPART,
                    sa1.c.A1_CARGO1,
                    sa1.c.A1_END,
                    sa1.c.A1_BAIRRO,
                    sa1.c.A1_MUN,
                    sa1.c.A1_EST,
                    sa1.c.A1_CEP,
                    sa1.c.A1_COMPLEM,
                    sa1.c.A1_TEL,
                    sa1.c.A1_XRAMAL,
                    sa1.c.A1_XCELULA,
                    sa1.c.A1_DTCAD,
                    sa1.c.A1_XKPRAPP,
                    sa1.c.A1_YEMAIL,
                )
                .join(
                    sa1,
                    and_(
                        sa1.c.D_E_L_E_T_ == " ",
                        sa1.c.A1_FILIAL == " ",
                        sa1.c.A1_COD == clientes_union.c.A1_COD,
                        sa1.c.A1_LOJA == clientes_union.c.A1_LOJA,
                    ),
                )
                .order_by(asc(sa1.c.A1_NOME))
                .offset((pagina - 1) * registros)
                .limit(registros)
            )

            resultado = self.db.execute(query).fetchall()
            if resultado:
                retorno["pagina"] = pagina

            retorno["registros_por_pagina"] = registros
            retorno["total_de_paginas"] = (
                retorno["total_de_registros"] // registros
            ) + (
                1
                if not retorno["total_de_registros"] // registros
                == retorno["total_de_registros"] / registros
                else 0
            )
            retorno["prospects"] = []

            for registro in resultado:
                data_inclusao = datetime.strptime(
                    (
                        registro.A1_DTCAD
                        if len(registro.A1_DTCAD.strip()) == 8
                        else "20100101"
                    ),
                    "%Y%m%d",
                )
                retorno["prospects"].append(
                    GetProspect(
                        cnpj=registro.A1_CGC,
                        empresa=registro.A1_NOME.strip(),
                        contato=registro.A1_CONTATO.strip(),
                        departamento=registro.A1_XDEPART.strip(),
                        cargo=registro.A1_CARGO1.strip(),
                        endereco=registro.A1_END.strip(),
                        bairro=registro.A1_BAIRRO.strip(),
                        cidade=registro.A1_MUN.strip(),
                        estado=registro.A1_EST,
                        cep=registro.A1_CEP,
                        telefone=registro.A1_TEL.strip(),
                        celular=registro.A1_XCELULA,
                        data_inclusao=data_inclusao,
                        complemento=registro.A1_COMPLEM.strip(),
                        ramal=registro.A1_XRAMAL,
                        cnpj_representante=self.cnpj_representante,
                        chave_prospect=registro.A1_XKPRAPP,
                        email=registro.A1_YEMAIL.strip(),
                    )
                )

            return retorno

        except HTTPException:
            raise

        except SQLAlchemyError as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao buscar registros no banco de dados",
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


@prospect_router.get("/prospect_app")
def lista_prospects(
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
    pagina: Union[int, None] = 1,
    registros: Union[int, None] = 10,
) -> ListaProspects:
    """
    Lista os prospects de um representante.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o representante.
    """
    # Valida se tem acesso
    auth_service = autentica_representante_app(db, payload.get("sub"), "PROSPECT_APP")

    prospect_app = ProspectApp(db)

    prospect_app.cnpj_representante = (
        auth_service.dados_usuario.dados_representante.cnpj
    )
    prospect_app.codigo_representante = (
        auth_service.dados_usuario.dados_representante.codigo
    )

    return prospect_app.listar_prospects(pagina=pagina, registros=registros)
