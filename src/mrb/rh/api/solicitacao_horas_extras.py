from datetime import date
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import (
    DATE,
    Select,
    and_,
    cast,
    delete,
    func,
    insert,
    inspect,
    or_,
    update,
)
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError

from src.mrb.rh.models.model_funcionarios_sra import funcionarios_sra
from src.mrb.rh.schemas.schema_liberacao_horas_extras import ListaLiberacaoHorasExtras
from src.mrb.common.lib.log_httpexception_raise import log_httpexception_raise
from src.mrb.common.database.db_engine import get_db
from src.mrb.common.security.auth_service import AuthService, valida_token
from src.mrb.rh.schemas.schema_solicitacao_horas_extras import (
    ListaSolicitacaoHorasExtras,
    SolicitacaoHorasExtras as SolicitacaoHE,
)
from src.mrb.rh.models.model_solicitacoes_horas_extras import SolicitacoesHorasExtras

solicitacao_horas_extras_router = APIRouter()


def valida_acesso_endpoint(db: Session, payload: dict) -> bool:
    auth_service = AuthService(db)
    return auth_service.valida_acesso(payload.get("sub"), "SOLICITA_HE")


def existe_matricula_datas(db: Session, solicitacoes_he: List[SolicitacaoHE]) -> bool:
    matricula = solicitacoes_he[0].matricula
    datas_planejadas = [
        and_(
            cast(SolicitacoesHorasExtras.data_planejada, DATE)
            == solicitacao_he.data_planejada.date(),
            SolicitacoesHorasExtras.id != solicitacao_he.id,
        )
        for solicitacao_he in solicitacoes_he
    ]
    query = Select(SolicitacoesHorasExtras.id).where(
        SolicitacoesHorasExtras.matricula == matricula, or_(*datas_planejadas)
    )
    resultado = db.execute(query).fetchone()
    return True if resultado else False


class SolitacaoHorasExtras:
    def __init__(self, db: Session) -> None:
        self.db = db

    def inserir(self, solicitacoes_he: List[SolicitacaoHE]) -> List[SolicitacaoHE]:
        try:
            for solicitacao_he in solicitacoes_he:
                if solicitacao_he.id != "0":
                    solicitacao_he.id = "0"

            if existe_matricula_datas(self.db, solicitacoes_he):
                log_httpexception_raise(
                    status_code=status.HTTP_409_CONFLICT,
                    mensagem=f"Registro já existe para a matrícula {solicitacoes_he[0].matricula} em alguma das datas apontadas.",
                    nivel_log=3,
                )

            novas_solicitacoes_he = [
                solicitacao_he.model_dump(exclude={"id"})
                for solicitacao_he in solicitacoes_he
            ]
            query = (
                insert(SolicitacoesHorasExtras)
                .returning(SolicitacoesHorasExtras)
                .values(novas_solicitacoes_he)
            )

            resultado = self.db.execute(query).fetchall()
            registros_gravados = []
            colunas = [
                column.name for column in inspect(SolicitacoesHorasExtras).columns
            ]
            for linha in resultado:
                registro = {coluna: getattr(linha[0], coluna) for coluna in colunas}
                registros_gravados.append(registro)

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

    def alterar(self, solicitacoes_he: List[SolicitacaoHE]) -> List[SolicitacaoHE]:
        try:
            # Verifica se existem os ids e recupera a data
            ids_selecao = [
                SolicitacoesHorasExtras.id == solicitacao_he.id
                for solicitacao_he in solicitacoes_he
            ]
            query = Select(
                SolicitacoesHorasExtras.id, SolicitacoesHorasExtras.data_planejada
            ).where(or_(*ids_selecao))
            ids_recuperados = self.db.execute(query).fetchall()

            ids_nao_localizados = {
                solicitacao_he.id for solicitacao_he in solicitacoes_he
            } - {row.id for row in ids_recuperados}

            if ids_nao_localizados:
                log_httpexception_raise(
                    status_code=status.HTTP_404_NOT_FOUND,
                    mensagem=f"IDs não localizados para atualização: {sorted(ids_nao_localizados)}",
                    nivel_log=3,
                )

            # Se está mudando a data, verifica se já não tem registro gravado na nova data
            datas_recuperadas = {
                row.id: row.data_planejada.date() for row in ids_recuperados
            }
            datas_alteradas = [
                solicitacao_he
                for solicitacao_he in solicitacoes_he
                if solicitacao_he.data_planejada.date()
                != datas_recuperadas.get(solicitacao_he.id)
            ]

            if datas_alteradas and existe_matricula_datas(self.db, datas_alteradas):
                log_httpexception_raise(
                    status_code=status.HTTP_409_CONFLICT,
                    mensagem=f"Datas alteradas inválidas, já existe para a matrícula {datas_alteradas[0].matricula}",
                    nivel_log=3,
                )

            # Executa a alteração
            for solicitacao_he in solicitacoes_he:
                valores_atualizacao = {
                    key: value
                    for key, value in solicitacao_he.model_dump().items()
                    if value is not None and key != "id"
                }
                query = (
                    update(SolicitacoesHorasExtras)
                    .returning(SolicitacoesHorasExtras)
                    .where(SolicitacoesHorasExtras.id == solicitacao_he.id)
                    .values(**valores_atualizacao)
                )
                resultado = self.db.execute(query)
                registros_gravados = []
                colunas = [
                    column.name for column in inspect(SolicitacoesHorasExtras).columns
                ]
                for linha in resultado:
                    registro = {coluna: getattr(linha[0], coluna) for coluna in colunas}
                    registros_gravados.append(registro)

            self.db.commit()

        except HTTPException:
            raise

        except SQLAlchemyError as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao atualizar registros no banco de dados",
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

    def excluir(self, id: int):
        try:
            # Verifica se o id existe e qual o status atual
            query = Select(SolicitacoesHorasExtras.status_aprovacao).where(
                SolicitacoesHorasExtras.id == id
            )
            retorno_solicitacao = self.db.execute(query).fetchone()
            if not retorno_solicitacao:
                log_httpexception_raise(
                    status_code=status.HTTP_404_NOT_FOUND,
                    mensagem=f"ID {id} não localizado!",
                    nivel_log=3,
                )

            # Se status for do tipo 4, não permite excluir
            elif retorno_solicitacao.status_aprovacao == "4":
                log_httpexception_raise(
                    status_code=status.HTTP_409_CONFLICT,
                    mensagem=f"ID {id} com status que não permite a exclusão!",
                    nivel_log=3,
                )

            query = delete(SolicitacoesHorasExtras).where(
                SolicitacoesHorasExtras.id == id
            )
            self.db.execute(query)
            self.db.commit()

        except HTTPException:
            raise

        except SQLAlchemyError as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao atualizar registros no banco de dados",
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

    def recupera_liberacoes(
        self,
        matricula_aprovador: str,
        pagina: int,
        registros: int,
        status_aprovacao: str,
        data_de: date,
        data_ate: date,
    ):
        try:
            sra = aliased(funcionarios_sra, name="sra")

            # Condição para seleção dos registros
            condicao = []
            condicao.append(sra.c.D_E_L_E_T_ == " ")
            condicao.append(sra.c.RA_FILIAL == "01")
            condicao.append(sra.c.RA_MAT >= " ")
            condicao.append(sra.c.RA_XLIDER == matricula_aprovador)
            condicao.append(sra.c.RA_DEMISSA == " ")

            if status_aprovacao:
                condicao.append(
                    SolicitacoesHorasExtras.status_aprovacao == status_aprovacao
                )

            if data_de:
                condicao.append(
                    cast(SolicitacoesHorasExtras.data_planejada, DATE) >= data_de
                )

            if data_ate:
                condicao.append(
                    cast(SolicitacoesHorasExtras.data_planejada, DATE) <= data_ate
                )

            # Recupera o total de registros de acordo com as condições de filtro
            query = (
                Select(func.count())
                .select_from(sra)
                .join(
                    SolicitacoesHorasExtras,
                    SolicitacoesHorasExtras.matricula == sra.c.RA_MAT,
                )
                .where(and_(*condicao))
            )

            retorno = {}
            retorno["total_de_registros"] = self.db.execute(query).scalar_one()

            # Recupera os registros conforme as condições com controle de paginação
            query = (
                Select(sra.c.RA_NOME.label("nome"), SolicitacoesHorasExtras)
                .join(
                    SolicitacoesHorasExtras,
                    SolicitacoesHorasExtras.matricula == sra.c.RA_MAT,
                )
                .where(and_(*condicao))
                .order_by(SolicitacoesHorasExtras.matricula, SolicitacoesHorasExtras.id)
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

            retorno["liberacoes_horas_extras"] = []
            colunas = [
                column.name for column in inspect(SolicitacoesHorasExtras).columns
            ]
            for linha in resultado:
                registro = {coluna: getattr(linha[1], coluna) for coluna in colunas}
                registro["nome"] = linha[0]
                retorno["liberacoes_horas_extras"].append(registro)

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

        return retorno

    def listar(
        self,
        matricula: str,
        pagina: int,
        registros: int,
        status_aprovacao: str,
        data_de: date,
        data_ate: date,
    ):
        try:
            # Determina os filtros dos registros
            condicao = []

            if matricula:
                condicao.append(SolicitacoesHorasExtras.matricula == matricula)

            if status_aprovacao:
                condicao.append(
                    SolicitacoesHorasExtras.status_aprovacao == status_aprovacao
                )

            if data_de:
                condicao.append(
                    cast(SolicitacoesHorasExtras.data_planejada, DATE) >= data_de
                )

            if data_ate:
                condicao.append(
                    cast(SolicitacoesHorasExtras.data_planejada, DATE) <= data_ate
                )

            # Retorna o total de registros conforme a condição de filtro
            query = Select(func.count()).select_from(SolicitacoesHorasExtras)
            if condicao:
                query = query.where(and_(*condicao))

            retorno = {}
            retorno["total_de_registros"] = self.db.execute(query).scalar_one()

            # Seleciona os registros paginados
            query = (
                Select(SolicitacoesHorasExtras)
                .order_by(SolicitacoesHorasExtras.id)
                .offset((pagina - 1) * registros)
                .limit(registros)
            )
            if condicao:
                query = query.where(and_(*condicao))

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

            retorno["solicitacoes_horas_extras"] = []
            colunas = [
                column.name for column in inspect(SolicitacoesHorasExtras).columns
            ]
            for linha in resultado:
                registro = {coluna: getattr(linha[0], coluna) for coluna in colunas}
                retorno["solicitacoes_horas_extras"].append(registro)

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

        return retorno

    def recupera_solicitacao(self, id: int):
        try:
            query = Select(SolicitacoesHorasExtras).where(
                SolicitacoesHorasExtras.id == id
            )
            resultado = self.db.execute(query).fetchone()
            if not resultado:
                log_httpexception_raise(
                    status_code=status.HTTP_404_NOT_FOUND,
                    mensagem=f"ID {id} não localizado!",
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

        return resultado[0]


@solicitacao_horas_extras_router.put("/solicitacao_horas_extras")
def altera_solicitacao_horas_extras(
    solicitacoes_he: Union[List[SolicitacaoHE], SolicitacaoHE],
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[SolicitacaoHE]:
    """
    Altera solicitações de Banco de Horas.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o usuário.
    <p>O body pode conter um registro ou uma lista.

    """
    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sem acesso ao endpoint 'SOLICITA_HE'!",
        )

    if not isinstance(solicitacoes_he, list):
        solicitacoes_he = [solicitacoes_he]

    # Instancia a classe para alterar os registros
    solicitacao_horas_extras = SolitacaoHorasExtras(db)
    return solicitacao_horas_extras.alterar(solicitacoes_he)


@solicitacao_horas_extras_router.post("/solicitacao_horas_extras")
def nova_solicitacao_horas_extras(
    solicitacoes_he: Union[List[SolicitacaoHE], SolicitacaoHE],
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[SolicitacaoHE]:
    """
    Insere nova solicitação de Banco de Horas.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o usuário.
    <p>O body pode conter um registro ou uma lista.

    """
    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sem acesso ao endpoint 'SOLICITA_HE'!",
        )

    if not isinstance(solicitacoes_he, list):
        solicitacoes_he = [solicitacoes_he]

    # Instancia a classe para inserir os registros
    solicitacao_horas_extras = SolitacaoHorasExtras(db=db)

    return solicitacao_horas_extras.inserir(solicitacoes_he)


@solicitacao_horas_extras_router.delete(
    "/solicitacao_horas_extras/{id}", status_code=status.HTTP_204_NO_CONTENT
)
def apaga_solicitacao_horas_extras(
    id: int, payload: dict = Depends(valida_token), db: Session = Depends(get_db)
):
    """
    Exclui solicitação de Banco de Horas enviada na URL.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o usuário.

    """
    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sem acesso ao endpoint 'SOLICITA_HE'!",
        )

    # Instancia a classe para excluir os registros
    solicitacao_horas_extras = SolitacaoHorasExtras(db)
    solicitacao_horas_extras.excluir(id)


@solicitacao_horas_extras_router.get("/liberacao_horas_extras")
def lista_liberacao_horas_extras(
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
    matricula_aprovador: Union[str, None] = None,
    pagina: Union[int, None] = 1,
    registros: Union[int, None] = 10,
    status_aprovacao: Union[str, None] = None,
    data_de: Union[date, None] = None,
    data_ate: Union[date, None] = None,
) -> ListaLiberacaoHorasExtras:
    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sem acesso ao endpoint 'SOLICITA_HE'!",
        )
    # Instancia a classe para retornar os dados
    solicitacao_horas_extras = SolitacaoHorasExtras(db)
    return solicitacao_horas_extras.recupera_liberacoes(
        matricula_aprovador, pagina, registros, status_aprovacao, data_de, data_ate
    )


@solicitacao_horas_extras_router.get("/solicitacao_horas_extras")
def lista_solicitacoes_horas_extras(
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
    matricula: Union[str, None] = None,
    pagina: Union[int, None] = 1,
    registros: Union[int, None] = 10,
    status_aprovacao: Union[str, None] = None,
    data_de: Union[date, None] = None,
    data_ate: Union[date, None] = None,
) -> ListaSolicitacaoHorasExtras:
    """
    Retorna lista de solicitações de Banco de Horas.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o usuário.
    <p>Aceita receber via querystrings os parâmetros:
    <p><b>matricula</b>: código da matrícula para seleção dos registros
    <p><b>pagina</b>: número da página dos dados
    <p><b>registros</b>: quantidade de registros por página
    <p><b>status_aprovacao</b>: código do estatus de aprovação para seleção dos registros

    """
    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sem acesso ao endpoint 'SOLICITA_HE'!",
        )

    # Instancia a classe para retornar os registros
    solicitacao_horas_extras = SolitacaoHorasExtras(db)
    return solicitacao_horas_extras.listar(
        matricula, pagina, registros, status_aprovacao, data_de, data_ate
    )


@solicitacao_horas_extras_router.get("/solicitacao_horas_extras/{id}")
def recupera_solicitacao_hora_extra(
    id: int, payload: dict = Depends(valida_token), db: Session = Depends(get_db)
) -> SolicitacaoHE:
    """
    Retorna solicitação de Banco de Horas enviada na URL.
    <p>Espera receber no header o token de autenticação em base 64 que irá identificar o usuário.

    """
    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sem acesso ao endpoint 'SOLICITA_HE'!",
        )

    # Instancia a classe para retornar os dados
    solicitacao_horas_extras = SolitacaoHorasExtras(db)
    return solicitacao_horas_extras.recupera_solicitacao(id)
