import datetime
import locale
import flet as ft

from src.mrb.common.config import SqlConfiguration


MENSAGEM_LOGIN = "Faça o Login para acessar o sistema!"


class NavigationBar:
    def __init__(self, descricao: str, page: ft.Page = None) -> None:
        self.page = page
        self.descricao = f"Portal MRB - {descricao}"
        self.hour_text = ft.Text("hora", size=15, weight=ft.FontWeight.W_600)
        self.week_text = ft.Text("semana", size=12, weight=ft.FontWeight.W_200)
        self.text_title = ft.Text(
            value=self.descricao, size=26, weight=ft.FontWeight.W_500
        )
        self.btn_change_theme = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED,
            tooltip="Tema claro/escuro",
            on_click=lambda e: self.change_theme(e=e),
        )
        self.text_user = ft.Text(MENSAGEM_LOGIN, size=15, weight=ft.FontWeight.W_600)
        self.btn_logout = ft.IconButton(
            icon=ft.Icons.LOGOUT_OUTLINED,
            disabled=True,
            tooltip="Logout",
            on_click=lambda _: self.page.go("/logout"),
        )

        locale.setlocale(locale.LC_ALL, "pt_BR.utf8")
        self.update_day()

    def get_navigation_bar(self, descricao: str, nome_usuario: str = None):
        ambiente = SqlConfiguration.DATABASE
        if ambiente == "ZT8HTG":
            ambiente = ""

        else:
            ambiente = f" ({ambiente})"

        self.descricao = descricao
        if nome_usuario:
            self.text_user.value = nome_usuario.capitalize()
            self.btn_logout.disabled = False

        self.update_day()

        return ft.AppBar(
            elevation=10,
            leading_width=180,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            leading=ft.Container(
                padding=ft.padding.only(left=15),
                alignment=ft.alignment.center,
                content=ft.Row(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.COTTAGE_OUTLINED, size=36),
                        ft.Column(
                            expand=True,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=0,
                            controls=[self.hour_text, self.week_text],
                        ),
                    ],
                ),
            ),
            title=self.text_title,
            actions=[
                self.btn_change_theme,
                ft.PopupMenuButton(
                    icon=ft.Icons.COLOR_LENS_OUTLINED,
                    tooltip="Trocar cor do tema",
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.PURPLE_300,
                                    ),
                                    ft.Text("Roxo"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.ORANGE_300,
                                    ),
                                    ft.Text("Laranja"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.GREEN_300,
                                    ),
                                    ft.Text("Verde"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.RED_300,
                                    ),
                                    ft.Text("Vermelho"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.BLUE_300,
                                    ),
                                    ft.Text("Azul (Default)"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.YELLOW_300,
                                    ),
                                    ft.Text("Amarelo"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.INDIGO_300,
                                    ),
                                    ft.Text("Indigo"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.TEAL_300,
                                    ),
                                    ft.Text("Teal"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.LIME_300,
                                    ),
                                    ft.Text("Lime"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.COLOR_LENS_OUTLINED,
                                        color=ft.Colors.BROWN_400,
                                    ),
                                    ft.Text("Marrom"),
                                ]
                            ),
                            on_click=lambda e: self.change_color_seed(e=e),
                        ),
                    ],
                ),
                ft.Container(
                    padding=10,
                    content=ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text(f"Bem vindo!{ambiente}", size=12),
                            self.text_user,
                        ],
                    ),
                ),
                self.btn_logout,
            ],
        )

    def change_color_seed(self, e):
        self.page.theme = ft.Theme(
            color_scheme_seed=e.control.content.controls[0].color
        )
        self.page.update()
        self.page.client_storage.set(
            "page_color_scheme_seed", self.page.theme.color_scheme_seed
        )

    def change_theme(self, e):
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.btn_change_theme.icon = ft.Icons.WB_SUNNY_OUTLINED

        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.btn_change_theme.icon = ft.Icons.DARK_MODE_OUTLINED

        self.page.update()

        self.page.client_storage.set("page_theme_mode", self.page.theme_mode.value)

    def update_day(self):
        # Obtém a data atual
        today = datetime.date.today()

        # Define o formato de data para apenas dia e mês
        date_format = "%d/%m"

        # Define o texto para a label de data
        date_text = today.strftime(date_format)

        # Define o texto para a label de dia da semana
        day_of_week_text = today.strftime("%A")

        # Define o texto das labels
        self.hour_text.value = f"{date_text}"
        self.week_text.value = day_of_week_text.upper()
        self.text_title.value = self.descricao
        if self.hour_text.parent:
            self.hour_text.update()

        if self.week_text.parent:
            self.week_text.update()

        if self.text_title.parent:
            self.text_title.update()

        if self.text_user.parent:
            self.text_user.update()

    def mensagem_login(self):
        self.text_user.value = MENSAGEM_LOGIN
