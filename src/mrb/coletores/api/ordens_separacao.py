from decimal import Decimal
import time
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Header, Path, Response, status
from sqlalchemy import (
    Integer,
    Numeric,
    Select,
    String,
    Tuple,
    and_,
    cast,
    func,
    insert,
    literal,
    literal_column,
    select,
    text,
    union_all,
    update,
)
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError

from src.mrb.common.lib.prepara_dados_protheus import prepara_dados_protheus
from src.mrb.common.config import Environment
from src.mrb.coletores.schemas.schema_ordem_separacao import (
    ItemOrdemSeparacao,
    ListaOrdensSeparacao,
    OrdemSeparacao,
    RegistraSeparacao,
)
from src.mrb.common.security.auth_service import valida_token
from src.mrb.common.database.db_engine import get_db
from src.mrb.common.models.model_recursos_protheus import recursos_ae8
from src.mrb.common.models.model_usuarios_portal import usuarios_szk
from src.mrb.coletores.models.model_operadores_cb1 import operadores_cb1
from src.mrb.coletores.models.model_ordens_separacao import ordens_separacao_cb7
from src.mrb.coletores.models.model_posicoes_almoxarifado import posicoes_z0o
from src.mrb.coletores.models.model_itens_ordem_separacao import (
    itens_ordem_separacao_cb8,
)
from src.mrb.coletores.models.model_registro_separacao import registro_separacao_cb9
from src.mrb.comercial.models.model_clientes import clientes_sa1

ordens_separacao_router = APIRouter()


class OrdensSeparacao:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.codigo_operador: str = None

    def lista_ordens_separacao(self, usuario_operador: str):
        cb7 = aliased(ordens_separacao_cb7, name="cb7")
        sa1 = aliased(clientes_sa1, name="sa1")

        # Seleciona o código do operador com base no id do usuário
        query_usuario = self.query_usuario(usuario_operador)

        # Acrescenta o código de operador da fila de separação, onde todos podem atender
        # e monta a CTE para o WITH na seleção das ordens de separação
        query_operador = union_all(
            query_usuario, select(literal("000000").label("CB1_CODOPE"))
        ).cte("operadores")

        # Seleciona as ordens de separação vinculadas ao operador e na fila de separação
        query = (
            select(
                cb7.c.CB7_ORDSEP.label("ordem_separacao"),
                cb7.c.CB7_PEDIDO.label("pedido_vendas"),
                sa1.c.A1_NOME.label("nome_cliente"),
                cb7.c.CB7_XPROJE.label("projeto"),
                cb7.c.CB7_XPROD.label("celula"),
                cb7.c.CB7_XCONTE.label("conteiner"),
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
        ).order_by(cb7.c.CB7_PRIORI, cb7.c.CB7_ORDSEP)

        try:
            resultado = self.db.execute(query).mappings().all()
            ordens_separacao = [
                OrdemSeparacao.model_validate(
                    {
                        chave: valor.strip() if isinstance(valor, str) else valor
                        for chave, valor in row.items()
                    }
                )
                for row in resultado
            ]
            return ListaOrdensSeparacao(
                total_de_registros=len(ordens_separacao),
                ordens_separacao=ordens_separacao,
            )

        except HTTPException:
            raise

        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao selecionar as ordens de separação para o operador: {e}",
            )

    def query_usuario(self, usuario_operador: str) -> Select[Tuple]:
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

        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao buscar código do operador: {e}",
            )

        return codigo_operador

    def atualiza_operador(self, ordem_separacao: str, usuario_operador: str):
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
            # Inicia a transação
            self.db.begin()

            # Recupera o código do operador da ordem de separação bloqueando o registro
            operador_atual: str = self.db.execute(query).scalar()

        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao buscar a ordem de separação: {e}",
            )

        operador_atual = (
            operador_atual if operador_atual and (operador_atual.strip()) else "000000"
        )

        # Valida que não está para outro operador
        # Não é fila de separação e é de outro operador
        if (
            not operador_atual == "000000"
            and not operador_atual == self.codigo_operador
        ):
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A ordem de separação foi capturada pelo operador {operador_atual}",
            )

        # Se for fila de separação ou do próprio operador atualiza o operador e inicializa a separação
        if operador_atual == "000000" or operador_atual == self.codigo_operador:
            query = (
                update(cb7)
                .where(
                    cb7.c.D_E_L_E_T_ == " ",
                    cb7.c.CB7_FILIAL == "01",
                    cb7.c.CB7_ORDSEP == ordem_separacao,
                )
                .values(CB7_CODOPE=self.codigo_operador, CB7_STATUS="1", CB7_STATPA="0")
            )
            try:
                self.db.execute(query)

            except SQLAlchemyError as e:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Falha ao inicar a separação {e}",
                )

            # Pausa as demais ordens de separação que estiverem em andamento para o operador
            query = (
                update(cb7)
                .where(
                    cb7.c.D_E_L_E_T_ == " ",
                    cb7.c.CB7_FILIAL == "01",
                    cb7.c.CB7_ORDSEP != ordem_separacao,
                    cb7.c.CB7_CODOPE == self.codigo_operador,
                    cb7.c.CB7_STATUS >= "1",
                    cb7.c.CB7_STATUS <= "8",
                    cb7.c.CB7_DIVERG != "1",
                    cb7.c.CB7_STATPA != "1",
                )
                .values(CB7_STATPA="1")
            )
            try:
                self.db.execute(query)
                self.db.commit()

            except SQLAlchemyError as e:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Falha ao pausar separações do operador {e}",
                )

    def recupera_itens(
        self, ordem_separacao: str, item_anterior: str = " ", item: str = None
    ) -> List[ItemOrdemSeparacao]:
        itens_ordem_separacao: List[ItemOrdemSeparacao] = []
        cb8 = aliased(itens_ordem_separacao_cb8, name="cb8")
        z0o = aliased(posicoes_z0o, name="z0o")
        condicao = [
            cb8.c.D_E_L_E_T_ == " ",
            cb8.CB8_FILIAL == "01",
            cb8.c.CB8_ORDSEP == ordem_separacao,
            cb8.c.CB8_ITEM > item_anterior,
        ]
        if item:
            condicao.append(cb8.c.CB8_ITEM == item)

        query = (
            select(
                cb8.c.CB8_ITEM.label("item"),
                cb8.c.CB8_PEDIDO.label("pedido"),
                cb8.c.CB8_PROD.label("codigo_produto"),
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
            .where(and_(*condicao))
            .group_by(
                cb8.c.CB8_ITEM,
                cb8.c.CB8_PROD,
                cb8.c.CB8_LOCAL,
                cb8.c.CB8_QTDORI,
                cb8.c.CB8_SALDOS,
            )
            .order_by(func.min(z0o.c.Z0O_POSICA), cb8.c.CB8_ITEM)
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha ao selecionar os itens da ordem de separação {e}",
            )

        return itens_ordem_separacao

    def pausar_separacao(self, ordem_separacao: str) -> dict:
        cb7 = aliased(ordens_separacao_cb7, name="cb7")
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha ao pausar separação: {e}",
            )

        return {"resultado": "sucesso"}

    def registra_separacao(
        self,
        usuario_operador: str,
        dados_contagem: RegistraSeparacao,
    ) -> Union[ItemOrdemSeparacao, Response]:
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha recuperando saldo da separação no registro da contagem {e}",
            )

        if resultado:
            quantidade = min(dados_contagem.quantidade_separada, resultado.CB8_SALDOS)
            if resultado.REGCB9 > 0:
                # Caso exista contagem, incrementa a quantidade separada e o status
                query = (
                    update(cb9)
                    .where(cb9.c.R_E_C_N_O_ == resultado.REGCB9)
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
                self.db.execute(
                    update(cb8)
                    .where(cb8.c.R_E_C_N_O_ == resultado.REGCB8)
                    .values(CB8_SALDOS=max(resultado.CB8_SALDOS - quantidade, 0))
                )
                self.db.commit()
                if resultado.REGCB9 == 0:
                    time.sleep(0.25)

            except SQLAlchemyError as e:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Falha gravando a contagem {e}",
                )

        else:
            query_plana = query.compile(
                dialect=self.db.bind.dialect, compile_kwargs={"literal_binds": True}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item da separação não localizado com a query {query_plana}",
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


def recupera_posicoes(
    db: Session, codigo_produto: str, almoxarifado: str, posicao_atual: str
) -> List[str]:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na recuperação de posições complementares {e}",
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Chave de cliente inválida!"
        )


@ordens_separacao_router.post(
    "/separar/{ordem_separacao}",
    summary="Processo de registro da separação de materiais",
)
@ordens_separacao_router.post(
    "/separar/{ordem_separacao}/{item}",
    summary="Processo de registro da separação de materiais",
)
@ordens_separacao_router.post(
    "/pular_item/{ordem_separacao}/{item_anterior}",
    summary="Pula o item enviado retornando o próximo item",
)
def separar(
    ordem_separacao: str,
    item: Optional[str] = Path(default=None),
    item_anterior: Optional[str] = Path(default=None),
    x_cliente_token: str = Header(
        alias="X-Cliente-Token", title="Chave de identificação do cliente"
    ),
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
) -> Union[List[ItemOrdemSeparacao], Response]:
    if not valida_chave_coletor(x_cliente_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Chave de cliente inválida!"
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
    if not valida_chave_coletor(x_cliente_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Chave de cliente inválida!"
        )

    ordens_separacao = OrdensSeparacao(db=db)
    return ordens_separacao.pausar_separacao(ordem_separacao)


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
) -> Union[ItemOrdemSeparacao, Response]:
    if not valida_chave_coletor(x_cliente_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Chave de cliente inválida!"
        )

    ordens_separacao = OrdensSeparacao(db=db)
    return ordens_separacao.registra_separacao(
        usuario_operador=payload.get("sub"),
        dados_contagem=dados_contagem,
    )


def valida_chave_coletor(chave_cliente) -> bool:
    return chave_cliente == Environment.CHAVE_COLETOR
