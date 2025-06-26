import base64
from datetime import datetime
import uuid
import flet as ft

from src.mrb.common.lib.hdec_to_hhmm import hdec_to_hhmm
from src.mrb.common.security.gera_token_downloads import gera_token_downloads
from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.common.lib.aviso import Aviso
from src.mrb.common.interfaces.valida_data_digitada import valida_data_digitada
from src.mrb.common.interfaces.preenche_data import preenche_data
from src.mrb.rh.schemas.schema_extrato_horas_extras import (
    ExtratoHorasExtras as SchemaExtrato,
)
from src.mrb.rh.schemas.schema_colaboradores_extrato import ListaColaboradorExtrato
from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.rh.schemas.schema_periodos_banco_horas import ListaPeriodosBancoHoras
from src.mrb.rh.interfaces.comunica_api_horas_extras import ComunicaApiHorasExtras
from src.mrb.common.interfaces.paginacao import Paginacao
from src.mrb.common.interfaces.botoes_menu_principal import BotoesMenuPrincipal
from src.mrb.common.interfaces.navigation_bar import NavigationBar

TIPO_MOVIMENTO = {1: "Crédito", 2: "Débito", 3: "Encerramento"}


class ExtratoHorasExtras:

    def __init__(
        self,
        page: ft.Page,
        navigation_bar: NavigationBar,
        botoes_menu_principal: BotoesMenuPrincipal,
    ):
        self.page = page
        self.navigation_bar = navigation_bar
        self.botoes_menu_principal = botoes_menu_principal

        self.botao_gerar_pdf = ft.IconButton(
            icon=ft.Icons.PRINT_OUTLINED,
            tooltip="Gerar relatório",
            on_click=lambda _: self.gerar_relatorio_horas_extras(),
        )

        # Filtros
        self.botao_limpar_filtros = ft.IconButton(
            icon=ft.Icons.FILTER_ALT_OFF_OUTLINED,
            tooltip="Limpar filtros",
            on_click=lambda _: self.limpar_filtros(),
            disabled=True,
        )
        self.seletor_periodos = ft.Dropdown(
            width=250,
            height=40,
            label="Período Banco de Horas",
            dense=True,
            options=[],
            data={"pagina_atual": 0, "total_paginas": None, "chave_selecionada": None},
            on_change=lambda e: self.on_change_periodo(e.control),
        )
        # A primeira opção do seletor de colaborador serve para limpar a seleção
        self.seletor_colaborador = ft.Dropdown(
            width=370,
            height=40,
            label="Filtrar colaborador",
            dense=True,
            options=[
                ft.dropdown.Option(
                    "-", "Limpar seleção", data=None, text_style=ft.TextStyle(size=12)
                )
            ],
            data={"pagina_atual": 0, "total_paginas": None},
            on_change=lambda e: self.on_change_colaborador(e.control),
        )
        self.campo_data_de = ft.TextField(
            dense=True,
            width=120,
            hint_text="  /  /    ",
            data="",
            text_size=14,
            on_change=lambda e: preenche_data(
                evento=e, se_data_valida=self.recupera_extrato
            ),
            on_blur=lambda e: valida_data_digitada(
                evento=e, se_data_valida=self.recupera_extrato
            ),
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^[0-9/]*$", replacement_string=""
            ),
        )
        self.campo_data_ate = ft.TextField(
            dense=True,
            width=120,
            hint_text="  /  /    ",
            data="",
            text_size=14,
            on_change=lambda e: preenche_data(
                evento=e, se_data_valida=self.recupera_extrato
            ),
            on_blur=lambda e: valida_data_digitada(
                evento=e, se_data_valida=self.recupera_extrato
            ),
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^[0-9/]*$", replacement_string=""
            ),
        )
        self.browse_movimentos = ft.DataTable(
            expand=True,
            divider_thickness=0.4,
            sort_ascending=True,
            columns=[
                ft.DataColumn(ft.Text("Matrícula", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Nome", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Carga Horária", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Tipo Movimento", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Hrs Apontadas", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Hrs Aprovadas", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Hrs Computadas", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        # Browse extrato
        self.paginacao = Paginacao(lambda _: self.recupera_extrato())

    def limpar_filtros(self, recupera_extrato: bool = True):
        self.campo_data_de.value = ""
        self.campo_data_de.data = ""
        self.campo_data_ate.value = ""
        self.campo_data_ate.data = ""
        self.seletor_colaborador.value = ""
        self.botao_limpar_filtros.disabled = True
        if recupera_extrato:
            self.recupera_extrato()

    def on_change_colaborador(self, seletor_colaborador: ft.Dropdown):
        if seletor_colaborador.value == "-":
            seletor_colaborador.value = None
            seletor_colaborador.update()

        self.recupera_extrato()

    def on_change_periodo(self, seletor_periodos: ft.Dropdown):
        # Se a chave selecionada for "...", recupera mais períodos, restaura a chave anterior e faz update
        if seletor_periodos.value == "...":
            self.recupera_periodos_banco_horas()
            seletor_periodos.value = seletor_periodos.data["chave_selecionada"]
            seletor_periodos.update()

        else:
            seletor_periodos.data["chave_selecionada"] = seletor_periodos.value
            self.recupera_extrato()

            # Se trocou o período, limpa os filtros e reinicia os dados da lista de colaboradores
            self.limpar_filtros(recupera_extrato=False)
            self.seletor_colaborador.data = {"pagina_atual": 0, "total_paginas": None}
            self.recupera_colaboradores_extrato(self.seletor_periodos.value)

    def recupera_extrato(self):
        matricula_lider = AuthSession(self.page).user_data()["dados_cadastro_recursos"][
            "matricula"
        ]

        # Informa a página de destino da requisição
        parametros_requisicao = {
            "pagina": (
                self.paginacao.pagina_atual if self.paginacao.pagina_atual > 0 else 1
            ),
            "codigo_periodo": self.seletor_periodos.value,
        }

        # Informa o período de datas para filtro (dentro do período de banco de horas)
        if len(self.campo_data_de.data) == 10:
            parametros_requisicao["data_de"] = datetime.strptime(
                self.campo_data_de.data, "%d/%m/%Y"
            )
        if len(self.campo_data_ate.data) == 10:
            parametros_requisicao["data_ate"] = datetime.strptime(
                self.campo_data_ate.data, "%d/%m/%Y"
            )
        if self.seletor_colaborador.value:
            parametros_requisicao["matricula_colaborador"] = (
                self.seletor_colaborador.value
            )

        retorno_extrato = ComunicaApiHorasExtras(self.page).recupera_solicitacoes(
            end_point=f"/extrato_he/{matricula_lider}",
            parametros_requisicao=parametros_requisicao,
        )
        if retorno_extrato:
            if len(parametros_requisicao) > 2:
                self.botao_limpar_filtros.disabled = False

            extrato_recuperado = SchemaExtrato(**retorno_extrato)
            self.browse_movimentos.rows.clear()
            self.paginacao.set_total_paginas(extrato_recuperado.total_de_paginas)
            for movimento in extrato_recuperado.movimentos:
                self.browse_movimentos.rows.append(
                    ft.DataRow(
                        data=movimento,
                        cells=[
                            ft.DataCell(ft.Text(movimento.matricula)),
                            ft.DataCell(ft.Text(movimento.nome.rstrip())),
                            ft.DataCell(ft.Text(movimento.dia.strftime("%d/%m/%Y"))),
                            ft.DataCell(
                                ft.Text(hdec_to_hhmm(movimento.carga_horaria_dia))
                            ),
                            ft.DataCell(
                                ft.Text(TIPO_MOVIMENTO[movimento.tipo_registro])
                            ),
                            ft.DataCell(
                                ft.Text(
                                    hdec_to_hhmm(movimento.quantidade_horas_apontadas)
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    hdec_to_hhmm(movimento.quantidade_horas_aprovadas)
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    hdec_to_hhmm(movimento.quantidade_horas_computadas)
                                )
                            ),
                        ],
                    )
                )

            self.page.update()

    def recupera_colaboradores_extrato(self, codigo_periodo: str = None):
        matricula_lider = AuthSession(self.page).user_data()["dados_cadastro_recursos"][
            "matricula"
        ]
        if (
            not self.seletor_colaborador.data["total_paginas"]
            or self.seletor_colaborador.data["pagina_atual"]
            < self.seletor_colaborador.data["total_paginas"]
        ):
            self.seletor_colaborador.data["pagina_atual"] += 1
            parametros_requisicao = {
                "pagina": self.seletor_colaborador.data["pagina_atual"],
                "registros": 100,
            }
            if codigo_periodo:
                parametros_requisicao["codigo_periodo"] = codigo_periodo

            retorno_colaboradores = ComunicaApiHorasExtras(
                self.page
            ).recupera_solicitacoes(
                end_point=f"/extrato_he/colaboradores/{matricula_lider}",
                parametros_requisicao=parametros_requisicao,
            )

            if retorno_colaboradores:
                colaboradores_recuperados = ListaColaboradorExtrato(
                    **retorno_colaboradores
                )
                self.seletor_colaborador.data["total_paginas"] = (
                    colaboradores_recuperados.total_de_paginas
                )
                # Adiciona os colaboradores recuperados nas opções
                for colaborador in colaboradores_recuperados.colaboradores:
                    self.seletor_colaborador.options.append(
                        ft.dropdown.Option(
                            colaborador.matricula,
                            f"({colaborador.matricula.strip()}) {colaborador.nome}",
                            data=colaborador,
                            text_style=ft.TextStyle(size=12),
                        )
                    )

                self.page.update()

    def recupera_periodos_banco_horas(self):
        # Incrementa o controle de paginação do browse se a página atual for menor que o total de páginas
        if (
            not self.seletor_periodos.data["total_paginas"]
            or self.seletor_periodos.data["pagina_atual"]
            < self.seletor_periodos.data["total_paginas"]
        ):
            self.seletor_periodos.data["pagina_atual"] += 1
            retorno_periodos = ComunicaApiHorasExtras(self.page).recupera_solicitacoes(
                end_point="/extrato_he/lista_periodos",
                parametros_requisicao={
                    "pagina": self.seletor_periodos.data["pagina_atual"]
                },
            )
            # Remove o elemento que carrega mais elementos
            if (
                len(self.seletor_periodos.options) > 0
                and self.seletor_periodos.options[-1].key == "..."
            ):
                del self.seletor_periodos.options

            if retorno_periodos:
                periodos_recuperados = ListaPeriodosBancoHoras(**retorno_periodos)
                self.seletor_periodos.data["total_paginas"] = (
                    periodos_recuperados.total_de_paginas
                )
                # Adiciona as linhas recuperadas no box
                for periodo in periodos_recuperados.periodos:
                    self.seletor_periodos.options.append(
                        ft.dropdown.Option(
                            periodo.codigo_do_periodo,
                            periodo.data_inicial_periodo.strftime("%d/%m/%Y")
                            + " - "
                            + periodo.data_final_periodo.strftime("%d/%m/%Y"),
                            data=periodo,
                            text_style=ft.TextStyle(size=12),
                        )
                    )

                # Caso nada tenha sido selecionado, força o primeiro período (atual)
                if not self.seletor_periodos.value:
                    self.seletor_periodos.value = periodos_recuperados.periodos[
                        0
                    ].codigo_do_periodo
                    self.seletor_periodos.data["chave_selecionada"] = (
                        self.seletor_periodos.value
                    )

                if (
                    self.seletor_periodos.data["total_paginas"]
                    > self.seletor_periodos.data["pagina_atual"]
                ):
                    # Adiciona o elemento que carrega mais elementos
                    self.seletor_periodos.options.append(
                        ft.dropdown.Option(
                            "...",
                            "Carregar mais períodos...",
                            text_style=ft.TextStyle(size=12),
                        )
                    )

                self.page.update()

            elif self.seletor_periodos.data["total_paginas"] > 0:
                self.seletor_periodos.data["total_paginas"] -= 1

    def get_extrato_horas_extras(self) -> ft.View:
        area_de_filtros = ft.Container(
            expand=10,
            border_radius=5,
            padding=10,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row(
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.botao_gerar_pdf,
                            self.seletor_periodos,
                            ft.VerticalDivider(color=ft.Colors.TRANSPARENT),
                            self.botao_limpar_filtros,
                            self.seletor_colaborador,
                            ft.VerticalDivider(color=ft.Colors.TRANSPARENT),
                            ft.Text("Data de:"),
                            self.campo_data_de,
                            ft.Text("Até:"),
                            self.campo_data_ate,
                        ],
                    ),
                ],
            ),
        )

        area_de_dados = ft.Container(
            expand=85,
            border_radius=5,
            padding=5,
            content=ft.Column(
                expand=True,
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=20,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[self.paginacao.get_paginacao()],
                            )
                        ],
                    ),
                    ft.ListView(
                        expand=True,
                        controls=[
                            ft.Row(
                                expand=True,
                                scroll=ft.ScrollMode.ADAPTIVE,
                                controls=[self.browse_movimentos],
                            )
                        ],
                    ),
                ],
            ),
        )

        conteudo_extrato = ft.Container(
            padding=0,
            border_radius=5,
            expand=True,
            content=ft.Column(controls=[area_de_filtros, ft.Divider(), area_de_dados]),
        )

        return ft.View(
            route="/extrato_he",
            padding=0,
            controls=[
                self.navigation_bar.get_navigation_bar("Consulta ao Banco de Horas"),
                ft.Row(
                    controls=[
                        self.botoes_menu_principal.get_botoes_menu_principal(),
                        ft.Container(
                            content=conteudo_extrato,
                            alignment=ft.alignment.center,
                            expand=True,
                            padding=0,
                            margin=0,
                        ),
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
        )

    def gerar_relatorio_horas_extras(self):

        def salvar_pdf(e: ft.FilePickerResultEvent, content, page: ft.Page):
            """Salvar o PDF no local escolhido pelo usuário"""
            try:
                if e.path:
                    with open(e.path, "wb") as f:
                        f.write(content)

            except Exception as erro:
                Aviso(
                    self.page,
                    content=f"Falha ao salvar o arquivo: {erro}",
                    title="Atenção",
                    actions=["Ok"],
                ).exibir()

        if not self.seletor_colaborador.value:
            Aviso(
                self.page,
                content="Selecione um colaborador específico para emitir o relatório!",
                title="Atenção",
                actions=["Ok"],
            ).exibir()

        else:
            matricula_lider = AuthSession(self.page).user_data()[
                "dados_cadastro_recursos"
            ]["matricula"]
            codigo_usuario = AuthSession(self.page).user_data()["id_usuario"]
            id_requisicao = str(uuid.uuid4())
            token_relatorio = gera_token_downloads(
                id_requisicao=id_requisicao, codigo_usuario=codigo_usuario
            )
            retorno_relatorio = ComunicaApiHorasExtras(self.page).recupera_solicitacoes(
                end_point=f"/extrato_he/relatorio/{self.seletor_periodos.value}/{matricula_lider}",
                parametros_requisicao={
                    "matricula_colaborador": self.seletor_colaborador.value,
                    "nome_arquivo_resultado": id_requisicao,
                },
            )
            if retorno_relatorio:
                if self.page.web:
                    url_relatorio = f"http://{Environment.SERVER_IP}:{ApiConfiguration.rh.PORT}/download/"
                    url_relatorio += f"{base64.urlsafe_b64encode(Environment.CAMINHO_RELATORIOS.encode()).decode()}"
                    url_relatorio += f"?id_usuario={codigo_usuario}"
                    url_relatorio += f"&token_arquivo={token_relatorio}"
                    url_relatorio += f"&extencao_arquivo=pdf"
                    self.page.launch_url(url_relatorio)

                else:
                    # Criar um seletor de arquivos para o usuário escolher onde salvar
                    file_picker = ft.FilePicker(
                        on_result=lambda e: salvar_pdf(e, retorno_relatorio, self.page)
                    )
                    self.page.overlay.append(file_picker)
                    self.page.update()

                    # Abrir o seletor para salvar arquivo
                    file_picker.save_file(
                        file_type=[ft.FilePickerFileType.CUSTOM],
                        allowed_extensions=["pdf"],
                        dialog_title="Salvar relatório de Banco de Horas",
                        initial_directory="C:\\Users\\Public\\Documents",
                        file_name=f"relatorio_extrato_he_{self.seletor_periodos.value}_{self.seletor_colaborador.value.strip()}.pdf",
                    )
