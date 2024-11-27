from flet import (
    UserControl,
    TextField,
    icons,
    OutlinedButton,
    Container,
    alignment,
    Row,
    MainAxisAlignment,
    CrossAxisAlignment,
    padding,
    colors,
    BoxShadow,
    Offset,
    ShadowBlurStyle,
    Column,
    Text,
    TextThemeStyle,
)
import requests

from src.mrb.common.lib import Aviso
from src.mrb.common.config import ApiConfiguration


class Login(UserControl):
    def __init__(self, route):
        super().__init__()
        self.route = route

    def build(self):
        self.text_user = TextField(
            label="Usuário",
            prefix_icon=icons.PERSON_2_OUTLINED,
            expand=True,
            autofocus=True,
            on_change=self.analyze_to_enable_button,
        )
        self.text_password = TextField(
            label="Senha",
            prefix_icon=icons.LOCK_OUTLINE_ROUNDED,
            expand=True,
            password=True,
            can_reveal_password=True,
            on_change=self.analyze_to_enable_button,
        )
        self.btn_login = OutlinedButton(
            text="Login",
            width=240,
            icon=icons.LOGIN_OUTLINED,
            disabled=True,
            on_click=self.login_clicked,
        )
        return Container(
            expand=True,
            alignment=alignment.center,
            content=Row(
                expand=True,
                alignment=MainAxisAlignment.CENTER,
                vertical_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Container(
                        padding=padding.only(60, 34, 60, 20),
                        bgcolor=colors.SURFACE,
                        border_radius=10,
                        width=500,
                        height=360,
                        shadow=BoxShadow(
                            spread_radius=5,
                            blur_radius=5,
                            color=colors.GREY_300,
                            offset=Offset(1, 1),
                            blur_style=ShadowBlurStyle.NORMAL,
                        ),
                        content=Column(
                            spacing=30,
                            alignment=MainAxisAlignment.START,
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            tight=True,
                            controls=[
                                Row(
                                    alignment=MainAxisAlignment.CENTER,
                                    controls=[
                                        Text(
                                            "Login",
                                            theme_style=TextThemeStyle.TITLE_LARGE,
                                        )
                                    ],
                                ),
                                Row(controls=[self.text_user]),
                                Row(controls=[self.text_password]),
                                Row(
                                    alignment=MainAxisAlignment.CENTER,
                                    controls=[self.btn_login],
                                ),
                            ],
                        ),
                    )
                ],
            ),
        )

    def go_to_home(self, name, permission):
        # self.route.config.set_permissions(name, permission)

        self.page.go("/home")
        self.route.bar.enable_btn_logout()
        self.route.bar.set_username(name)
        self.route.bar.set_title("Página Inicial")
        self.route.menu.cont.visible = True
        self.route.menu.update()
        self.route.page.update()

    def login(self):
        data = [self.text_user.value, self.text_password.value]
        response_auth = requests.post(
            url=f"http://{ApiConfiguration.auth.URL}:{ApiConfiguration.auth.PORT}/auth",
            data={
                "username": self.text_user.value,
                "password": self.text_password.value,
            },
        )

        aviso = Aviso(self.page, modal=True)
        if response_auth.status_code == 200:
            dados_autenticacao = response_auth.json()
            name = dados_autenticacao["dados_usuario"]["nome_usuario"]
            permission = dados_autenticacao["dados_autenticacao"]["token"]
        else:
            aviso.content = (
                f"{response_auth.status_code} - {response_auth.json()['detail']}"
            )
            aviso.title = "Retorno da autenticação"
            aviso.actions = ["Ok"]
            aviso.exibir()
            return

        self.go_to_home(name, permission)

    def login_clicked(self, e):
        # self.route.config.initialize()

        # if self.route.config.host is None:
        #     return

        # if not self.verify_count_of_users():
        #     self.create_admin()
        #     return

        self.login()

    def analyze_to_enable_button(self, e):
        self.btn_login.disabled = (
            self.text_user.value == "" or self.text_password.value == ""
        )
        self.update()

    def initialize(self):
        if not self.route.bar.scheduler.running:
            self.route.bar.scheduler.start()
