from datetime import date, datetime
from decimal import Decimal
import os
from fpdf import FPDF
from sqlalchemy import Select, and_
from sqlalchemy.orm import Session, aliased
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from src.mrb.common.lib.dec_to_str import dec_to_str
from src.mrb.rh.interfaces.extrato_horas_extras_view import TIPO_MOVIMENTO
from src.mrb.rh.schemas.schema_extrato_horas_extras import MovimentoExtratoHorasExtras
from src.mrb.rh.models.model_movimentos_horas_extras import MovimentosHorasExtras
from src.mrb.common.config import Environment
from src.mrb.rh.models.model_funcionarios_sra import funcionarios_sra
from src.mrb.common.models.model_tabelas_genericas_sx5 import tabelas_genericas_sx5


def relatorio_extrato_horas_extras(
    db: Session,
    codigo_periodo: str,
    matricula_lider: str,
    matricula_colaborador: str = None,
) -> str | None:
    nome_arquivo: str = None
    data_emissao: str = datetime.now().strftime("%d/%m/%Y %H:%M")
    limpa_pasta_trabalho()

    # Seleção dos dados do período
    periodo: list[date] = recupera_dados_periodo(db=db, codigo_periodo=codigo_periodo)

    # Seleção dos dados para impressão
    dados_extrato: list[MovimentoExtratoHorasExtras] = recupera_dados_extrato(
        db=db,
        data_inicial=periodo[0],
        data_final=periodo[1],
        matricula_lider=matricula_lider,
        matricula_colaborador=matricula_colaborador,
    )

    if dados_extrato:
        pagina_atual: int = 1
        imprime_cabecalho: bool = True
        saldo_horas: Decimal = Decimal("0.00")
        total_de_registros: int = len(dados_extrato)

        nome_arquivo = os.path.join(
            Environment.CAMINHO_RELATORIOS,
            f"extrato_he_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
        pdf = FPDF()
        limite_inferior = pdf.h - pdf.b_margin
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()

        for n, registro in enumerate(dados_extrato):
            muda_pagina: bool = False
            if imprime_cabecalho:
                imprime_cabecalho = False
                imprime_cabecalho_rodape(
                    pdf=pdf,
                    matricula=registro.matricula,
                    nome=registro.nome,
                    periodo=periodo,
                    pagina_atual=pagina_atual,
                    limite_inferior=limite_inferior,
                    data_emissao=data_emissao,
                )

            saldo_horas += registro.quantidade_horas_computadas * (
                1 if registro.tipo_registro == 1 else -1
            )

            pdf.set_font("Arial", "", 10)
            pdf.cell(20, 5, registro.dia.strftime("%d/%m/%Y"), align="C")
            pdf.cell(25, 5, dec_to_str(registro.carga_horaria_dia), align="R")
            pdf.cell(20, 5, TIPO_MOVIMENTO[registro.tipo_registro])
            pdf.cell(33, 5, dec_to_str(registro.quantidade_horas_apontadas), align="R")
            pdf.cell(33, 5, dec_to_str(registro.quantidade_horas_aprovadas), align="R")
            pdf.cell(33, 5, dec_to_str(registro.quantidade_horas_computadas), align="R")
            pdf.cell(28, 5, dec_to_str(saldo_horas), align="R")
            pdf.ln()

            # Se é o último registro ou mudou o colaborador, totaliza
            if (
                n == total_de_registros - 1
                or not registro.matricula == dados_extrato[n + 1].matricula
            ):
                pdf.ln()
                pdf.set_x(0)
                pdf.cell(
                    0,
                    5,
                    f"Saldo para o colaborador {registro.nome.strip()}: {dec_to_str(saldo_horas)}",
                    align="R",
                )
                pdf.ln()
                pdf.ln()
                saldo_horas = 0
                muda_pagina = True

            if pdf.get_y() > limite_inferior - 10 or muda_pagina:
                pagina_atual += 1
                pdf.add_page()
                imprime_cabecalho = True

        pdf.output(nome_arquivo)

    return nome_arquivo


def imprime_cabecalho_rodape(
    pdf: FPDF,
    matricula: str,
    nome: str,
    periodo: list[date],
    pagina_atual: int,
    limite_inferior: float,
    data_emissao: str,
):
    pdf.image(Environment.LOGOTIPO_RELATORIOS, x=10, y=10, w=20, h=0)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 10, data_emissao, align="R")
    pdf.set_x(0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Extrato de Banco de Horas", 0, 1, align="C")
    pdf.set_x(0)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(
        0,
        10,
        f"Periodo: {periodo[0].strftime('%d/%m/%Y')} a {periodo[1].strftime('%d/%m/%Y')}",
        align="C",
        ln=1,
    )
    pdf.cell(25, 10, "Colaborador:")
    pdf.set_font("Arial", "", 10)
    pdf.cell(
        10,
        10,
        f"({matricula.strip()}) {nome.strip()}",
        ln=1,
    )

    # Imprime o rodapé
    backup_linha = pdf.get_y()
    pdf.set_y(limite_inferior)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 10, f"Página {pagina_atual}", 0, 1, align="C")
    pdf.set_y(backup_linha)

    # Imprime o cabeçalho das colunas
    pdf.set_font("Arial", "B", 10)
    pdf.cell(20, 5, "Data", align="C")
    pdf.cell(25, 5, "Carga Horária", align="C")
    pdf.cell(20, 5, "Tipo")
    pdf.cell(33, 5, "Horas Apontadas", align="C")
    pdf.cell(33, 5, "Horas Aprovadas", align="C")
    pdf.cell(33, 5, "Horas para Banco", align="C")
    pdf.cell(28, 5, "Saldo", align="C")
    pdf.ln()


def recupera_dados_periodo(db: Session, codigo_periodo: str) -> list[date]:
    sx5 = aliased(tabelas_genericas_sx5, name="sx5")
    query = Select(sx5.c.X5_CHAVE, sx5.c.X5_DESCRI).where(
        sx5.c.D_E_L_E_T_ == " ",
        sx5.c.X5_FILIAL == " ",
        sx5.c.X5_TABELA == "Z0",
        sx5.c.X5_CHAVE == codigo_periodo,
    )
    resultado = db.execute(query).fetchone()
    if resultado:
        periodo = [
            datetime.strptime(resultado.X5_DESCRI[:8], "%Y%m%d").date(),
            datetime.strptime(resultado.X5_DESCRI.strip()[8:], "%Y%m%d").date(),
        ]

    else:
        periodo = []

    return periodo


def recupera_dados_extrato(
    db: Session,
    data_inicial: date,
    data_final: date,
    matricula_lider: str,
    matricula_colaborador: str = None,
) -> list[MovimentoExtratoHorasExtras]:
    campos_extrato = [
        getattr(MovimentosHorasExtras, col)
        for col in MovimentosHorasExtras.__table__.columns.keys()
    ]
    sra = aliased(funcionarios_sra, name="sra")
    campos_extrato.append(sra.c.RA_NOME.label("nome"))

    condicoes = [MovimentosHorasExtras.dia.between(data_inicial, data_final)]
    if matricula_colaborador:
        condicoes.append(MovimentosHorasExtras.matricula == matricula_colaborador)

    query = (
        Select(*campos_extrato)
        .join(
            sra,
            and_(
                sra.c.D_E_L_E_T_ == " ",
                sra.c.RA_FILIAL == "01",
                sra.c.RA_MAT == MovimentosHorasExtras.matricula,
                sra.c.RA_XLIDER == matricula_lider,
            ),
        )
        .where(and_(*condicoes))
    ).order_by(
        sra.c.RA_NOME, MovimentosHorasExtras.dia, MovimentosHorasExtras.tipo_registro
    )
    resultado = db.execute(query).fetchall()
    if resultado:
        retorno = [MovimentoExtratoHorasExtras.model_validate(reg) for reg in resultado]

    else:
        retorno = []

    return retorno


def limpa_pasta_trabalho():
    data_referencia = datetime.now().date()

    for arquivo in os.listdir(Environment.CAMINHO_RELATORIOS):
        if (
            os.path.isfile(os.path.join(Environment.CAMINHO_RELATORIOS, arquivo))
            and arquivo.startswith("extrato_he_")
            and datetime.fromtimestamp(
                os.stat(os.path.join(Environment.CAMINHO_RELATORIOS, arquivo)).st_ctime
            ).date()
            != data_referencia
        ):
            os.remove(os.path.join(Environment.CAMINHO_RELATORIOS, arquivo))
