from datetime import datetime
import flet as ft

from src.mrb.common.interfaces.valida_data_digitada import valida_data_digitada
from src.mrb.common.interfaces.preenche_data import preenche_data
from src.mrb.rh.interfaces.comunica_api_horas_extras import ComunicaApiHorasExtras
from src.mrb.rh.interfaces.periodo_apontamento import PeriodoApontamento
from src.mrb.common.interfaces.paginacao import Paginacao
from src.mrb.common.lib.aviso import Aviso
from src.mrb.rh.interfaces.solicitacao_horas_extras_view import STATUS_APROVACAO
from src.mrb.common.lib.iso_to_date import iso_to_date
from src.mrb.common.config import ApiConfiguration
from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.interfaces.botoes_menu_principal import BotoesMenuPrincipal
from src.mrb.common.interfaces.navigation_bar import NavigationBar


class LiberacaoHorasExtras:
    """
    Classe de montagem e controle da view de liberação de horas extras.
    """

    def __init__(
        self,
        page: ft.Page,
        navigation_bar: NavigationBar,
        botoes_menu_principal: BotoesMenuPrincipal,
    ) -> None:
        self.page = page
        self.navigation_bar = navigation_bar
        self.botoes_menu_principal = botoes_menu_principal
        self.paginacao = Paginacao(lambda _: self.carrega_liberacoes())
        self.periodo_apontamento = PeriodoApontamento()

        # Componentes do grid de registros
        self.browse_liberacoes = ft.DataTable(
            expand=True,
            divider_thickness=0.4,
            sort_ascending=True,
            columns=[
                ft.DataColumn(ft.Text("Ações", weight="bold")),
                ft.DataColumn(ft.Text("Id", weight="bold")),
                ft.DataColumn(ft.Text("Matricula", weight="bold")),
                ft.DataColumn(ft.Text("Nome", weight="bold")),
                ft.DataColumn(ft.Text("Dt. Planejada", weight="bold")),
                ft.DataColumn(ft.Text("Qtd. Horas", weight="bold")),
                ft.DataColumn(ft.Text("Dt. Solicitação", weight="bold")),
                ft.DataColumn(ft.Text("Motivo", weight="bold")),
                ft.DataColumn(ft.Text("Status Aprovação", weight="bold")),
                ft.DataColumn(ft.Text("Dt. Aprovação", weight="bold")),
                ft.DataColumn(ft.Text("Matr. Aprovador", weight="bold")),
                ft.DataColumn(ft.Text("Comentário", weight="bold")),
            ],
            rows=[],
        )

        # Componentes dos paineis
        self.texto_periodo_em_vigor = ft.Text("De   /  /     a   /  /    ")
        self.cartao_periodo_apontamento = ft.Card(
            elevation=1.5,
            animate_scale=200,
            surface_tint_color=ft.Colors.INVERSE_PRIMARY,
            content=ft.Container(
                padding=10,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "Período de Apontamento em Vigor",
                                    text_align=ft.TextAlign.CENTER,
                                    expand=True,
                                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                self.texto_periodo_em_vigor,
                            ],
                        ),
                    ]
                ),
            ),
        )
        self.coluna_painel_visualizacao = ft.Column(scroll=ft.ScrollMode.ADAPTIVE)
        self.cartao_painel_visualizacao = ft.Card(
            elevation=1.5,
            animate_scale=200,
            surface_tint_color=ft.Colors.INVERSE_PRIMARY,
            content=ft.Container(padding=10, content=self.coluna_painel_visualizacao),
            visible=False,
        )

        # Componentes do painel de liberação
        self.titulo_painel_liberacao = ft.Text(
            "",
            text_align=ft.TextAlign.CENTER,
            expand=True,
            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
        )
        self.matricula_painel_liberacao = ft.Text("")
        self.nome_painel_liberacao = ft.Text("")
        self.data_planejada_painel_liberacao = ft.Text("")
        self.quantidade_horas_painel_liberacao = ft.Text("")
        self.data_solicitacao_painel_liberacao = ft.Text("")
        self.motivo_painel_liberacao = ft.Text("", expand=True)
        self.status_painel_liberacao = ft.Text("")
        self.data_aprovacao_painel_liberacao = ft.Text("")
        self.matricula_aprovador_painel_liberacao = ft.Text("")
        self.campo_comentarios = ft.TextField(
            dense=True,
            expand=True,
            bgcolor=ft.Colors.WHITE,
            tooltip="Comente a ação de aprovar ou reprovar a solicitação",
            max_length=250,
            multiline=True,
            on_change=lambda e: self.on_change_comentario(e),
            text_size=14,
            max_lines=3,
        )
        self.botao_salvar = ft.IconButton(
            icon=ft.Icons.CHECK_CIRCLE_OUTLINE_OUTLINED,
            icon_color=ft.Colors.GREEN,
            icon_size=40,
            tooltip="Salvar",
            on_click=lambda e: self.salvar_edicao(
                liberar=e.control.data[0], dados_liberacao=e.control.data[1]
            ),
        )
        self.coluna_painel_liberacao = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[self.titulo_painel_liberacao],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Matrícula:", theme_style=ft.TextThemeStyle.LABEL_LARGE
                        ),
                        self.matricula_painel_liberacao,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("Nome:", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                        self.nome_painel_liberacao,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Data Planejada:", theme_style=ft.TextThemeStyle.LABEL_LARGE
                        ),
                        self.data_planejada_painel_liberacao,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Qtd. Horas Planejadas:",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        self.quantidade_horas_painel_liberacao,
                    ],
                ),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Data da Solicitação:",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        self.data_solicitacao_painel_liberacao,
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Motivo: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        self.motivo_painel_liberacao,
                    ],
                ),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Status da Aprovação:",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        self.status_painel_liberacao,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Data da Aprovação:",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        self.data_aprovacao_painel_liberacao,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Matrícula Aprovador:",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        self.matricula_aprovador_painel_liberacao,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Comentários:", theme_style=ft.TextThemeStyle.LABEL_LARGE
                        )
                    ]
                ),
                ft.Row(controls=[self.campo_comentarios]),
                ft.Divider(),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        self.botao_salvar,
                        ft.IconButton(
                            icon=ft.Icons.CANCEL_OUTLINED,
                            icon_color=ft.Colors.RED,
                            icon_size=40,
                            tooltip="Cancelar",
                            on_click=lambda _: self.cancelar_edicao(),
                        ),
                    ],
                ),
            ],
        )
        self.cartao_painel_edicao = ft.Card(
            elevation=1.5,
            animate_scale=200,
            surface_tint_color=ft.Colors.INVERSE_PRIMARY,
            content=ft.Container(padding=10, content=self.coluna_painel_liberacao),
            visible=False,
        )

        # Componentes da filtragem de registros
        self.botao_limpa_filtros = ft.IconButton(
            icon=ft.Icons.FILTER_ALT_OFF_OUTLINED,
            tooltip="Limpar filtros",
            on_click=lambda _: self.limpar_filtros(),
            disabled=True,
        )
        self.texto_data_de = ft.TextField(
            dense=True,
            on_change=lambda e: preenche_data(
                evento=e, se_data_valida=self.carrega_liberacoes
            ),
            on_blur=lambda e: valida_data_digitada(
                evento=e, se_data_valida=self.carrega_liberacoes
            ),
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^[0-9/]*$", replacement_string=""
            ),
            width=120,
            hint_text="  /  /    ",
            data="",
            text_size=14,
        )
        self.texto_data_ate = ft.TextField(
            dense=True,
            on_change=lambda e: preenche_data(
                evento=e, se_data_valida=self.carrega_liberacoes
            ),
            on_blur=lambda e: valida_data_digitada(
                evento=e, se_data_valida=self.carrega_liberacoes
            ),
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^[0-9/]*$", replacement_string=""
            ),
            width=120,
            hint_text="  /  /    ",
            data="",
            text_size=14,
        )
        self.seletor_aguardando_aprovacao = ft.Switch(
            label="Apenas aguardando aprovação",
            value=False,
            on_change=lambda _: self.carrega_liberacoes(),
            height=40,
        )

    def get_liberacao_horas_extras(self) -> ft.View:
        """
        Montagem e retorno da view de controle
        """
        conteudo_liberacao = ft.Container(
            padding=0,
            border_radius=5,
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Container(
                                    expand=5,
                                    border_radius=5,
                                    padding=15,
                                    content=ft.Column(
                                        expand=True,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=20,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Row(
                                                spacing=20,
                                                controls=[
                                                    self.botao_limpa_filtros,
                                                    ft.Text("Data Planejada de:"),
                                                    self.texto_data_de,
                                                    ft.Text("Até:"),
                                                    self.texto_data_ate,
                                                    self.seletor_aguardando_aprovacao,
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            ),
                                            ft.Row(
                                                spacing=20,
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                controls=[
                                                    self.paginacao.get_paginacao()
                                                ],
                                            ),
                                            ft.ListView(
                                                expand=True,
                                                controls=[
                                                    ft.Row(
                                                        controls=[
                                                            self.browse_liberacoes
                                                        ],
                                                        expand=True,
                                                        scroll=ft.ScrollMode.ADAPTIVE,
                                                    )
                                                ],
                                            ),
                                        ],
                                    ),
                                ),
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    expand=2,
                                    border_radius=5,
                                    padding=15,
                                    content=ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            self.cartao_periodo_apontamento,
                                            self.cartao_painel_visualizacao,
                                            self.cartao_painel_edicao,
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    )
                ]
            ),
        )
        return ft.View(
            route="/aprova_he",
            padding=0,
            controls=[
                self.navigation_bar.get_navigation_bar(
                    "Aprovação de Solicitações de Horas Extras"
                ),
                ft.Row(
                    controls=[
                        self.botoes_menu_principal.get_botoes_menu_principal(),
                        ft.Container(
                            content=conteudo_liberacao,
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

    def carrega_liberacoes(self):
        """
        Monta os parâmetros para requisição da lista de liberações de acordo com o filtro e
        alimenta as linhas do browse da tela principal de liberação.
        """
        auth_session = AuthSession()
        pagina_destino = (
            self.paginacao.pagina_atual if self.paginacao.pagina_atual > 0 else 1
        )
        parametros_requisicao = {
            "matricula_aprovador": auth_session.user_data["dados_cadastro_recursos"][
                "matricula"
            ],
            "pagina": str(pagina_destino),
        }

        if self.seletor_aguardando_aprovacao.value:
            parametros_requisicao["status_aprovacao"] = "1"

        if len(self.texto_data_de.data) == 10:
            parametros_requisicao["data_de"] = datetime.strptime(
                self.texto_data_de.data, "%d/%m/%Y"
            )

        if len(self.texto_data_ate.data) == 10:
            parametros_requisicao["data_ate"] = datetime.strptime(
                self.texto_data_ate.data, "%d/%m/%Y"
            )

        comunica_api_horas_extras = ComunicaApiHorasExtras(self.page)
        retorno_liberacoes = comunica_api_horas_extras.recupera_solicitacoes(
            parametros_requisicao=parametros_requisicao,
            end_point="liberacao_horas_extras",
        )

        if retorno_liberacoes:
            if len(parametros_requisicao) > 2:
                self.botao_limpa_filtros.disabled = False

            self.browse_liberacoes.rows.clear()

            self.paginacao.set_total_paginas(retorno_liberacoes["total_de_paginas"])

            for liberacao in retorno_liberacoes["liberacoes_horas_extras"]:
                botoes_da_linha = []
                # Cores da linha por status
                if liberacao["status_aprovacao"] == "1":
                    # Aguardando aprovação
                    cor_da_linha = ft.Colors.YELLOW

                elif liberacao["status_aprovacao"] == "2":
                    # Aprovada
                    cor_da_linha = ft.Colors.GREEN

                elif liberacao["status_aprovacao"] == "3":
                    # Rejeitada
                    cor_da_linha = ft.Colors.RED

                else:
                    cor_da_linha = None

                botoes_da_linha.append(
                    ft.Icon(
                        name=ft.Icons.ARROW_RIGHT_ROUNDED,
                        tooltip="Status "
                        + STATUS_APROVACAO[liberacao["status_aprovacao"]],
                        color=cor_da_linha,
                        size=40,
                    ),
                )

                if liberacao["status_aprovacao"] == "1":
                    botoes_da_linha.append(
                        ft.IconButton(
                            icon=ft.Icons.ALARM_ON_OUTLINED,
                            data=(liberacao["id"], len(self.browse_liberacoes.rows)),
                            tooltip="Aprovar solicitação",
                            icon_color=ft.Colors.GREEN_ACCENT,
                            on_click=self.aprovar_solicitacao,
                        ),
                    )
                    botoes_da_linha.append(
                        ft.IconButton(
                            icon=ft.Icons.ALARM_OFF_OUTLINED,
                            data=(liberacao["id"], len(self.browse_liberacoes.rows)),
                            tooltip="Recusar solicitação",
                            icon_color=ft.Colors.RED,
                            on_click=self.recusar_solicitacao,
                        ),
                    )

                self.browse_liberacoes.rows.append(
                    ft.DataRow(
                        data=liberacao,
                        cells=[
                            ft.DataCell(ft.Row(botoes_da_linha)),
                            ft.DataCell(ft.Text(str(liberacao["id"]))),
                            ft.DataCell(ft.Text(liberacao["matricula"])),
                            ft.DataCell(ft.Text(liberacao["nome"])),
                            ft.DataCell(
                                ft.Text(iso_to_date(liberacao["data_planejada"]))
                            ),
                            ft.DataCell(ft.Text(liberacao["total_horas_planejada"])),
                            ft.DataCell(
                                ft.Text(iso_to_date(liberacao["data_solicitacao"]))
                            ),
                            ft.DataCell(ft.Text(liberacao["motivo"])),
                            ft.DataCell(
                                ft.Text(STATUS_APROVACAO[liberacao["status_aprovacao"]])
                            ),
                            ft.DataCell(
                                ft.Text(iso_to_date(liberacao["data_aprovacao"]))
                            ),
                            ft.DataCell(ft.Text(liberacao["matricula_aprovador"])),
                            ft.DataCell(ft.Text(liberacao["comentario_aprovador"])),
                        ],
                        on_select_changed=lambda e: self.clique_browse_liberacoes(
                            e.control.data
                        ),
                    )
                )

            if retorno_liberacoes["liberacoes_horas_extras"]:
                self.clique_browse_liberacoes(
                    retorno_liberacoes["liberacoes_horas_extras"][0]
                )
            else:
                self.cartao_painel_visualizacao.visible = False

            self.atualiza_periodo_apontamento()
            self.page.update()

    def atualiza_periodo_apontamento(self):
        """
        Método atualiza os dados do período de apontamento em aberto
        """
        self.periodo_apontamento.obtem_periodo_apontamento()
        if self.periodo_apontamento.erro_requisicao:
            self.texto_periodo_em_vigor.value = self.periodo_apontamento.erro_requisicao

        else:
            self.texto_periodo_em_vigor.value = (
                "De "
                + self.periodo_apontamento.inicio_periodo.strftime("%d/%m/%Y")
                + " a "
                + self.periodo_apontamento.final_periodo.strftime("%d/%m/%Y")
            )

        self.texto_periodo_em_vigor.update()

    def clique_browse_liberacoes(self, solicitacao: dict):
        """
        Método acionado a partir do clique na linha do browse de liberações.
        \n
        Utilizado para atualizar os dados do cartão de visualização individual da liberação da linha clicada.
        """
        if not self.cartao_painel_edicao.visible:
            self.cartao_painel_visualizacao.visible = True
            self.coluna_painel_visualizacao.controls.clear()
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            f"Dados da Solicitação Id: {solicitacao['id']}",
                            text_align=ft.TextAlign.CENTER,
                            expand=True,
                            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        )
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Matrícula: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(solicitacao["matricula"]),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Nome: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(solicitacao["nome"]),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Data Planejada: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(iso_to_date(solicitacao["data_planejada"])),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Qtd. Horas Planejadas: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(solicitacao["total_horas_planejada"]),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(ft.Divider())
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Data da Solicitação: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(iso_to_date(solicitacao["data_solicitacao"])),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Motivo: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(solicitacao["motivo"], expand=True),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(ft.Divider())
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Status da Aprovação: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(STATUS_APROVACAO[solicitacao["status_aprovacao"]]),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Data da Aprovação: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(iso_to_date(solicitacao["data_aprovacao"])),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Matrícula do Aprovador: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(solicitacao["matricula_aprovador"]),
                    ],
                )
            )
            self.coluna_painel_visualizacao.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Comentários: ",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        ft.Text(solicitacao["comentario_aprovador"], expand=True),
                    ],
                )
            )
            self.page.update()

    def limpar_filtros(self):
        """
        Método faz a limpeza dos campos de filtros.
        """
        self.texto_data_de.value = ""
        self.texto_data_de.data = ""
        self.texto_data_ate.value = ""
        self.texto_data_ate.data = ""
        self.seletor_aguardando_aprovacao.value = False
        self.botao_limpa_filtros.disabled = True
        self.carrega_liberacoes()

    def habilitar_desabilitar_edicao(self):
        """
        Método faz a mudança entre os painéis de visualização e edição.
        \n
        Quando é chamado, desativa o que está ativo e vice-versa.
        """
        self.cartao_painel_edicao.visible = not self.cartao_painel_edicao.visible
        self.cartao_painel_visualizacao.visible = (
            not self.cartao_painel_visualizacao.visible
        ) and len(self.browse_liberacoes.rows) > 0
        self.page.update()

    def recusar_solicitacao(self, e):
        """
        Acionado pelo botão de recusa da solicitação de liberação a partir da linha do browse.
        \n
        Recebe como argumento o objeto do evento de clique no botão e utiliza a propriedade 'data'
        que armazena tuple com o id e o índice da linha a qual o botão pertence.
        """
        if self.cartao_painel_edicao.visible:
            Aviso(
                self.page,
                content="Confirme ou cancele a edição atual antes de iniciar outra!",
                title="Atenção",
                actions=["Ok"],
            ).exibir()

        else:
            self.clique_browse_liberacoes(
                self.browse_liberacoes.rows[e.control.data[1]].data
            )
            self.interface_liberacao_hora_extra(
                self.browse_liberacoes.rows[e.control.data[1]].data, liberar=False
            )

    def aprovar_solicitacao(self, e):
        """
        Acionado pelo botão de aprovação da solicitação de liberação a partir da linha do browse.
        \n
        Recebe como argumento o objeto do evento de clique no botão e utiliza a propriedade 'data'
        que armazena tuple com o id e o índice da linha a qual o botão pertence.
        """
        if self.cartao_painel_edicao.visible:
            Aviso(
                self.page,
                content="Confirme ou cancele a liberação atual antes de iniciar outra!",
                title="Atenção",
                actions=["Ok"],
            ).exibir()

        else:
            self.clique_browse_liberacoes(
                self.browse_liberacoes.rows[e.control.data[1]].data
            )
            self.interface_liberacao_hora_extra(
                self.browse_liberacoes.rows[e.control.data[1]].data, liberar=True
            )

    def interface_liberacao_hora_extra(self, dados_liberacao: dict, liberar: bool):
        """
        Monta a interface para o usuário informar os comentários e confirmar a liberação ou recusa da solicitação.
        \n
        Argumentos:
        \n
        'dados_liberacao': dicionário com os dados da solicitação que será liberada ou rejeitada.
        \n
        'liberar': se True, processo de liberação; se False, rejeição.
        """
        auth_session = AuthSession()
        self.titulo_painel_liberacao.value = (
            "Aprovação" if liberar else "Rejeição"
        ) + f" da Solicitação Id: {dados_liberacao['id']}"
        self.matricula_painel_liberacao.value = dados_liberacao["matricula"]
        self.nome_painel_liberacao.value = dados_liberacao["nome"]
        self.data_planejada_painel_liberacao.value = iso_to_date(
            dados_liberacao["data_planejada"]
        )
        self.quantidade_horas_painel_liberacao.value = dados_liberacao[
            "total_horas_planejada"
        ]
        self.data_solicitacao_painel_liberacao.value = iso_to_date(
            dados_liberacao["data_solicitacao"]
        )
        self.motivo_painel_liberacao.value = dados_liberacao["motivo"]
        self.status_painel_liberacao.value = STATUS_APROVACAO[
            dados_liberacao["status_aprovacao"]
        ]
        self.data_aprovacao_painel_liberacao.value = (
            datetime.now().strftime("%d/%m/%Y")
            if liberar
            else iso_to_date(dados_liberacao["data_aprovacao"])
        )
        self.matricula_aprovador_painel_liberacao.value = (
            auth_session.user_data["dados_cadastro_recursos"]["matricula"]
            if liberar
            else dados_liberacao["matricula_aprovador"]
        )
        self.botao_salvar.tooltip = (
            "Liberar" if liberar else "Rejeitar" + " solicitação"
        )
        self.botao_salvar.data = (liberar, dados_liberacao)
        self.habilitar_desabilitar_edicao()

    def cancelar_edicao(self):
        """
        Controla o fechamento da interface de liberação pelo botão 'Cancelar'.
        """
        if (
            Aviso(
                self.page,
                content="Descartar as informações digitadas?",
                title="Atenção",
                actions=["Sim", "Não"],
            ).exibir()
            == 0
        ):
            self.habilitar_desabilitar_edicao()
            self.limpa_campos_edicao()

    def salvar_edicao(self, liberar: bool, dados_liberacao: dict):
        """
        Controla a confirmação da interface de liberação.
        \n
        Argumentos:
        \n
        'liberar': se True, processo de liberação; se False, rejeição.
        \n
        'dados_liberacao': dicionário com os dados da solicitação que será liberada ou rejeitada.
        """
        if (
            Aviso(
                self.page,
                content=f"Confirma a {'liberação' if liberar else 'rejeição'} da solicitação id {dados_liberacao['id']}?",
                title="Atenção",
                actions=["Sim", "Não"],
            ).exibir()
            == 0
        ):
            if liberar:
                dados_liberacao["status_aprovacao"] = "2"
                dados_liberacao["data_aprovacao"] = datetime.now().isoformat()

            else:
                dados_liberacao["status_aprovacao"] = "3"

            dados_liberacao["matricula_aprovador"] = (
                self.matricula_aprovador_painel_liberacao.value
            )
            dados_liberacao["comentario_aprovador"] = self.campo_comentarios.value

            comunica_api_horas_extras = ComunicaApiHorasExtras(page=self.page)
            if comunica_api_horas_extras.envia_alteracao_solicitacao(
                dados_solicitacao=dados_liberacao
            ):
                self.habilitar_desabilitar_edicao()
                self.limpa_campos_edicao()
                self.carrega_liberacoes()

    def limpa_campos_edicao(self):
        """
        Faz a limpeza dos campos utilizados na interface de edição da liberação.
        """
        self.titulo_painel_liberacao.value = ""
        self.matricula_painel_liberacao.value = ""
        self.nome_painel_liberacao.value = ""
        self.data_planejada_painel_liberacao.value = ""
        self.quantidade_horas_painel_liberacao.value = ""
        self.data_solicitacao_painel_liberacao.value = ""
        self.motivo_painel_liberacao.value = ""
        self.status_painel_liberacao.value = ""
        self.data_aprovacao_painel_liberacao.value = ""
        self.matricula_aprovador_painel_liberacao.value = ""
        self.campo_comentarios.value = ""
        self.botao_salvar.data = None

    def on_change_comentario(self, e):
        """
        Método acionado no evento de digitação do campo de comentário.
        \n
        Criado para eliminar o <enter> do texto digitado.
        """
        e.control.value = e.control.value.replace("\n", "")
        e.control.update()
