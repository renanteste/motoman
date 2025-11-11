from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Header, Path, Response, status
from sqlalchemy import (
    Integer,
    Numeric,
    Select,
    String,
    Tuple,
    and_,
    case,
    cast,
    func,
    insert,
    literal,
    literal_column,
    select,
    union_all,
    update,
)
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError

from src.mrb.common.lib.log_httpexception_raise import NivelLog, log_httpexception_raise
from src.mrb.common.lib.prepara_dados_protheus import prepara_dados_protheus
import logging
from src.mrb.common.config import Environment
from src.mrb.coletores.schemas.schema_ordem_separacao import (
    ItemOrdemSeparacao,
    ListaOrdensSeparacao,
    OrdemSeparacao,
    RegistraSeparacao,
)
from src.mrb.common.security.auth_service import AuthService, valida_token
from src.mrb.common.database.db_engine import get_db
from src.mrb.common.models.model_recursos_protheus import recursos_ae8
from src.mrb.common.models.model_usuarios_portal import usuarios_szk
from src.mrb.coletores.models.model_operadores_cb1 import operadores_cb1
from src.mrb.coletores.models.model_ordens_separacao import ordens_separacao_cb7
from src.mrb.coletores.models.model_pedidos_vendas import pedidos_vendas_sc6
from src.mrb.coletores.models.model_posicoes_almoxarifado import posicoes_z0o
from src.mrb.coletores.models.model_itens_ordem_separacao import (
    itens_ordem_separacao_cb8,
)
from src.mrb.coletores.models.model_registro_separacao import registro_separacao_cb9
from src.mrb.comercial.models.model_clientes import clientes_sa1
from src.mrb.common.models.model_produtos_sb1 import produtos_sb1
from src.mrb.common.models.model_insumos_projeto_afa import insumos_projetos_afa

ordens_separacao_router = APIRouter()

OPERADOR_PADRAO = "000000"


class OrdensSeparacao:
    """
    Classe para gravação e recuperação de dados do processo de separação de materiais.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.codigo_operador: str = None

    def lista_ordens_separacao(self, usuario_operador: str):
        """
        Recupera a lista de ordens de separação determinadas para o operador do parâmetro ou do operador padrão '000000'.
        """
        cb7 = aliased(ordens_separacao_cb7, name="cb7")
        sa1 = aliased(clientes_sa1, name="sa1")

        # Seleciona o código do operador com base no id do usuário
        query_usuario = self.query_usuario(usuario_operador)

        # Acrescenta o código de operador da fila de separação, onde todos podem atender
        # e monta a CTE para o WITH na seleção das ordens de separação
        query_operador = union_all(
            query_usuario, select(literal(OPERADOR_PADRAO).label("CB1_CODOPE"))
        ).cte("operadores")

        # Seleciona as ordens de separação vinculadas ao operador e na fila de separação.
        # Ordena por prioridade, operador (decrescente) e ordem de separação,
        # fazendo com que as mais prioritárias venham no início da fila, seguidas pelas
        # que foram determinadas ao operador e em seguida, pelas mais antigas (numeração)
        query = (
            select(
                cb7.c.CB7_ORDSEP.label("ordem_separacao"),
                cb7.c.CB7_PEDIDO.label("pedido_vendas"),
                sa1.c.A1_NOME.label("nome_cliente"),
                cb7.c.CB7_XPROJE.label("projeto"),
                cb7.c.CB7_XPROD.label("celula"),
                cb7.c.CB7_XCONTE.label("conteiner"),
                cb7.c.CB7_DIVERG.label("divergencia"),
                cb7.c.CB7_STATPA.label("em_pausa"),
                cb7.c.CB7_STATUS.label("status"),
                cb7.c.CB7_XTPENT.label("tipo_entrega"),
                cb7.c.CB7_NOTA.label("nota_fiscal"),
                cb7.c.CB7_XQTDIM.label("quantidade_impressoes"),
                cb7.c.CB7_PRIORI.label("prioridade"),
                cb7.c.CB7_ORIGEM.label("origem"),
            )
            .select_from(
                cb7.join(
                    query_operador, query_operador.c.CB1_CODOPE == cb7.c.CB7_CODOPE
                ).outerjoin(
                    sa1,
                    and_(
                        sa1.c.D_E_L_E_T_ == " ",
                        sa1.c.A1_FILIAL == " ",
                        sa1.c.A1_COD == cb7.c.CB7_CLIENT,
                        sa1.c.A1_LOJA == cb7.c.CB7_LOJA,
                    ),
                )
            )
            .where(
                and_(
                    cb7.c.D_E_L_E_T_ == " ",
                    cb7.c.CB7_FILIAL == "01",
                    cb7.c.CB7_ORDSEP >= " ",
                    cb7.c.CB7_CODOPE != " ",
                    cb7.c.CB7_STATUS.between("0", "8"),
                )
            )
        ).order_by(cb7.c.CB7_PRIORI, cb7.c.CB7_CODOPE.desc(), cb7.c.CB7_ORDSEP)

        try:
            resultado = self.db.execute(query).mappings().all()
            ordens_separacao = []
            for row in resultado:
                dados = {
                    chave: valor.strip() if isinstance(valor, str) else valor
                    for chave, valor in row.items()
                }
                dados["label"] = self.situacao_ordem_separacao(dados_separacao=dados)
                ordens_separacao.append(OrdemSeparacao.model_validate(dados))

            return ListaOrdensSeparacao(
                total_de_registros=len(ordens_separacao),
                ordens_separacao=ordens_separacao,
            )

        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao selecionar as ordens de separação para o operador",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

    def situacao_ordem_separacao(self, dados_separacao: dict) -> str:
        """
        Método aplica conjunto específico de regras para retornar a situação 'legenda' da ordem de separação
        de acordo com os dados recuperados do sistema.
        """
        regras_legendas = [
            (lambda dados: dados.get("divergencia") == "1", "1:Divergência"),
            (lambda dados: dados.get("em_pausa") == "1", "2:Em pausa"),
            (
                lambda dados: dados.get("status") == "9"
                and dados.get("tipo_entrega").strip() == ""
                and dados.get("nota_fiscal").strip() == "",
                "3:Finalizada",
            ),
            (
                lambda dados: dados.get("status") >= "1" and dados.get("status") <= "8",
                "4:Em andamento",
            ),
            (
                lambda dados: dados.get("status") == "0"
                and dados.get("quantidade_impressoes") > 0,
                "5:Impressa",
            ),
            (lambda dados: dados.get("status") == "0", "6:Não iniciada"),
            (
                lambda dados: dados.get("status") == "9"
                and dados.get("tipo_entrega") == "4",
                "7:Encerrada - contêiner não entregue",
            ),
            (
                lambda dados: dados.get("status") == "9"
                and (
                    not dados.get("tipo_entrega").strip() == ""
                    or not dados.get("nota_fiscal").strip() == ""
                ),
                "8:Encerrada - entregue",
            ),
        ]
        for condicao, legenda in regras_legendas:
            if condicao(dados_separacao):
                return legenda

        return "0:Indefinida"

    def query_usuario(self, usuario_operador: str) -> Select[Tuple]:
        """
        Montagem da query para seleção do usuário operador.
        """
        cb1 = aliased(operadores_cb1, name="cb1")
        szk = aliased(usuarios_szk, name="szk")
        ae8 = aliased(recursos_ae8, name="ae8")
        return (
            select(cb1.c.CB1_CODOPE)
            .select_from(
                szk.join(
                    ae8,
                    and_(
                        ae8.c.D_E_L_E_T_ == " ",
                        ae8.c.AE8_FILIAL == "01",
                        ae8.c.AE8_RECURS == szk.c.ZK_CDRECUR,
                    ),
                ).join(
                    cb1,
                    and_(
                        cb1.c.D_E_L_E_T_ == " ",
                        cb1.c.CB1_FILIAL == "01",
                        cb1.c.CB1_CODUSR == ae8.c.AE8_USER,
                    ),
                )
            )
            .where(
                and_(
                    szk.c.D_E_L_E_T_ == " ",
                    szk.c.ZK_FILIAL == " ",
                    szk.c.ZK_ID == usuario_operador,
                )
            )
        )

    def recupera_operador_usuario(self, usuario_operador: str) -> str:
        """
        Recupera o código de operador através do código do usuário do portal
        """
        try:
            codigo_operador = self.db.execute(
                self.query_usuario(usuario_operador)
            ).scalar()
            codigo_operador = codigo_operador if codigo_operador else OPERADOR_PADRAO

        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao buscar código do operador",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        return codigo_operador

    def atualiza_operador(self, ordem_separacao: str, usuario_operador: str):
        """
        Atualiza o código do operador na ordem de separação.
        """
        self.codigo_operador = self.recupera_operador_usuario(usuario_operador)

        cb7 = aliased(ordens_separacao_cb7, name="cb7")
        # Localiza e bloqueia a ordem de separação indicada
        query = (
            select(cb7.c.CB7_CODOPE)
            .with_hint(cb7, "WITH (ROWLOCK, XLOCK, HOLDLOCK)", dialect_name="mssql")
            .where(
                cb7.c.D_E_L_E_T_ == " ",
                cb7.c.CB7_FILIAL == "01",
                cb7.c.CB7_ORDSEP == ordem_separacao,
            )
        )

        try:
            # Recupera o código do operador da ordem de separação bloqueando o registro
            operador_atual: str = self.db.execute(query).scalar()

        except SQLAlchemyError as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Falha ao recuperar código do operador na Ordem de Separação",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        operador_atual = (
            operador_atual
            if operador_atual and (operador_atual.strip())
            else OPERADOR_PADRAO
        )

        # Valida que não está para outro operador
        # Não é fila de separação e é de outro operador
        if (
            not operador_atual == OPERADOR_PADRAO
            and not operador_atual == self.codigo_operador
        ):
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_409_CONFLICT,
                mensagem=f"A ordem de separação foi capturada pelo operador {operador_atual}",
                nivel_log=NivelLog.WARNING,
            )

        # Se for fila de separação ou do próprio operador atualiza o operador e inicializa a separação
        if operador_atual == OPERADOR_PADRAO or operador_atual == self.codigo_operador:
            query = (
                update(ordens_separacao_cb7)
                .where(
                    ordens_separacao_cb7.c.D_E_L_E_T_ == " ",
                    ordens_separacao_cb7.c.CB7_FILIAL == "01",
                    ordens_separacao_cb7.c.CB7_ORDSEP == ordem_separacao,
                )
                .values(CB7_CODOPE=self.codigo_operador, CB7_STATUS="1", CB7_STATPA="0")
            )
            try:
                self.db.execute(query)
                self.db.commit()

            except SQLAlchemyError as e:
                self.db.rollback()
                log_httpexception_raise(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    mensagem="Falha ao atualizar operador na Ordem de Separação",
                    exc_info=True,
                    nivel_log=NivelLog.ERROR,
                    excecao=e,
                )

            # Pausa as demais ordens de separação que estiverem em andamento para o operador
            query = (
                update(ordens_separacao_cb7)
                .where(
                    ordens_separacao_cb7.c.D_E_L_E_T_ == " ",
                    ordens_separacao_cb7.c.CB7_FILIAL == "01",
                    ordens_separacao_cb7.c.CB7_ORDSEP != ordem_separacao,
                    ordens_separacao_cb7.c.CB7_CODOPE == self.codigo_operador,
                    ordens_separacao_cb7.c.CB7_STATUS >= "1",
                    ordens_separacao_cb7.c.CB7_STATUS <= "8",
                    ordens_separacao_cb7.c.CB7_DIVERG != "1",
                    ordens_separacao_cb7.c.CB7_STATPA != "1",
                )
                .values(CB7_STATPA="1")
            )
            try:
                self.db.execute(query)
                self.db.commit()

            except SQLAlchemyError as e:
                self.db.rollback()
                log_httpexception_raise(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    mensagem="Falha ao pausar separações do operador",
                    exc_info=True,
                    nivel_log=NivelLog.ERROR,
                    excecao=e,
                )

        self.db.rollback()

    def recupera_itens(
        self, ordem_separacao: str, item_anterior: str = " ", item: str = None
    ) -> List[ItemOrdemSeparacao]:
        """
        Recupera os itens da ordem de separação.\n
        Se o argumento 'item' for informado, será retornado apenas o item.\n
        Caso 'item_anterior' seja informado, irá retornar o próximo item na ordem POSICAO + ITEM.
        """

        def recupera_posicao_item() -> str:
            query_item = (
                select(
                    func.min(
                        func.coalesce(
                            z0o.c.Z0O_POSICA,
                            cast(cast(cb8.c.CB8_LOCAL, Integer), String)
                            + literal_column("'-ALMOX'"),
                        )
                    ).label("posicao")
                )
                .select_from(
                    cb8.outerjoin(
                        z0o,
                        and_(
                            z0o.c.D_E_L_E_T_ == " ",
                            z0o.c.Z0O_FILIAL == "01",
                            z0o.c.Z0O_COD == cb8.c.CB8_PROD,
                            z0o.c.Z0O_LOCAL == cb8.c.CB8_LOCAL,
                        ),
                    )
                )
                .where(
                    and_(
                        cb8.c.D_E_L_E_T_ == " ",
                        cb8.c.CB8_FILIAL == "01",
                        cb8.c.CB8_ORDSEP == ordem_separacao,
                        cb8.c.CB8_ITEM == item_anterior,
                    )
                )
            )

            try:
                posicao_item = self.db.execute(query_item).scalar()

                return posicao_item + item_anterior if posicao_item else " "

            except SQLAlchemyError as e:
                log_httpexception_raise(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    mensagem="Falha ao recuperar posição do item da separação",
                    exc_info=True,
                    nivel_log=NivelLog.ERROR,
                    excecao=e,
                )

        item_anterior = item_anterior if item_anterior else " "
        itens_ordem_separacao: List[ItemOrdemSeparacao] = []
        cb8 = aliased(itens_ordem_separacao_cb8, name="cb8")
        cb7 = aliased(ordens_separacao_cb7, name="cb7")
        z0o = aliased(posicoes_z0o, name="z0o")
        sb1 = aliased(produtos_sb1, name="sb1")
        afa = aliased(insumos_projetos_afa, name="afa")
        if not item_anterior.strip() == "":
            item_posicao = recupera_posicao_item()

        else:
            item_posicao = " "

        condicao = [
            cb8.c.D_E_L_E_T_ == " ",
            cb8.c.CB8_FILIAL == "01",
            cb8.c.CB8_ORDSEP == ordem_separacao,
            cb8.c.CB8_ITEM >= " ",
            cb8.c.CB8_SEQUEN >= " ",
            cb8.c.CB8_PROD >= " ",
            cb8.c.CB8_SALDOS > 0,
        ]
        if item:
            condicao.append(cb8.c.CB8_ITEM == item)

        subquery_itens = (
            select(
                cb8.c.CB8_ITEM.label("item"),
                cb8.c.CB8_PEDIDO.label("pedido"),
                cb8.c.CB8_PROD.label("codigo_produto"),
                func.trim(sb1.c.B1_DESC).label("descricao_produto"),
                cb8.c.CB8_LOCAL.label("almoxarifado"),
                func.min(
                    func.coalesce(
                        z0o.c.Z0O_POSICA,
                        cast(cast(cb8.c.CB8_LOCAL, Integer), String)
                        + literal_column("'-ALMOX'"),
                    )
                ).label("posicao"),
                func.count(z0o.c.Z0O_POSICA).label("total_posicoes"),
                cast(cb8.c.CB8_QTDORI, Numeric(10, 2)).label("quantidade_original"),
                cast(cb8.c.CB8_SALDOS, Numeric(10, 2)).label("saldo_separar"),
                cb8.c.CB8_SEQUEN.label("sequencia_pedido"),
                afa.c.AFA_XAGRUP.label("agrupador"),
                cb7.c.CB7_ORIGEM.label("origem"),
            )
            .select_from(
                cb8.join(
                    sb1,
                    and_(
                        sb1.c.D_E_L_E_T_ == " ",
                        sb1.c.B1_FILIAL == "01",
                        sb1.c.B1_COD == cb8.c.CB8_PROD,
                    ),
                )
                .join(
                    cb7,
                    and_(
                        cb7.c.D_E_L_E_T_ == " ",
                        cb7.c.CB7_FILIAL == "01",
                        cb7.c.CB7_ORDSEP == cb8.c.CB8_ORDSEP,
                    ),
                )
                .outerjoin(
                    z0o,
                    and_(
                        z0o.c.D_E_L_E_T_ == " ",
                        z0o.c.Z0O_FILIAL == "01",
                        z0o.c.Z0O_COD == cb8.c.CB8_PROD,
                        z0o.c.Z0O_LOCAL == cb8.c.CB8_LOCAL,
                    ),
                )
                .outerjoin(
                    afa,
                    and_(
                        afa.c.D_E_L_E_T_ == " ",
                        afa.c.AFA_FILIAL == "01",
                        afa.c.AFA_PROJET == cb8.c.CB8_XPROJE,
                        afa.c.AFA_REVISA >= " ",
                        afa.c.AFA_TAREFA == cb8.c.CB8_XTAREF,
                        afa.c.AFA_ITEM == cb8.c.CB8_XITTAR,
                        afa.c.AFA_PRODUT == cb8.c.CB8_PROD,
                        afa.c.AFA_XPROD == cb8.c.CB8_XPROD,
                    ),
                )
            )
            .where(and_(*condicao))
            .group_by(
                cb8.c.CB8_ITEM,
                cb8.c.CB8_PEDIDO,
                cb8.c.CB8_SEQUEN,
                cb8.c.CB8_PROD,
                sb1.c.B1_DESC,
                cb8.c.CB8_LOCAL,
                cb8.c.CB8_QTDORI,
                cb8.c.CB8_SALDOS,
                afa.c.AFA_XAGRUP,
                cb7.c.CB7_ORIGEM,
            )
            .subquery("itens")
        )
        # Aninhamento dos itens para ordenar o resultado por endereço e item
        # e retornar o próximo endereço e item com referência ao endereço e item anteriores
        query = (
            select(subquery_itens)
            .where(subquery_itens.c.posicao + subquery_itens.c.item > item_posicao)
            .order_by(subquery_itens.c.posicao, subquery_itens.c.item)
            .limit(2)
        )

        try:
            resultado = self.db.execute(query).mappings().all()

            for row in resultado:
                if row["total_posicoes"] > 1:
                    enderecos_alternativos = recupera_posicoes(
                        db=self.db,
                        codigo_produto=row["codigo_produto"],
                        almoxarifado=row["almoxarifado"],
                        posicao_atual=row["posicao"],
                    )

                else:
                    enderecos_alternativos = None

                itens_ordem_separacao.append(
                    ItemOrdemSeparacao(
                        **row, enderecos_alternativos=enderecos_alternativos
                    )
                )

        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Falha ao selecionar os itens da ordem de separação",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        return itens_ordem_separacao

    def pausar_separacao(self, ordem_separacao: str) -> dict:
        """
        Atualiza a separação para o status de pausa.
        """
        cb7 = ordens_separacao_cb7
        query = (
            update(cb7)
            .where(
                and_(
                    cb7.c.D_E_L_E_T_ == " ",
                    cb7.c.CB7_FILIAL == "01",
                    cb7.c.CB7_ORDSEP == ordem_separacao,
                )
            )
            .values(CB7_STATPA="1")
        )
        try:
            self.db.execute(query)
            self.db.commit()

        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Falha ao pausar separação",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        return {"resultado": "sucesso"}

    def registra_separacao(
        self,
        usuario_operador: str,
        dados_contagem: RegistraSeparacao,
    ) -> Union[ItemOrdemSeparacao, Response]:
        """
        Grava a contagem do item na ordem de separação.
        """
        self.codigo_operador = self.recupera_operador_usuario(usuario_operador)

        cb8 = aliased(itens_ordem_separacao_cb8, name="cb8")
        cb9 = aliased(registro_separacao_cb9, name="cb9")
        resultado = None

        # Para registrar a separação, pesquisa primeiro se existe registro na CB9 pela chave
        # CB8_FILIAL + CB8_ORDSEP + CB8_ITEM + CB8_PROD + CB8_LOCAL CB8_PEDIDO
        query = (
            select(
                cb8.c.CB8_SALDOS,
                cb8.c.R_E_C_N_O_.label("REGCB8"),
                func.coalesce(cb9.c.R_E_C_N_O_, 0).label("REGCB9"),
                func.coalesce(cb9.c.CB9_QTESEP, 0).label("CB9_QTESEP"),
            )
            .select_from(
                cb8.outerjoin(
                    cb9,
                    and_(
                        cb9.c.D_E_L_E_T_ == " ",
                        cb9.c.CB9_FILIAL == "01",
                        cb9.c.CB9_ORDSEP == cb8.c.CB8_ORDSEP,
                        cb9.c.CB9_ITESEP == cb8.c.CB8_ITEM,
                        cb9.c.CB9_SEQUEN == cb8.c.CB8_SEQUEN,
                        cb9.c.CB9_PROD == cb8.c.CB8_PROD,
                        cb9.c.CB9_LOCAL == cb8.c.CB8_LOCAL,
                        cb9.c.CB9_PEDIDO == cb8.c.CB8_PEDIDO,
                    ),
                )
            )
            .where(
                and_(
                    cb8.c.D_E_L_E_T_ == " ",
                    cb8.c.CB8_FILIAL == "01",
                    cb8.c.CB8_ORDSEP == dados_contagem.ordem_separacao,
                    cb8.c.CB8_ITEM == dados_contagem.item,
                    cb8.c.CB8_SEQUEN == dados_contagem.sequencia_pedido,
                    cb8.c.CB8_PROD == dados_contagem.codigo_produto,
                    cb8.c.CB8_LOCAL == dados_contagem.almoxarifado,
                    cb8.c.CB8_PEDIDO == dados_contagem.pedido,
                )
            )
        )

        try:
            resultado = self.db.execute(query).fetchone()

        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Falha recuperando saldo da separação no registro da contagem",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        if resultado:
            quantidade = min(dados_contagem.quantidade_separada, resultado.CB8_SALDOS)
            if resultado.REGCB9 > 0:
                # Caso exista contagem, incrementa a quantidade separada e o status
                query = (
                    update(registro_separacao_cb9)
                    .where(registro_separacao_cb9.c.R_E_C_N_O_ == resultado.REGCB9)
                    .values(
                        CB9_QTESEP=resultado.CB9_QTESEP + quantidade, CB9_STATUS="1"
                    )
                )

            else:
                # Se não existir, inclui novo registro
                registro_separacao = prepara_dados_protheus(
                    tabela=registro_separacao_cb9,
                    dados_protheus={
                        "CB9_FILIAL": "01",
                        "CB9_ORDSEP": dados_contagem.ordem_separacao,
                        "CB9_PROD": dados_contagem.codigo_produto,
                        "CB9_CODSEP": self.codigo_operador,
                        "CB9_ITESEP": dados_contagem.item,
                        "CB9_SEQUEN": dados_contagem.sequencia_pedido,
                        "CB9_LOCAL": dados_contagem.almoxarifado,
                        "CB9_PEDIDO": dados_contagem.pedido,
                        "CB9_QTESEP": quantidade,
                        "CB9_STATUS": "1",
                    },
                    inicializa_id=True,
                    db=self.db,
                )
                query = insert(registro_separacao_cb9).values(registro_separacao)

            try:
                self.db.execute(query)
                # Subtrai a quantidade separada do item da ordem de separação sem deixar negativo
                cb8u = itens_ordem_separacao_cb8
                self.db.execute(
                    update(cb8u)
                    .where(cb8u.c.R_E_C_N_O_ == resultado.REGCB8)
                    .values(
                        CB8_SALDOS=max(
                            Decimal(str(resultado.CB8_SALDOS))
                            - Decimal(str(quantidade)),
                            Decimal(0),
                        )
                    )
                )
                self.db.commit()

                self.atualiza_status_separacao(
                    ordem_separacao=dados_contagem.ordem_separacao,
                    usuario_operador=usuario_operador,
                )

            except SQLAlchemyError as e:
                self.db.rollback()
                log_httpexception_raise(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    mensagem="Falha gravando a contagem",
                    exc_info=True,
                    nivel_log=NivelLog.ERROR,
                    excecao=e,
                )

        else:
            query_plana = query.compile(
                dialect=self.db.bind.dialect, compile_kwargs={"literal_binds": True}
            )
            log_httpexception_raise(
                status_code=status.HTTP_404_NOT_FOUND,
                mensagem=f"Item da separação não localizado com a query {query_plana}",
                nivel_log=NivelLog.ERROR,
            )

        # Se chegou até aqui, retorna o próximo item da separação
        proximos_itens = self.recupera_itens(
            ordem_separacao=dados_contagem.ordem_separacao,
            item_anterior=dados_contagem.item,
        )

        if proximos_itens:
            return proximos_itens[0]

        else:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    

    def atualiza_status_separacao(self, ordem_separacao: str, usuario_operador: str):
        """
        Verifica se a ordem de separação está totalmente separada e atualiza seu status para concluída.
        """
        itens_com_saldo: int = None
        cb8 = aliased(itens_ordem_separacao_cb8, name="cb8")

        query = select(func.count(cb8.c.CB8_ORDSEP).label("CNT")).where(
            and_(
                cb8.c.D_E_L_E_T_ == " ",
                cb8.c.CB8_FILIAL == "01",
                cb8.c.CB8_ORDSEP == ordem_separacao,
                cb8.c.CB8_SALDOS > 0,
            )
        )

        try:
            itens_com_saldo = self.db.execute(query).scalar()
        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Falha recuperando itens com saldo",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        if itens_com_saldo is not None and itens_com_saldo == 0:
            usuario_erp = " "

            try:
                auth_service = AuthService(db=self.db)
                auth_service.recupera_dados_usuario(id_usuario=usuario_operador)

                if (
                    auth_service.dados_usuario
                    and auth_service.dados_usuario.dados_cadastro_recursos
                    and auth_service.dados_usuario.dados_cadastro_recursos.codigo_usuario_protheus
                ):
                    usuario_erp = auth_service.dados_usuario.dados_cadastro_recursos.codigo_usuario_protheus
                else:
                    logging.warning(
                        f"[ATUALIZA_STATUS_SEPARACAO] Usuário '{usuario_operador}' sem código Protheus cadastrado."
                    )

            except Exception as e:
                logging.warning(
                    f"[ATUALIZA_STATUS_SEPARACAO] Erro ao recuperar dados do usuário '{usuario_operador}': {e}"
                )

            query_update = (
                update(ordens_separacao_cb7)
                .where(
                    and_(
                        ordens_separacao_cb7.c.D_E_L_E_T_ == " ",
                        ordens_separacao_cb7.c.CB7_FILIAL == "01",
                        ordens_separacao_cb7.c.CB7_ORDSEP == ordem_separacao,
                    )
                )
                .values(
                    CB7_STATUS="9",
                    CB7_STATPA="0",
                    CB7_DTFIMS=date.today().strftime("%Y%m%d"),
                    CB7_HRFIMS=datetime.now().strftime("%H%M"),
                    CB7_XUSREN=case(
                        (ordens_separacao_cb7.c.CB7_XUSREN == " ", usuario_erp),
                        else_=ordens_separacao_cb7.c.CB7_XUSREN,
                    ),
                )
            )

            try:
                self.db.execute(query_update)
                self.db.commit()
                logging.info(
                    f"[ATUALIZA_STATUS_SEPARACAO] Ordem {ordem_separacao} concluída com sucesso (usuário ERP: {usuario_erp})."
                )
            except SQLAlchemyError as e:
                self.db.rollback()
                log_httpexception_raise(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    mensagem="Falha ao atualizar o status da separação",
                    exc_info=True,
                    nivel_log=NivelLog.ERROR,
                    excecao=e,
                )


    def obter_todos_itens_os(self, ordem_separacao: str) -> List[ItemOrdemSeparacao]:
        """
        Recupera TODOS os itens da ordem de separação para exibição na tela intermediária.
        """
        itens_ordem_separacao: List[ItemOrdemSeparacao] = []
        cb8 = aliased(itens_ordem_separacao_cb8, name="cb8")
        cb7 = aliased(ordens_separacao_cb7, name="cb7")
        sb1 = aliased(produtos_sb1, name="sb1")
        afa = aliased(insumos_projetos_afa, name="afa")

        query = (
            select(
                cb8.c.CB8_ITEM.label("item"),
                cb8.c.CB8_PEDIDO.label("pedido"),
                cb8.c.CB8_PROD.label("codigo_produto"),
                func.trim(sb1.c.B1_DESC).label("descricao_produto"),
                cb8.c.CB8_LOCAL.label("almoxarifado"),
                # Remove a referência ao z0o e usa apenas o almoxarifado como posição padrão
                (cast(cb8.c.CB8_LOCAL, String) + literal_column("'-ALMOX'")).label("posicao"),
                cast(cb8.c.CB8_QTDORI, Numeric(10, 2)).label("quantidade_original"),
                cast(cb8.c.CB8_SALDOS, Numeric(10, 2)).label("saldo_separar"),
                cb8.c.CB8_SEQUEN.label("sequencia_pedido"),
                afa.c.AFA_XAGRUP.label("agrupador"),
                cb7.c.CB7_ORIGEM.label("origem"),
                case(
                    (cb8.c.CB8_SALDOS == 0, "Separado"),
                    (cb8.c.CB8_SALDOS > 0, "Pendente"),
                    else_="Indefinido"
                ).label("status_item")
            )
            .select_from(
                cb8.join(
                    sb1,
                    and_(
                        sb1.c.D_E_L_E_T_ == " ",
                        sb1.c.B1_FILIAL == "01",
                        sb1.c.B1_COD == cb8.c.CB8_PROD,
                    ),
                )
                .join(
                    cb7,
                    and_(
                        cb7.c.D_E_L_E_T_ == " ",
                        cb7.c.CB7_FILIAL == "01",
                        cb7.c.CB7_ORDSEP == cb8.c.CB8_ORDSEP,
                    ),
                )
                .outerjoin(
                    afa,
                    and_(
                        afa.c.D_E_L_E_T_ == " ",
                        afa.c.AFA_FILIAL == "01",
                        afa.c.AFA_PROJET == cb8.c.CB8_XPROJE,
                        afa.c.AFA_REVISA >= " ",
                        afa.c.AFA_TAREFA == cb8.c.CB8_XTAREF,
                        afa.c.AFA_ITEM == cb8.c.CB8_XITTAR,
                        afa.c.AFA_PRODUT == cb8.c.CB8_PROD,
                        afa.c.AFA_XPROD == cb8.c.CB8_XPROD,
                    ),
                )
            )
            .where(
                and_(
                    cb8.c.D_E_L_E_T_ == " ",
                    cb8.c.CB8_FILIAL == "01",
                    cb8.c.CB8_ORDSEP == ordem_separacao,
                    cb8.c.CB8_ITEM >= " ",
                    cb8.c.CB8_PROD >= " ",
                    cb8.c.CB8_SEQUEN >= " ",
                )
            )
            .order_by(cb8.c.CB8_ITEM)
        )

        try:
            resultado = self.db.execute(query).mappings().all()

            for row in resultado:
                # Para cada item, busca as posições (incluindo a principal)
                posicoes = recupera_posicoes(
                    db=self.db,
                    codigo_produto=row["codigo_produto"],
                    almoxarifado=row["almoxarifado"],
                    posicao_atual=None,  # Não temos mais posição atual do z0o
                )
                
                # Define a posição principal (primeira da lista ou almoxarifado como fallback)
                posicao_principal = row["almoxarifado"] + "-ALMOX"
                enderecos_alternativos = None
                
                if posicoes:
                    posicao_principal = posicoes[0]  # Primeira posição é a principal
                    if len(posicoes) > 1:
                        enderecos_alternativos = posicoes[1:]  # Restante são alternativas

                # Atualiza a posição no row
                row_dict = dict(row)
                row_dict["posicao"] = posicao_principal

                #print(f"DEBUG origem={row.get('origem')} item={row['item']}")

                itens_ordem_separacao.append(
                    ItemOrdemSeparacao(
                        **row_dict, 
                        enderecos_alternativos=enderecos_alternativos,
                        total_posicoes=1 if not enderecos_alternativos else len(posicoes)
                    )
                )

            return itens_ordem_separacao

        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem=f"Falha ao selecionar os itens da ordem de separação {ordem_separacao}",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

    def encerrar_separacao(self, ordem_separacao: str) -> dict:
        """
        Encerra a ordem de separação conforme regras de negócio.
        """

        cb7 = ordens_separacao_cb7
        cb8 = itens_ordem_separacao_cb8
        sc6 = pedidos_vendas_sc6
        afa = insumos_projetos_afa

        # 1️⃣ Buscar origem da ordem
        origem_stmt = select(cb7.c.CB7_ORIGEM).where(
            cb7.c.CB7_ORDSEP == ordem_separacao,
            cb7.c.D_E_L_E_T_ == " ",
            cb7.c.CB7_FILIAL == "01",
        )

        try:
            origem = self.db.execute(origem_stmt).scalar()
        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Falha ao recuperar origem da ordem de separação",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        # 🚫 Regras de origem: só pode 5 ou 6
        if origem not in ["5", "6"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não é permitido encerrar ordem {ordem_separacao} com origem {origem}. "
                    "Apenas origens 5 ou 6 são válidas."
            )

        # 2️⃣ Verificar pendências (CB8 + SC6)
        pendencia_stmt = (
            select(func.count())
            .select_from(
                cb8.join(
                    sc6,
                    and_(
                        sc6.c.D_E_L_E_T_ == " ",
                        sc6.c.C6_FILIAL == "01",
                        sc6.c.C6_NUM >= " ",
                        sc6.c.C6_ITEM >= " ",
                        sc6.c.C6_PRODUTO == cb8.c.CB8_PROD,
                        sc6.c.C6_XCPORIG == cb8.c.CB8_XNUMSA,
                        sc6.c.C6_XITCPOR == cb8.c.CB8_XITSA,
                        sc6.c.C6_XCPORIG != " ",
                        sc6.c.C6_XITCPOR != " ",
                    ),
                )
            )
            .where(
                cb8.c.D_E_L_E_T_ == " ",
                cb8.c.CB8_FILIAL == "01",
                cb8.c.CB8_ORDSEP == ordem_separacao,
                cb8.c.CB8_ITEM >= " ",
            )
        )


        try:
            pendencias = self.db.execute(pendencia_stmt).scalar()
        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao verificar pendências na separação",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        if pendencias > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Existem pendências entre CB8 e SC6. Não é possível encerrar."
            )

        # 3️⃣ Definir CB7_XTPENT / CB7_XDOCEN
        try:
            cb8_info = self.db.execute(
                select(cb8.c.CB8_XNUMSA)
                .where(cb8.c.D_E_L_E_T_ == " ", cb8.c.CB8_ORDSEP == ordem_separacao)
                .limit(1)
            ).first()
        except SQLAlchemyError as e:
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Falha ao buscar CB8_XNUMSA para encerramento",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        if cb8_info and cb8_info.CB8_XNUMSA.strip():
            xtpent = "4"
            xdocen = cb8_info.CB8_XNUMSA.strip()
        else:
            xtpent = "3"
            xdocen = " " * 10

        # 4️⃣ Atualizar CB7
        update_stmt = (
            update(cb7)
            .where(
                cb7.c.D_E_L_E_T_ == " ",
                cb7.c.CB7_FILIAL == "01",
                cb7.c.CB7_ORDSEP == ordem_separacao,
            )
            .values(
                CB7_STATUS="9",
                CB7_STATPA="0",
                CB7_DTFIMS=datetime.now().strftime("%Y%m%d"),
                CB7_HRFIMS=datetime.now().strftime("%H%M"),
                CB7_XTPENT=xtpent,
                CB7_XDOCEN=xdocen,
            )
        )

        try:
            self.db.execute(update_stmt)
        except SQLAlchemyError as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao atualizar CB7 durante encerramento",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        # 5️⃣ Limpar vínculos AFA_XORDSE
        afa_stmt = (
            select(afa.c.R_E_C_N_O_)
            .select_from(
                cb8.join(
                    afa,
                    and_(
                        afa.c.D_E_L_E_T_ == " ",
                        afa.c.AFA_FILIAL == "01",
                        afa.c.AFA_PROJET == cb8.c.CB8_XPROJE,
                        afa.c.AFA_TAREFA == cb8.c.CB8_XTAREF,
                        afa.c.AFA_ITEM == cb8.c.CB8_XITTAR,
                        afa.c.AFA_PRODUT == cb8.c.CB8_PROD,
                        afa.c.AFA_XORDSE == cb8.c.CB8_ORDSEP,
                    ),
                )
            )
            .where(
                cb8.c.D_E_L_E_T_ == " ",
                cb8.c.CB8_FILIAL == "01",
                cb8.c.CB8_ORDSEP == ordem_separacao,
            )
        )

        try:
            registros_afa = [r[0] for r in self.db.execute(afa_stmt)]
            for reg in registros_afa:
                self.db.execute(
                    update(afa)
                    .where(afa.c.R_E_C_N_O_ == reg)
                    .values(AFA_XORDSE="      ")
                )
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro ao limpar vínculos em AFA (AFA_XORDSE)",
                exc_info=True,
                nivel_log=NivelLog.ERROR,
                excecao=e,
            )

        return {"detail": f"✅ Ordem {ordem_separacao} encerrada com sucesso e atualizada."}


def recupera_posicoes(
    db: Session, codigo_produto: str, almoxarifado: str, posicao_atual: str
) -> List[str]:
    """
    Recupera outras possíveis posições de armazenamento do produto, diferentes da posição atual.
    """
    posicoes: List = None
    z0o = aliased(posicoes_z0o, name="z0o")
    query = (
        select(z0o.c.Z0O_POSICA)
        .where(
            and_(
                z0o.c.D_E_L_E_T_ == " ",
                z0o.c.Z0O_FILIAL == "01",
                z0o.c.Z0O_COD == codigo_produto,
                z0o.c.Z0O_LOCAL == almoxarifado,
                z0o.c.Z0O_POSICA != posicao_atual,
            )
        )
        .order_by(z0o.c.Z0O_POSICA)
    )
    try:
        posicoes = [row[0] for row in db.execute(query).fetchall()]

    except SQLAlchemyError as e:
        log_httpexception_raise(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            mensagem="Falha na recuperação de posições complementares",
            exc_info=True,
            nivel_log=NivelLog.ERROR,
            excecao=e,
        )

    return posicoes


@ordens_separacao_router.get(
    "/ordens_separacao", summary="Listagem de ordens de separação"
)
def lista_ordens_separacao(
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> ListaOrdensSeparacao:
    """
    Lista as ordens de separação disponíveis na fila ou direcionadas ao operador autenticado.
    """
    if valida_chave_coletor(x_cliente_token):
        ordens_separacao = OrdensSeparacao(db=db)
        return ordens_separacao.lista_ordens_separacao(payload.get("sub"))

    else:
        log_httpexception_raise(
            status_code=status.HTTP_403_FORBIDDEN,
            mensagem="Chave de cliente inválida!",
            nivel_log=NivelLog.WARNING,
        )


@ordens_separacao_router.post(
    "/separar/{ordem_separacao}",
    summary="Processo de registro da separação de materiais",
)
def separar_ordem(
    ordem_separacao: str = Path(...),
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente do endpoint"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[ItemOrdemSeparacao]:
    """
    Endpoint para iniciar o processo de separação a partir da fila.
    """
    return separar(
        ordem_separacao=ordem_separacao,
        x_cliente_token=x_cliente_token,
        payload=payload,
        db=db,
    )


@ordens_separacao_router.post(
    "/separar/{ordem_separacao}/{item}",
    summary="Processo de registro da separação de materiais",
)
def separar_ordem_item(
    ordem_separacao: str = Path(...),
    item: str = Path(...),
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[ItemOrdemSeparacao]:
    """
    Endpoint para dar continuidade ao processo de separação a partir de um item.
    """
    return separar(
        ordem_separacao=ordem_separacao,
        item=item,
        x_cliente_token=x_cliente_token,
        payload=payload,
        db=db,
    )


@ordens_separacao_router.post(
    "/pular_item/{ordem_separacao}/{item_anterior}",
    summary="Pula o item enviado retornando o próximo item",
)
def pular_item(
    ordem_separacao: str = Path(...),
    item_anterior: str = Path(...),
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[ItemOrdemSeparacao]:
    """
    Endpoint para pular o item da separação.
    """
    return separar(
        ordem_separacao=ordem_separacao,
        item_anterior=item_anterior,
        x_cliente_token=x_cliente_token,
        payload=payload,
        db=db,
    )


def separar(
    ordem_separacao: str,
    x_cliente_token: str,
    payload: dict,
    db: Session,
    item: Optional[str] = None,
    item_anterior: Optional[str] = None,
) -> Union[List[ItemOrdemSeparacao], Response]:
    """
    Função para retornar os dados do item para separação.\n
    Se 'item_anterior' for infomado, busca os dados do próximo item.\n
    Se 'item' for informado, retorna os dados do próprio item informado.
    """
    if not valida_chave_coletor(x_cliente_token):
        log_httpexception_raise(
            status_code=status.HTTP_403_FORBIDDEN,
            mensagem="Chave de cliente inválida!",
            nivel_log=NivelLog.WARNING,
        )

    ordens_separacao = OrdensSeparacao(db=db)
    # Se o item não é nulo, significa que a separação já foi iniciada
    if not item:
        ordens_separacao.atualiza_operador(ordem_separacao, payload.get("sub"))

    itens_recuperados = ordens_separacao.recupera_itens(
        ordem_separacao, item=item, item_anterior=item_anterior
    )

    if itens_recuperados:
        return itens_recuperados

    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@ordens_separacao_router.post(
    "/pausar_separacao/{ordem_separacao}",
    summary="Coloca a ordem de separação em pausa",
)
def pausar_separacao(
    ordem_separacao: str,
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> dict:
    """
    Enpoint para pausar a Ordem de Separação.
    """
    if not valida_chave_coletor(x_cliente_token):
        log_httpexception_raise(
            status_code=status.HTTP_403_FORBIDDEN,
            mensagem="Chave de cliente inválida!",
            nivel_log=NivelLog.WARNING,
        )

    ordens_separacao = OrdensSeparacao(db=db)
    return ordens_separacao.pausar_separacao(ordem_separacao)

@ordens_separacao_router.post(
    "/encerrar_separacao/{ordem_separacao}",
    summary="Encerra a ordem de separação",
)
def encerrar_separacao(
    ordem_separacao: str,
    x_cliente_token: str = Header(alias="X-Cliente-Token"),
    db: Session = Depends(get_db),
):
    if not valida_chave_coletor(x_cliente_token):
        log_httpexception_raise(
            status_code=status.HTTP_403_FORBIDDEN,
            mensagem="Chave de cliente inválida!",
            nivel_log=NivelLog.WARNING,
        )

    ordens = OrdensSeparacao(db=db)
    return ordens.encerrar_separacao(ordem_separacao)



@ordens_separacao_router.post(
    "/registra_separacao", summary="Registra a separação do material"
)
def registra_separacao(
    dados_contagem: RegistraSeparacao,
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> ItemOrdemSeparacao:
    """
    Endpoint para gravar os dados da separação coletados.
    """
    if not valida_chave_coletor(x_cliente_token):
        log_httpexception_raise(
            status_code=status.HTTP_403_FORBIDDEN,
            mensagem="Chave de cliente inválida!",
            nivel_log=NivelLog.WARNING,
        )

    ordens_separacao = OrdensSeparacao(db=db)
    return ordens_separacao.registra_separacao(
        usuario_operador=payload.get("sub"),
        dados_contagem=dados_contagem,
    )


def valida_chave_coletor(chave_cliente) -> bool:
    """
    Valida se a chave do cliente que identifica o coletor está coerente com a definida no ambiente.
    """
    return chave_cliente == Environment.CHAVE_COLETOR

@ordens_separacao_router.get("/verifica_pendencias/{ordem_separacao}")
def verifica_pendencias(ordem_separacao: str, db: Session = Depends(get_db)):
    cb8 = itens_ordem_separacao_cb8
    sc6 = pedidos_vendas_sc6  # tabela SC6

    stmt = (
        select(func.count())
        .select_from(
            cb8.join(
                sc6,
                and_(
                    sc6.c.D_E_L_E_T_ == " ",
                    sc6.c.C6_FILIAL == "01",
                    sc6.c.C6_NUM >= " ",
                    sc6.c.C6_ITEM >= " ",
                    sc6.c.C6_PRODUTO == cb8.c.CB8_PROD,
                    sc6.c.C6_XCPORIG == cb8.c.CB8_XNUMSA,
                    sc6.c.C6_XITCPOR == cb8.c.CB8_XITSA,
                    sc6.c.C6_XCPORIG != " ",
                    sc6.c.C6_XITCPOR != " ",
                ),
            )
        )
        .where(
            cb8.c.D_E_L_E_T_ == " ",
            cb8.c.CB8_FILIAL == "01",
            cb8.c.CB8_ORDSEP == ordem_separacao,
            cb8.c.CB8_ITEM >= " ",
            cb8.c.CB8_SALDOS > 0,  # ainda há saldo a separar
        )
    )

    pendencias = db.execute(stmt).scalar() or 0
    print(f"🔎 Verifica pendências → OS {ordem_separacao}: {pendencias} itens com saldo")
    return {"pendencias": pendencias}



@ordens_separacao_router.get(
    "/itens_ordem_separacao/{ordem_separacao}",
    summary="Lista todos os itens de uma ordem de separação",
    response_model=List[ItemOrdemSeparacao]
)
def obter_itens_ordem_separacao(
    ordem_separacao: str = Path(..., description="Número da ordem de separação"),
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> List[ItemOrdemSeparacao]:
    """
    Endpoint para obter TODOS os itens de uma ordem de separação específica.
    Ideal para exibição em telas de consulta.
    """
    if not valida_chave_coletor(x_cliente_token):
        log_httpexception_raise(
            status_code=status.HTTP_403_FORBIDDEN,
            mensagem="Chave de cliente inválida!",
            nivel_log=NivelLog.WARNING,
        )

    ordens_separacao = OrdensSeparacao(db=db)
    itens = ordens_separacao.obter_todos_itens_os(ordem_separacao)
    
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum item encontrado para a ordem de separação {ordem_separacao}"
        )
    
    return itens

@ordens_separacao_router.post("/encerrar/{ordem_separacao}")
def encerrar_ordem(
    ordem_separacao: str = Path(...),
    x_cliente_token: str = Header(alias="X-Cliente-Token"),
    db: Session = Depends(get_db)
):
    if not valida_chave_coletor(x_cliente_token):
        raise HTTPException(status_code=403, detail="Chave de cliente inválida!")

    try:
        ordens = OrdensSeparacao(db=db)
        ordens.encerrar(ordem_separacao)  # <-- você vai criar esse método
        return {"mensagem": f"Ordem {ordem_separacao} encerrada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ordens_separacao_router.get("/origem_separacao/{ordem_separacao}")
def origem_separacao(ordem_separacao: str, db: Session = Depends(get_db)):
    """
    Retorna a origem da ordem de separação (CB7_ORIGEM)
    """
    query = select(ordens_separacao_cb7.c.CB7_ORIGEM).where(
        and_(
            ordens_separacao_cb7.c.D_E_L_E_T_ == " ",
            ordens_separacao_cb7.c.CB7_FILIAL == "01",
            ordens_separacao_cb7.c.CB7_ORDSEP == ordem_separacao,
        )
    )
    origem = db.execute(query).scalar()

    if origem is None:
        raise HTTPException(
            status_code=404, detail=f"Ordem {ordem_separacao} não encontrada."
        )

    return {"origem": origem}
