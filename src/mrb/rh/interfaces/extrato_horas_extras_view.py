import flet as ft

from src.mrb.common.interfaces.paginacao import Paginacao
from src.mrb.common.interfaces.botoes_menu_principal import BotoesMenuPrincipal
from src.mrb.common.interfaces.navigation_bar import NavigationBar


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

        # Filtros
        self.botao_limpar_filtros = ft.IconButton(
            icon=ft.Icons.FILTER_ALT_OFF_OUTLINED,
            tooltip="Limpar filtros",
            disabled=True,
        )
        self.seletor_colaborador = ft.Dropdown(
            width=330,
            height=40,
            label="Colaborador",
            hint_text="Selecione um colaborador",
            dense=True,
            options=[
                ft.dropdown.Option(" ", " "),
                ft.dropdown.Option("000001", "ADAUTO MEDEIROS"),
                ft.dropdown.Option("000002", "KEISI"),
                ft.dropdown.Option("000003", "GUSTAVO"),
                ft.dropdown.Option("000004", "RICARDO SILVEIRA"),
                ft.dropdown.Option("000005", "MARCELO MENDES COLATO"),
            ],
        )
        self.campo_data_de = ft.TextField(
            dense=True,
            width=120,
            hint_text="  /  /    ",
            text_size=14,
        )
        self.campo_data_ate = ft.TextField(
            dense=True,
            width=120,
            hint_text="  /  /    ",
            text_size=14,
        )
        self.browse_periodos = ft.DataTable(
            expand=True,
            divider_thickness=0.4,
            sort_ascending=True,
            columns=[
                ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Dt. Inicial", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Dt. Final", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )
        self.browse_movimentos = ft.DataTable(
            expand=True,
            divider_thickness=0.4,
            sort_ascending=True,
            columns=[
                ft.DataColumn(ft.Text("Id", weight=ft.FontWeight.BOLD)),
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
        self.paginacao = Paginacao(lambda _: print("Página mudou"))

    def get_extrato_horas_extras(self) -> ft.View:
        area_de_filtros = ft.Container(
            expand=2,
            border_radius=5,
            padding=15,
            content=ft.Column(
                expand=True,
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Filtros", theme_style=ft.TextThemeStyle.TITLE_MEDIUM
                            )
                        ],
                    ),
                    ft.Divider(),
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.botao_limpar_filtros,
                            self.seletor_colaborador,
                        ],
                    ),
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("Data de:"),
                            self.campo_data_de,
                            ft.Text("Até:"),
                            self.campo_data_ate,
                        ],
                    ),
                    ft.Divider(color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Períodos de Banco de Horas",
                                theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                            )
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        border=ft.border.all(1),
                        border_radius=5,
                        content=ft.ListView(
                            expand=True,
                            auto_scroll=True,
                            controls=[
                                ft.Row(
                                    expand=True,
                                    scroll=ft.ScrollMode.ADAPTIVE,
                                    controls=[self.browse_periodos],
                                )
                            ],
                        ),
                    ),
                ],
            ),
        )

        area_de_dados = ft.Container(
            expand=5,
            border_radius=5,
            padding=15,
            content=ft.Column(
                expand=True,
                spacing=20,
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
                        auto_scroll=True,
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
            content=ft.Column(
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                area_de_filtros,
                                ft.VerticalDivider(),
                                area_de_dados,
                            ],
                        ),
                    )
                ]
            ),
        )

        return ft.View(
            route="/extrato_he",
            padding=0,
            controls=[
                self.navigation_bar.get_navigation_bar(
                    "Consulta ao Extrato de Horas Extras"
                ),
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
