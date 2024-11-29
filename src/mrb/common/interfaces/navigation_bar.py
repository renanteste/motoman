import datetime
import locale
import time
import flet as ft
from apscheduler.schedulers.blocking import BlockingScheduler


class NavigationBar:
    def __init__(self, descricao: str) -> None:
        self.pediu_para_parar = False
        self.descricao = f"Portal MRB - {descricao}"
        self.hour_text = ft.Text("hora", size=15, weight=ft.FontWeight.W_600)
        self.week_text = ft.Text("semana", size=12, weight=ft.FontWeight.W_200)
        self.text_title = ft.Text(
            value=self.descricao, size=26, weight=ft.FontWeight.W_500
        )
        self.btn_change_theme = ft.IconButton(
            icon=ft.icons.DARK_MODE_OUTLINED,
            tooltip="Tema claro/escuro",
            on_click=print("change_theme"),
        )
        self.text_user = ft.Text(
            "Faça o Login para acessar o sistema!", size=15, weight=ft.FontWeight.W_600
        )
        self.btn_logout = ft.IconButton(
            icon=ft.icons.LOGOUT_OUTLINED,
            disabled=True,
            tooltip="Logout",
            on_click=print("logout"),
        )

        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self.update_day, "interval", seconds=1, args=[descricao])
        locale.setlocale(locale.LC_ALL, "pt_BR.utf8")
        self.update_day()
        # if not self.scheduler.running:
        #     self.scheduler.start()
        self.navigation_bar = self.get_navigation_bar()

    def get_navigation_bar(self):
        # if not self.scheduler.running:
        #     self.scheduler.start()

        return ft.AppBar(
            elevation=10,
            leading_width=180,
            bgcolor=ft.colors.PRIMARY_CONTAINER,
            leading=ft.Container(
                padding=ft.padding.only(left=15),
                alignment=ft.alignment.center,
                content=ft.Row(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.icons.COTTAGE_OUTLINED, size=36),
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
                    icon=ft.icons.COLOR_LENS_OUTLINED,
                    tooltip="Trocar cor do tema",
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.PURPLE_300,
                                    ),
                                    ft.Text("Roxo"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.ORANGE_300,
                                    ),
                                    ft.Text("Laranja"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.GREEN_300,
                                    ),
                                    ft.Text("Verde"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.RED_300,
                                    ),
                                    ft.Text("Vermelho"),
                                ]
                            ),
                            on_click=print("change_color_seed,"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.BLUE_300,
                                    ),
                                    ft.Text("Azul (Default)"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.YELLOW_300,
                                    ),
                                    ft.Text("Amarelo"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.INDIGO_300,
                                    ),
                                    ft.Text("Indigo"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.TEAL_300,
                                    ),
                                    ft.Text("Teal"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.LIME_300,
                                    ),
                                    ft.Text("Lime"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.COLOR_LENS_OUTLINED,
                                        color=ft.colors.BROWN_400,
                                    ),
                                    ft.Text("Marrom"),
                                ]
                            ),
                            on_click=print("change_color_seed"),
                        ),
                    ],
                ),
                ft.Container(
                    padding=10,
                    content=ft.Column(
                        spacing=0,
                        controls=[ft.Text("Bem vindo!", size=12), self.text_user],
                    ),
                ),
                self.btn_logout,
            ],
        )

    def update_day(self, descricao: str = None):
        if descricao:
            print(descricao)

        # Obtém a data atual
        today = datetime.date.today()

        # Obtem a hora atual
        agora = datetime.datetime.now()

        # Formata a hora em uma string com o formato h:m:s
        hora_formatada = agora.strftime("%H:%M:%S")

        # Define o formato de data para apenas dia e mês
        date_format = "%d/%m"

        # Define o texto para a label de data
        date_text = today.strftime(date_format)

        # Define o texto para a label de dia da semana
        day_of_week_text = today.strftime("%A")

        # Define o texto das labels
        self.hour_text.value = f"{date_text} - {hora_formatada}"
        self.week_text.value = day_of_week_text.upper()
        self.text_title.value = self.descricao
        if self.hour_text.parent:
            self.hour_text.update()
            self.week_text.update()
            self.text_title.update()

        else:
            if self.scheduler.running:
                self.pediu_para_parar = True
                self.scheduler.shutdown(False)
