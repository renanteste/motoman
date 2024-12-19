import flet as ft
import requests

from src.mrb.common.interfaces.navigation_bar import NavigationBar
from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.config import ApiConfiguration
from src.mrb.common.lib.aviso import Aviso


class Login:
    def __init__(self, page: ft.Page, navigation_bar: NavigationBar) -> None:
        self.dados_autenticacao = None
        self.page = page
        self.navigation_bar = navigation_bar
        self.nome_usuario_input = ft.TextField(
            label="Usuário",
            prefix_icon=ft.icons.PERSON_2_OUTLINED,
            expand=True,
            autofocus=True,
            on_blur=lambda e: self.completa_email(e),
        )
        self.senha_input = ft.TextField(
            label="Senha",
            prefix_icon=ft.icons.LOCK_OUTLINE_ROUNDED,
            expand=True,
            password=True,
            can_reveal_password=True,
        )

        self.login_button = ft.OutlinedButton(
            text="Login",
            width=240,
            icon=ft.icons.LOGIN_OUTLINED,
            on_click=self.on_login_click,
        )
        self.login_view = self.get_login_view()

    def on_login_click(self, e):
        self.dados_autenticacao = None
        self.login_button.disabled = True
        if self.login_button.parent:
            self.login_button.update()
        aviso = Aviso(self.page, modal=True)
        if not self.nome_usuario_input.value:
            aviso.content = "Informe seu id de usuário para acesso ao portal!"
            aviso.title = "Atenção"
            aviso.actions = ["Ok"]
            aviso.exibir()
        elif not self.senha_input.value:
            aviso.content = "Digite sua senha!"
            aviso.title = "Atenção"
            aviso.actions = ["Ok"]
            aviso.exibir()
        else:
            response_auth = requests.post(
                headers={"User-Agent": "PortalPy"},
                url=f"http://{ApiConfiguration.auth.URL}:{ApiConfiguration.auth.PORT}/auth",
                data={
                    "username": self.nome_usuario_input.value,
                    "password": self.senha_input.value,
                },
            )
            if response_auth.status_code == 200:
                self.dados_autenticacao = response_auth.json()
                aviso.content = f"Bem vindo {self.dados_autenticacao['dados_usuario']['nome_usuario']}!"
                aviso.title = "Acesso ao Portal"
                aviso.actions = ["Acessar"]
            else:
                aviso.content = (
                    f"{response_auth.status_code} - {response_auth.json()['detail']}"
                )
                aviso.title = "Retorno da autenticação"
                aviso.actions = ["Ok"]

            aviso.exibir()
            if self.dados_autenticacao:
                auth_data = AuthSession()
                auth_data.set_auth_data(
                    self.dados_autenticacao["dados_autenticacao"]["token"],
                    self.dados_autenticacao["dados_usuario"],
                )
                self.login_view.visible = False
                self.page.go("/menu_principal")

        self.login_button.disabled = False
        if self.login_button.parent:
            self.login_button.update()
        self.page.update()

    def get_login_view(self):
        self.navigation_bar.descricao = "Login"

        login_control = ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Row(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(60, 34, 60, 20),
                        bgcolor=ft.colors.SURFACE,
                        border_radius=10,
                        width=500,
                        height=360,
                        shadow=ft.BoxShadow(
                            spread_radius=5,
                            blur_radius=5,
                            color=ft.colors.GREY_300,
                            offset=ft.Offset(1, 1),
                            blur_style=ft.ShadowBlurStyle.NORMAL,
                        ),
                        content=ft.Column(
                            spacing=30,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            tight=True,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(
                                            "Login",
                                            theme_style=ft.TextThemeStyle.TITLE_LARGE,
                                        )
                                    ],
                                ),
                                ft.Row(controls=[self.nome_usuario_input]),
                                ft.Row(controls=[self.senha_input]),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[self.login_button],
                                ),
                            ],
                        ),
                    )
                ],
            ),
        )

        login_view = ft.Column(
            controls=[
                login_control,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return ft.View(
            route="/login",
            controls=[self.navigation_bar.get_navigation_bar("Login"), login_view],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def completa_email(self, e):
        campo_usuario: ft.TextField = e.control

        if not campo_usuario.value.strip() == "" and not "@" in campo_usuario.value:
            campo_usuario.value += "@motoman.com.br"
            campo_usuario.update()
