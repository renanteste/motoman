# login_view.py
import flet as ft
import requests

from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.config import ApiConfiguration
from src.mrb.common.lib.aviso import Aviso
from src.mrb.common.lib.view_ft_azul import ViewFtAzul


def login_view(page):
    titulo = ft.Text("Portal MRB - Login", theme_style=ft.TextThemeStyle.DISPLAY_MEDIUM)
    nome_usuario_input = ft.TextField(
        label="Usuário",
        max_length=50,
        width=400,
        bgcolor=ft.colors.WHITE,
        color=ft.colors.BLACK54,
    )
    senha_input = ft.TextField(
        label="Senha",
        password=True,
        max_length=25,
        width=400,
        bgcolor=ft.colors.WHITE,
        color=ft.colors.BLACK54,
    )
    nome_usuario_input.value = "mm.colato@gmail.com"
    senha_input.value = "Cc0l@t0O422320"

    def on_login_click(e):
        dados_autenticacao = None
        login_button.disabled = True
        login_button.update()
        aviso = Aviso(page, modal=True)
        if not nome_usuario_input.value:
            aviso.content = "Informe seu id de usuário para acesso ao portal!"
            aviso.title = "Atenção"
            aviso.actions = ["Ok"]
            aviso.exibir()
        elif not senha_input.value:
            aviso.content = "Digite sua senha!"
            aviso.title = "Atenção"
            aviso.actions = ["Ok"]
            aviso.exibir()
        else:
            response_auth = requests.post(
                url=f"http://{ApiConfiguration.auth.URL}:{ApiConfiguration.auth.PORT}/auth",
                data={
                    "username": nome_usuario_input.value,
                    "password": senha_input.value,
                },
            )
            if response_auth.status_code == 200:
                dados_autenticacao = response_auth.json()
                aviso.content = (
                    f"Bem vindo {dados_autenticacao['dados_usuario']['nome_usuario']}!"
                )
                aviso.title = "Acesso ao Portal"
                aviso.actions = ["Acessar"]
            else:
                aviso.content = (
                    f"{response_auth.status_code} - {response_auth.json()['detail']}"
                )
                aviso.title = "Retorno da autenticação"
                aviso.actions = ["Ok"]

            aviso.exibir()
            if dados_autenticacao:
                auth_data = AuthSession()
                auth_data.set_auth_data(
                    dados_autenticacao["dados_autenticacao"]["token"],
                    dados_autenticacao["dados_usuario"],
                )
                login_view.visible = False
                page.go("/menu_principal")

        login_button.disabled = False
        login_button.update()
        page.update()

    login_button = ft.FilledButton(text="Login", on_click=on_login_click)
    login_view = ft.Column(
        controls=[
            titulo,
            ft.Container(
                content=ft.Column(
                    controls=[
                        nome_usuario_input,
                        senha_input,
                        login_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=350,
                height=220,
                padding=20,
                border_radius=ft.border_radius.all(15),
                bgcolor=ft.colors.WHITE,
                alignment=ft.alignment.center,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ViewFtAzul(
        route="/login",
        controls=[login_view],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
