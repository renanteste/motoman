# menu_principal.py
import flet as ft

from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.common.lib.view_ft_azul import ViewFtAzul

OPCOES_MENU_PRINCIPAL = [
    {
        "codigo_rotina": "SOLICITA_HE",
        "descricao_menu": "Solicitação Hora Extra",
        "modulo": "RH",
        "url_view": "solicita_he",
    },
    {
        "codigo_rotina": "APROVA_HE",
        "descricao_menu": "Aprovação Hora Extra",
        "modulo": "RH",
        "url_view": "aprova_he",
    },
]


def botoes_menu_principal() -> list[ft.ElevatedButton]:
    botoes = []
    for opcao in OPCOES_MENU_PRINCIPAL:
        botao = ft.ElevatedButton(
            opcao["descricao_menu"],
            on_click=lambda e: e.page.go(f"/{opcao['url_view']}"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
            height=50,
            width=300,
        )
        botoes.append(botao)
    return botoes


def menu_principal_view():
    return ViewFtAzul(
        route="/menu_principal",
        padding=0,
        controls=[
            # Barra de título no topo
            ft.AppBar(
                title=ft.Text("Portal MRB - Menu Principal"),
                bgcolor=ft.colors.SURFACE_VARIANT,
                center_title=True,
            ),
            # Linha principal dividindo o menu e o conteúdo central
            ft.Row(
                controls=[
                    # Menu Lateral (25% da largura)
                    ft.Container(
                        content=ft.Column(
                            controls=botoes_menu_principal(),
                            alignment=ft.MainAxisAlignment.START,
                            spacing=0,
                        ),
                        width=300,  # Aproximadamente 25% da largura em uma tela média
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        padding=0,
                    ),
                    # Área central com o logotipo
                    ft.Container(
                        content=ft.Image(
                            src=f"http://{Environment.SERVER_IP}:{ApiConfiguration.rh.PORT}/images/robo.png",  # Coloque o caminho do logotipo aqui
                            width=400,
                            height=400,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        alignment=ft.alignment.center,
                        expand=True,  # Ocupa o espaço restante da linha
                    ),
                ],
                expand=True,
                spacing=0,
            ),
        ],
    )
