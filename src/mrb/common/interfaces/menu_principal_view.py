# menu_principal.py
import flet as ft

from src.mrb.common.interfaces.instancia_navigation_bar import instancia_navigation_bar

# from src.mrb.common.interfaces.navigation_bar import NavigationBar
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


class MenuPrincipal:
    def __init__(self) -> None:
        # self.navigation_bar = NavigationBar("Menu Principal")
        self.menu_principal = self.get_menu_principal_view()

    def get_menu_principal_view(self):
        instancia_navigation_bar.descricao = "Menu Principal"
        view_retorno = ft.View(
            route="/menu_principal",
            padding=0,
            controls=[
                # Barra de título no topo
                instancia_navigation_bar.get_navigation_bar(),
                # Linha principal dividindo o menu e o conteúdo central
                ft.Row(
                    controls=[
                        # Menu Lateral (25% da largura)
                        ft.Container(
                            content=ft.Column(
                                controls=self.botoes_menu_principal(),
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
                                src=f"http://{Environment.SERVER_IP}:{ApiConfiguration.rh.PORT}/images/OG-Robot-Lineup.jpg",  # Coloque o caminho do logotipo aqui
                                width=1236,
                                height=673,
                                fit=ft.ImageFit.FILL,
                                expand=True,
                            ),
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
        # view_retorno.navigation_bar = self.navigation_bar.get_navigation_bar()
        return view_retorno

    def botoes_menu_principal(self) -> list[ft.ElevatedButton]:
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
