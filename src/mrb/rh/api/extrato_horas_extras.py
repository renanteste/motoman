from datetime import date, datetime, timedelta
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import (
    Date,
    Select,
    and_,
    case,
    delete,
    desc,
    exists,
    func,
    text,
    union_all,
)
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import mssql

from src.mrb.rh.relatorios.relatorio_extrato_horas_extras import (
    relatorio_extrato_horas_extras,
)
from src.mrb.rh.schemas.schema_colaboradores_extrato import (
    ColaboradorExtrato,
    ListaColaboradorExtrato,
)
from src.mrb.rh.schemas.schema_periodos_banco_horas import (
    ListaPeriodosBancoHoras,
    PeriodoBancoDeHoras,
)
from src.mrb.common.lib.recupera_parametro_sx6 import RecuperaParametroSx6
from src.mrb.rh.schemas.schema_extrato_horas_extras import (
    ExtratoHorasExtras,
    MovimentoExtratoHorasExtras,
)
from src.mrb.common.database.db_engine import get_db
from src.mrb.common.security.auth_service import AuthService, valida_token
from src.mrb.common.lib.log_httpexception_raise import log_httpexception_raise
from src.mrb.rh.models.model_movimentos_horas_extras import MovimentosHorasExtras
from src.mrb.rh.models.model_solicitacoes_horas_extras import SolicitacoesHorasExtras
from src.mrb.rh.models.model_feriados_sp3 import feriados_sp3
from src.mrb.rh.models.model_apontamentos_zzu import apontamentos_zzu
from src.mrb.rh.models.model_funcionarios_sra import funcionarios_sra
from src.mrb.rh.models.model_apontamentos_spc import apontamentos_spc
from src.mrb.rh.models.model_historico_apontamentos_sph import (
    historico_apontamentos_sph,
)
from src.mrb.common.models.model_recursos_protheus import recursos_ae8
from src.mrb.common.models.model_tabelas_genericas_sx5 import tabelas_genericas_sx5

extrato_horas_extras_router = APIRouter()


def valida_acesso_endpoint(db: Session, payload: dict) -> bool:
    auth_service = AuthService(db)
    return auth_service.valida_acesso(payload.get("sub"), "EXTRATO_HE")


class CalculaExtratoHorasExtras:

    def __init__(
        self, db: Session, matricula_lider: str, codigo_periodo: str = None
    ) -> None:
        self.db = db
        self.matricula_lider = matricula_lider
        self.data_inicial: date = None
        self.data_final: date = None
        self.datas_intervalo: List[date] = []
        # Propriedade deve armazenar o período atual (em vigor) de acúmulo do banco de horas
        # [0]: Código, [1]: Data inicial, [3]: Data final
        self.periodo_atual: List[str, date, date] = []
        # Propriedade armazenará o período que está sendo consultado
        # [0]: Código, [1]: Data inicial, [3]: Data final
        self.periodo_consulta: List[str, date, date] = []
        # Código de abono do ponto no ERP para desconto da ausência do banco de horas
        self.codigo_abono_bh: str = (
            RecuperaParametroSx6(db=self.db)
            .retorna_parametro_sx6("MM_CDABBHR")
            .conteudo_parametro
        )

        # Recupera o período de Banco de Horas
        self.recupera_periodos(codigo_periodo)

        # Monta a tabela de datas para o período com a carga horária e feriados
        self.monta_tabela_datas()

    def recupera_periodos(self, codigo_periodo: str = None):
        """
        Método irá recuperar os períodos de cálculo de banco de horas, alimentando as propriedades
        periodo_atual e periodo_consulta.
        \n
        Se o argumento codigo_periodo não for informado, será considerado o periodo em vigor
        """
        sx5 = aliased(tabelas_genericas_sx5, name="sx5")

        # Recupera o período atualmente aberto
        query = (
            Select(sx5.c.X5_CHAVE, sx5.c.X5_DESCRI)
            .where(
                sx5.c.D_E_L_E_T_ == " ", sx5.c.X5_FILIAL == " ", sx5.c.X5_TABELA == "Z0"
            )
            .order_by(desc(sx5.c.X5_DESCRI))
            .limit(1)
        )
        resultado = self.db.execute(query).first()
        if resultado:
            self.periodo_atual = [
                resultado.X5_CHAVE,
                datetime.strptime(resultado.X5_DESCRI[:8], "%Y%m%d").date(),
                datetime.strptime(resultado.X5_DESCRI.strip()[8:], "%Y%m%d").date(),
            ]

            # Caso tenha sido informado o codigo de período para consulta, recupera pelo código de período
            resultado = None
            if codigo_periodo:
                query = Select(sx5.c.X5_CHAVE, sx5.c.X5_DESCRI).where(
                    sx5.c.D_E_L_E_T_ == " ",
                    sx5.c.X5_FILIAL == " ",
                    sx5.c.X5_TABELA == "Z0",
                    sx5.c.X5_CHAVE == codigo_periodo,
                )
                resultado = self.db.execute(query).fetchone()

            if resultado:
                # O código de período foi informado e retornou dados
                self.periodo_consulta = [
                    resultado.X5_CHAVE,
                    datetime.strptime(resultado.X5_DESCRI[:8], "%Y%m%d").date(),
                    datetime.strptime(resultado.X5_DESCRI.strip()[8:], "%Y%m%d").date(),
                ]

            else:
                self.periodo_consulta = self.periodo_atual[:]

            self.data_inicial = self.periodo_consulta[1]
            self.data_final = self.periodo_consulta[2]

        else:
            log_httpexception_raise(
                status_code=status.HTTP_404_NOT_FOUND,
                mensagem="""
                            Não localizado o último período de acúmulo de Banco de Horas na tabela
                            'Z0' do arquivo 'SX5' no ERP Protheus!
                        """,
                exc_info=True,
                nivel_log=1,
            )

    def monta_tabela_datas(self):
        try:
            sp3 = aliased(feriados_sp3, name="sp3")

            # Recupera os feriados fixos
            query = (
                Select(sp3.c.P3_MESDIA)
                .where(
                    and_(
                        sp3.c.D_E_L_E_T_ == " ",
                        sp3.c.P3_FILIAL == "01",
                        sp3.c.P3_TPEXT.in_(["4", "8"]),
                        sp3.c.P3_MESDIA != " ",
                    )
                )
                .group_by(sp3.c.P3_MESDIA)
                .order_by(sp3.c.P3_MESDIA)
            )
            feriados_fixos = list(self.db.execute(query).scalars().all())

            # Recupera os feriados móveis
            query = (
                Select(sp3.c.P3_DATA)
                .where(
                    sp3.c.D_E_L_E_T_ == " ",
                    sp3.c.P3_FILIAL == "01",
                    sp3.c.P3_DATA.between(
                        self.data_inicial.strftime("%Y%m%d"),
                        self.data_final.strftime("%Y%m%d"),
                    ),
                    sp3.c.P3_MESDIA == " ",
                    sp3.c.P3_TPEXT.in_(["4", "8"]),
                )
                .order_by(sp3.c.P3_DATA)
            )
            feriados_moveis = list(self.db.execute(query).scalars().all())

            data_atual = self.data_inicial
            self.datas_intervalo: List[List[date, int, bool]] = []
            while data_atual <= self.data_final:
                feriado = (
                    data_atual.strftime("%m%d") in feriados_fixos
                    or data_atual.strftime("%Y%m%d") in feriados_moveis
                )
                dia_da_semana = data_atual.weekday()
                if feriado or dia_da_semana >= 5:
                    # Se feriado ou final de semana
                    carga_horaria = 0

                elif dia_da_semana == 4:
                    # Sexta-feira, carga horária de 8 horas
                    carga_horaria = 8

                else:
                    # Demais dias, carga horária de 9 horas
                    carga_horaria = 9

                # Tratamento para feriado no sábado
                if feriado and dia_da_semana == 5:
                    horas_sabado = 4
                    # Varre as datas do intervalo para diminuir as horas do sábado da carga horária
                    for i in range(len(self.datas_intervalo) - 1, -1, -1):
                        # Se não for feriado, tiver carga_horaria e não for sexta a domingo
                        if (
                            not self.datas_intervalo[i][2]
                            and self.datas_intervalo[i][1] > 0
                            and self.datas_intervalo[i][0].weekday() < 4
                        ):
                            self.datas_intervalo[i][1] -= 1
                            horas_sabado -= 1

                        if horas_sabado <= 0:
                            break

                self.datas_intervalo.append([data_atual, carga_horaria, feriado])
                data_atual += timedelta(days=1)

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

    def carga_horaria_dia(self, dia: date) -> int:
        carga_horaria = 0
        for linha in self.datas_intervalo:
            if dia == linha[0]:
                carga_horaria = linha[1]
                break

        return carga_horaria

    def grava_dados_extrato(self):
        """
        Método deve calcular a movimentação de crédito e débido de horas e alimentar a tabela de controle.
        \n
        Recebe como argumentos o período que deve ser considerado para recuperar as informações
        """
        try:
            em_trasacao = False

            zzu = aliased(apontamentos_zzu, name="zzu")
            ae8 = aliased(recursos_ae8, name="ae8")
            sra = aliased(funcionarios_sra, name="sra")
            spc = aliased(apontamentos_spc, name="spc")
            sph = aliased(historico_apontamentos_sph, name="sph")

            # Recupera todos os apontamentos do período para funcionários liderados
            query = (
                Select(
                    ae8.c.AE8_CODFUN,
                    func.cast(zzu.c.ZZU_DATA, Date).label("ZZU_DATA"),
                    func.sum(zzu.c.ZZU_HQUANT).label("ZZU_HQUANT"),
                )
                .join(
                    ae8,
                    and_(
                        ae8.c.D_E_L_E_T_ == " ",
                        ae8.c.AE8_FILIAL == "01",
                        ae8.c.AE8_RECURS == zzu.c.ZZU_RECURS,
                        ae8.c.AE8_CODFUN != " ",
                    ),
                )
                .join(
                    sra,
                    and_(
                        sra.c.D_E_L_E_T_ == " ",
                        sra.c.RA_FILIAL == "01",
                        sra.c.RA_MAT == ae8.c.AE8_CODFUN,
                        sra.c.RA_XLIDER == self.matricula_lider,
                    ),
                )
                .where(
                    zzu.c.D_E_L_E_T_ == " ",
                    zzu.c.ZZU_FILIAL == " ",
                    zzu.c.ZZU_RECURS >= " ",
                    zzu.c.ZZU_CONTRO >= " ",
                    zzu.c.ZZU_DATA.between(
                        self.data_inicial.strftime("%Y%m%d"),
                        self.data_final.strftime("%Y%m%d"),
                    ),
                    zzu.c.ZZU_HORAI >= " ",
                    zzu.c.ZZU_HORAF >= " ",
                    zzu.c.ZZU_SUBTAR >= " ",
                    zzu.c.ZZU_TAREFA.not_like("__MOCO"),
                    zzu.c.ZZU_TAREFA != "AUSENTE",
                )
                .group_by(
                    ae8.c.AE8_CODFUN,
                    zzu.c.ZZU_DATA,
                )
                .order_by(
                    ae8.c.AE8_CODFUN,
                    zzu.c.ZZU_DATA,
                )
            )
            print(
                query.compile(
                    dialect=mssql.dialect(), compile_kwargs={"literal_binds": True}
                )
            )
            resultado_apontamentos = self.db.execute(query).fetchall()
            if resultado_apontamentos:
                # Recupera as aprovações de Banco de Horas para os funcionários no período
                query = (
                    Select(
                        SolicitacoesHorasExtras.matricula,
                        SolicitacoesHorasExtras.data_planejada,
                        func.sum(SolicitacoesHorasExtras.total_horas_planejada).label(
                            "total_horas_planejada"
                        ),
                    )
                    .join(
                        sra,
                        and_(
                            sra.c.D_E_L_E_T_ == " ",
                            sra.c.RA_FILIAL == "01",
                            sra.c.RA_MAT == SolicitacoesHorasExtras.matricula,
                            sra.c.RA_XLIDER == self.matricula_lider,
                        ),
                    )
                    .where(
                        SolicitacoesHorasExtras.status_aprovacao == "2",
                        SolicitacoesHorasExtras.data_planejada.between(
                            self.data_inicial.strftime("%Y-%m-%d"),
                            self.data_final.strftime("%Y-%m-%d"),
                        ),
                    )
                    .group_by(
                        SolicitacoesHorasExtras.matricula,
                        SolicitacoesHorasExtras.data_planejada,
                    )
                )
                resultado_solicitacoes_aprovadas = self.db.execute(query).fetchall()

            # Recupera o consumo das Banco de Horas do sigapon
            query = union_all(
                Select(
                    spc.c.PC_MAT,
                    func.cast(spc.c.PC_DATA, Date).label("PC_DATA"),
                    spc.c.PC_QUANTC,
                    spc.c.PC_QUANTI,
                    spc.c.PC_QTABONO,
                )
                .join(
                    sra,
                    and_(
                        sra.c.D_E_L_E_T_ == " ",
                        sra.c.RA_FILIAL == "01",
                        sra.c.RA_MAT == spc.c.PC_MAT,
                        sra.c.RA_XLIDER == self.matricula_lider,
                    ),
                )
                .where(
                    and_(
                        spc.c.D_E_L_E_T_ == " ",
                        spc.c.PC_FILIAL == "01",
                        spc.c.PC_MAT >= " ",
                        spc.c.PC_PD >= " ",
                        spc.c.PC_DATA.between(
                            self.data_inicial.strftime("%Y%m%d"),
                            self.data_final.strftime("%Y%m%d"),
                        ),
                        spc.c.PC_TPMARCA >= " ",
                        spc.c.PC_CC >= " ",
                        spc.c.PC_DEPTO >= " ",
                        spc.c.PC_POSTO >= " ",
                        spc.c.PC_CODFUNC >= " ",
                        spc.c.PC_ABONO == self.codigo_abono_bh,
                    )
                ),
                Select(
                    sph.c.PH_MAT.label("PC_MAT"),
                    func.cast(sph.c.PH_DATA, Date).label("PC_DATA"),
                    sph.c.PH_QUANTC.label("PC_QUANTC"),
                    sph.c.PH_QUANTI.label("PC_QUANTI"),
                    sph.c.PH_QTABONO.label("PC_QTABONO"),
                )
                .join(
                    sra,
                    and_(
                        sra.c.D_E_L_E_T_ == " ",
                        sra.c.RA_FILIAL == "01",
                        sra.c.RA_MAT == sph.c.PH_MAT,
                        sra.c.RA_XLIDER == self.matricula_lider,
                    ),
                )
                .where(
                    and_(
                        sph.c.D_E_L_E_T_ == " ",
                        sph.c.PH_FILIAL == "01",
                        sph.c.PH_MAT >= " ",
                        sph.c.PH_PD >= " ",
                        sph.c.PH_DATA.between(
                            self.data_inicial.strftime("%Y%m%d"),
                            self.data_final.strftime("%Y%m%d"),
                        ),
                        sph.c.PH_TPMARCA >= " ",
                        sph.c.PH_CC >= " ",
                        sph.c.PH_DEPTO >= " ",
                        sph.c.PH_POSTO >= " ",
                        sph.c.PH_CODFUNC >= " ",
                        sph.c.PH_ABONO == self.codigo_abono_bh,
                    )
                ),
            ).order_by(spc.c.PC_MAT, spc.c.PC_DATA)
            resultado_consumo_bh = self.db.execute(query).fetchall()

            # Monta os dados para o extrato
            registros_para_extrato: List[MovimentosHorasExtras] = []
            for linha in resultado_apontamentos:
                registros_para_extrato.append(MovimentosHorasExtras())
                registros_para_extrato[-1].matricula = linha.AE8_CODFUN
                registros_para_extrato[-1].dia = linha.ZZU_DATA
                registros_para_extrato[-1].tipo_registro = 1  # Registro de crédito
                registros_para_extrato[-1].carga_horaria_dia = self.carga_horaria_dia(
                    linha.ZZU_DATA
                )
                registros_para_extrato[-1].quantidade_horas_apontadas = linha.ZZU_HQUANT

                # Pega a quantidade de horas aprovadas dos registros recuperados
                registros_para_extrato[-1].quantidade_horas_aprovadas = 0
                for solicitacao in resultado_solicitacoes_aprovadas:
                    if solicitacao.data_planejada == registros_para_extrato[-1].dia:
                        registros_para_extrato[-1].quantidade_horas_aprovadas = (
                            solicitacao.total_horas_planejada
                        )

                # Se a quantidade de horas aprovadas for menor que as horas apontadadas, vale as aprovadas
                registros_para_extrato[-1].quantidade_horas_computadas = min(
                    registros_para_extrato[-1].quantidade_horas_aprovadas,
                    registros_para_extrato[-1].quantidade_horas_apontadas,
                )

            for linha in resultado_consumo_bh:
                registros_para_extrato.append(MovimentosHorasExtras())
                registros_para_extrato[-1].matricula = linha.PC_MAT
                registros_para_extrato[-1].dia = linha.PC_DATA
                registros_para_extrato[-1].tipo_registro = 2  # Registro de débito
                registros_para_extrato[-1].carga_horaria_dia = self.carga_horaria_dia(
                    linha.PC_DATA
                )
                registros_para_extrato[-1].quantidade_horas_apontadas = (
                    linha.PC_QUANTI if linha.PC_QUANTI > 0 else linha.PC_QUANTC
                )
                registros_para_extrato[-1].quantidade_horas_aprovadas = linha.PC_QTABONO
                registros_para_extrato[-1].quantidade_horas_computadas = (
                    linha.PC_QTABONO
                )

            # Apaga os dados do extrato para o período
            query = delete(MovimentosHorasExtras).where(
                and_(
                    exists(
                        Select(0).where(
                            sra.c.D_E_L_E_T_ == " ",
                            sra.c.RA_FILIAL == "01",
                            sra.c.RA_MAT == MovimentosHorasExtras.matricula,
                            sra.c.RA_XLIDER == self.matricula_lider,
                        )
                    ),
                    MovimentosHorasExtras.dia.between(
                        self.data_inicial.strftime("%Y-%m-%d"),
                        self.data_final.strftime("%Y-%m-%d"),
                    ),
                ),
            )
            em_trasacao = True
            self.db.execute(query)

            # Insere os novos registros para o período
            em_trasacao = True
            self.db.add_all(registros_para_extrato)
            self.db.flush()

            self.db.commit()

        except HTTPException:
            raise

        except SQLAlchemyError as e:
            if em_trasacao:
                self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro em operação com banco de dados",
                exc_info=True,
                nivel_log=1,
                excecao=e,
            )

        except Exception as e:
            if em_trasacao:
                self.db.rollback()
            log_httpexception_raise(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem="Erro inesperado",
                exc_info=True,
                nivel_log=1,
                excecao=e,
            )

    def regrava_periodo(self) -> bool:
        # Se o periodo de consulta é o último período, recalcula o extrato
        regravar = self.periodo_atual == self.periodo_consulta

        # Se é o último período, verifica se a última gravação ocorreu no tempo determinado
        if regravar:
            sra = aliased(funcionarios_sra, name="sra")
            query = (
                Select(func.max(MovimentosHorasExtras.data_inclusao))
                .select_from(MovimentosHorasExtras)
                .join(
                    sra,
                    and_(
                        sra.c.D_E_L_E_T_ == "",
                        sra.c.RA_FILIAL == "01",
                        sra.c.RA_MAT == MovimentosHorasExtras.matricula,
                        sra.c.RA_XLIDER == self.matricula_lider,
                    ),
                )
            )
            ultima_atualizacao: datetime = self.db.execute(query).scalar()

            regravar = (not ultima_atualizacao) or (
                (datetime.now() - ultima_atualizacao).total_seconds() / 60
            ) > 15

        return regravar

    def recupera_movimentos_extrato(
        self,
        pagina: int,
        registros: int,
        forca_regravacao: bool = False,
        data_adicional_de: date = None,
        data_adicional_ate: date = None,
        matricula_colaborador: str = None,
    ) -> ExtratoHorasExtras:
        extrato_horas_extras: ExtratoHorasExtras = ExtratoHorasExtras(
            codigo_do_periodo=self.periodo_consulta[0],
            data_inicial_movimentos=self.data_inicial,
            data_final_movimentos=self.data_final,
            matricula_do_lider=self.matricula_lider,
        )
        sra = aliased(funcionarios_sra, name="sra")

        if forca_regravacao or self.regrava_periodo():
            self.grava_dados_extrato()

        # Calcula a quantidade de registros confirme as condições de seleção
        condicoes = [
            MovimentosHorasExtras.dia.between(self.data_inicial, self.data_final)
        ]
        # Se informados, insere os filtros adicionais de data
        if data_adicional_de:
            condicoes.append(MovimentosHorasExtras.dia >= data_adicional_de)
        if data_adicional_ate:
            condicoes.append(MovimentosHorasExtras.dia <= data_adicional_ate)
        # Se informado, insere o filtro adicional da matrícula do colaborador
        if matricula_colaborador:
            condicoes.append(MovimentosHorasExtras.matricula == matricula_colaborador)

        query = (
            Select(func.count())
            .select_from(MovimentosHorasExtras)
            .join(
                sra,
                and_(
                    sra.c.D_E_L_E_T_ == " ",
                    sra.c.RA_FILIAL == "01",
                    sra.c.RA_MAT == MovimentosHorasExtras.matricula,
                    sra.c.RA_XLIDER == self.matricula_lider,
                ),
            )
            .where(and_(*condicoes))
        )

        extrato_horas_extras.total_de_registros = self.db.execute(query).scalar_one()
        extrato_horas_extras.registros_por_pagina = registros
        extrato_horas_extras.total_de_paginas = (
            extrato_horas_extras.total_de_registros // registros
        ) + (
            1
            if not extrato_horas_extras.total_de_registros // registros
            == extrato_horas_extras.total_de_registros / registros
            else 0
        )

        # Seleciona os dados para retorno
        campos_extrato = [
            getattr(MovimentosHorasExtras, col)
            for col in MovimentosHorasExtras.__table__.columns.keys()
        ]
        campos_extrato.append(sra.c.RA_NOME.label("nome"))
        query = (
            Select(*campos_extrato)
            .join(
                sra,
                and_(
                    sra.c.D_E_L_E_T_ == " ",
                    sra.c.RA_FILIAL == "01",
                    sra.c.RA_MAT == MovimentosHorasExtras.matricula,
                    sra.c.RA_XLIDER == self.matricula_lider,
                ),
            )
            .where(and_(*condicoes))
            .order_by(MovimentosHorasExtras.matricula, MovimentosHorasExtras.dia)
            .offset((pagina - 1) * registros)
            .limit(registros)
        )

        resultado = self.db.execute(query).fetchall()
        if resultado:
            extrato_horas_extras.pagina = pagina
            extrato_horas_extras.movimentos = [
                MovimentoExtratoHorasExtras.model_validate(reg) for reg in resultado
            ]

        return extrato_horas_extras


@extrato_horas_extras_router.get("/extrato_he/lista_periodos")
def lista_periodos_bd(
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
) -> ListaPeriodosBancoHoras:

    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sem acesso ao endpoint!"
        )

    # Instancia a classe de retorno
    lista_periodos_banco_horas: ListaPeriodosBancoHoras = ListaPeriodosBancoHoras()

    sx5 = aliased(tabelas_genericas_sx5, name="sx5")

    # Prepara o controle de paginação
    query = (
        Select(func.count())
        .select_from(sx5)
        .where(
            and_(
                sx5.c.D_E_L_E_T_ == " ", sx5.c.X5_FILIAL == " ", sx5.c.X5_TABELA == "Z0"
            )
        )
    )
    lista_periodos_banco_horas.total_de_registros = db.execute(query).scalar_one()
    lista_periodos_banco_horas.registros_por_pagina = registros
    lista_periodos_banco_horas.total_de_paginas = (
        lista_periodos_banco_horas.total_de_registros // registros
    ) + (
        1
        if not lista_periodos_banco_horas.total_de_registros // registros
        == lista_periodos_banco_horas.total_de_registros / registros
        else 0
    )

    # Seleciona os registros da tabela de períodos
    query = (
        Select(sx5.c.X5_CHAVE, sx5.c.X5_DESCRI)
        .where(
            and_(
                sx5.c.D_E_L_E_T_ == " ", sx5.c.X5_FILIAL == " ", sx5.c.X5_TABELA == "Z0"
            )
        )
        .order_by(desc(sx5.c.X5_DESCRI))
        .offset((pagina - 1) * registros)
        .limit(registros)
    )
    resultado = db.execute(query).fetchall()

    if resultado:
        lista_periodos_banco_horas.pagina = pagina

    for linha in resultado:
        lista_periodos_banco_horas.periodos.append(
            PeriodoBancoDeHoras(
                codigo_do_periodo=linha.X5_CHAVE,
                data_inicial_periodo=datetime.strptime(
                    linha.X5_DESCRI[:8], "%Y%m%d"
                ).date(),
                data_final_periodo=datetime.strptime(
                    linha.X5_DESCRI.strip()[8:], "%Y%m%d"
                ).date(),
            )
        )

    return lista_periodos_banco_horas


@extrato_horas_extras_router.get("/extrato_he/colaboradores/{matricula_lider}")
def lista_colaboradores_extrato(
    matricula_lider: str,
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
    codigo_periodo: Union[str, None] = Query(
        default=None,
        title="Código do Período",
        description="Código que identifica um período específico para consulta do extrato de Banco de Horas.",
        examples=["000001", "000015"],
    ),
    pagina: int = Query(
        default=1, ge=1, description="Número da página (maior que zero)"
    ),
    registros: int = Query(
        default=10,
        ge=1,
        description="Quantidade de registros por página (maior que zero)",
    ),
) -> ListaColaboradorExtrato:

    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sem acesso ao endpoint!"
        )

    # Instanciamento da classe já calcula os períodos
    extrato_horas_extras = CalculaExtratoHorasExtras(
        db=db, matricula_lider=matricula_lider, codigo_periodo=codigo_periodo
    )

    lista_colaboradores = ListaColaboradorExtrato(
        matricula_do_lider=matricula_lider,
        codigo_do_periodo=extrato_horas_extras.periodo_consulta[0],
        data_inicial_movimentos=extrato_horas_extras.periodo_consulta[1],
        data_final_movimentos=extrato_horas_extras.periodo_consulta[2],
    )

    sra = aliased(funcionarios_sra, name="sra")
    query_base = (
        Select(MovimentosHorasExtras.matricula, sra.c.RA_NOME.label("nome"))
        .join(
            sra,
            and_(
                sra.c.D_E_L_E_T_ == " ",
                sra.c.RA_FILIAL == "01",
                sra.c.RA_MAT == MovimentosHorasExtras.matricula,
                sra.c.RA_XLIDER == matricula_lider,
            ),
        )
        .where(
            and_(
                MovimentosHorasExtras.dia.between(
                    extrato_horas_extras.data_inicial,
                    extrato_horas_extras.data_final,
                )
            )
        )
        .group_by(MovimentosHorasExtras.matricula, sra.c.RA_NOME)
    )
    # Conta os registros para o controle de paginação
    query = Select(func.count()).select_from(query_base.subquery())
    lista_colaboradores.total_de_registros = db.execute(query).scalar_one()
    lista_colaboradores.registros_por_pagina = registros
    lista_colaboradores.total_de_paginas = (
        lista_colaboradores.total_de_registros // registros
    ) + (
        1
        if not lista_colaboradores.total_de_registros // registros
        == lista_colaboradores.total_de_registros / registros
        else 0
    )
    # Executa a seleção de todos os colaboradores do líder que tem lançamento de extrato no período
    query = (
        query_base.order_by(sra.c.RA_NOME)
        .offset((pagina - 1) * registros)
        .limit(registros)
    )

    resultado = db.execute(query).fetchall()
    if resultado:
        lista_colaboradores.pagina = pagina
        lista_colaboradores.colaboradores = [
            ColaboradorExtrato.model_validate(
                {"matricula": linha.matricula, "nome": linha.nome.rstrip()}
            )
            for linha in resultado
        ]
    return lista_colaboradores


@extrato_horas_extras_router.get(
    "/extrato_he/relatorio/{codigo_periodo}/{matricula_lider}"
)
def gera_relatorio_horas_extras(
    codigo_periodo: str,
    matricula_lider: str,
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
    matricula_colaborador: str = Query(
        default=None,
        title="Matrícula do colaborador",
        description="Parâmetro opcional contendo a matrícula de um único colaborador para gerar o relatório.",
        examples=["123456"],
    ),
):
    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sem acesso ao endpoint!"
        )

    relatorio = relatorio_extrato_horas_extras(
        db=db,
        codigo_periodo=codigo_periodo,
        matricula_lider=matricula_lider,
        matricula_colaborador=matricula_colaborador,
    )

    if relatorio:
        return FileResponse(
            relatorio, media_type="application/pdf", filename=relatorio.split("/")[-1]
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dados não localizados para impressão",
        )


@extrato_horas_extras_router.get("/extrato_he/{matricula_lider}")
def recupera_extrato_horas_extras(
    matricula_lider: str,
    payload: dict = Depends(valida_token),
    db: Session = Depends(get_db),
    codigo_periodo: str = Query(
        default=None,
        title="Código do Período",
        description="Código que identifica um período específico para consulta do extrato de Banco de Horas.",
        examples=["000001", "000015"],
    ),
    pagina: int = Query(
        default=1, ge=1, description="Número da página (maior que zero)"
    ),
    registros: int = Query(
        default=10,
        ge=1,
        description="Quantidade de registros por página (maior que zero)",
    ),
    forca_regravacao: bool = Query(
        default=False,
        description="""
                    Se 'true' indica que deve forçar o recálculo do período em aberto, independente de quando ocorreu o último recálculo.\n
                    Se 'false' (default), o recálculo ocorre a cada 15 minutos, sempre se o período consultado for o em aberto.
                    """,
        examples=["true", "false"],
    ),
    data_de: date = Query(
        default=None, description="Filtro adicional de data dentro do período."
    ),
    data_ate: date = Query(
        default=None, description="Filtro adicional de data dentro do período."
    ),
    matricula_colaborador: str = Query(
        default=None,
        description="Matrícula do colaborador para filtro de movimentos.",
        examples=["123456"],
    ),
) -> ExtratoHorasExtras:

    # Validar se tem acesso pelo token
    if not valida_acesso_endpoint(db, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sem acesso ao endpoint!"
        )

    # Instanciamento da classe
    extrato_horas_extras = CalculaExtratoHorasExtras(
        db=db, matricula_lider=matricula_lider, codigo_periodo=codigo_periodo
    )

    return extrato_horas_extras.recupera_movimentos_extrato(
        pagina=pagina,
        registros=registros,
        forca_regravacao=forca_regravacao,
        data_adicional_de=data_de,
        data_adicional_ate=data_ate,
        matricula_colaborador=matricula_colaborador,
    )
