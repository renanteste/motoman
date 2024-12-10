# menu_principal.py
import flet as ft

from src.mrb.common.interfaces.botoes_menu_principal import BotoesMenuPrincipal
from src.mrb.common.interfaces.navigation_bar import NavigationBar
from src.mrb.common.schemas.schema_auth_service import DadosUsuario
from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.common.lib.view_ft_azul import ViewFtAzul


class MenuPrincipal:
    def __init__(
        self,
        navigation_bar: NavigationBar,
        botoes_menu_principal: BotoesMenuPrincipal,
    ) -> None:
        self.navigation_bar = navigation_bar
        self.botoes_laterais = botoes_menu_principal

    def get_menu_principal_view(self, nome_usuario: str = None):
        return ft.View(
            route="/menu_principal",
            padding=0,
            controls=[
                # Barra de título no topo
                self.navigation_bar.get_navigation_bar(
                    "Menu Principal", nome_usuario=nome_usuario
                ),
                # Linha principal dividindo o menu e o conteúdo central
                ft.Row(
                    controls=[
                        self.botoes_laterais.get_botoes_menu_principal(),
                        # Área central com o logotipo
                        ft.Container(
                            content=ft.Image(
                                src=f"http://{Environment.SERVER_IP}:{ApiConfiguration.rh.PORT}/images/OG-Robot-Lineup.jpg",
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
