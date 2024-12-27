import flet as ft

from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.security.opcoes_acesso import OPCOES_MENU_PRINCIPAL


class BotoesMenuPrincipal:
    def __init__(self, page: ft.Page) -> None:
        self.page = page

        self.container = ft.Container(
            padding=ft.padding.all(5),
            border_radius=ft.border_radius.all(5),
            visible=True,
        )

        self.navigation_rail = ft.NavigationRail(
            extended=False,
            label_type=ft.NavigationRailLabelType.NONE,
            min_width=56,
            min_extended_width=160,
            bgcolor="transparent",
            leading=ft.IconButton(
                icon=ft.Icons.SWAP_HORIZ_ROUNDED,
                icon_size=40,
                tooltip="Mostrar/Ocultar Descrição",
                on_click=lambda e: self.mostrar_ocultar_descrição(e=e),
            ),
            group_alignment=-0.95,
            destinations=self.get_opcoes_menu_principal(),
            on_change=lambda e: self.navegar_para(e),
        )
        self.container.content = self.navigation_rail

    def get_botoes_menu_principal(self):
        return self.container

    def navegar_para(self, e):
        opcao_selecionada = e.control.selected_index
        if e.control.selected_index == 0:
            self.page.go("/menu_principal")
        else:
            opcao_selecionada -= 1
            self.page.go(OPCOES_MENU_PRINCIPAL[opcao_selecionada]["url_view"])

    def mostrar_ocultar_descrição(self, e):
        self.navigation_rail.extended = not self.navigation_rail.extended
        self.page.update()

    def get_opcoes_menu_principal(self) -> list[ft.NavigationRailDestination]:
        opcoes_menu_pricipal = [
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.Icons.COTTAGE_OUTLINED, tooltip="Home"),
                selected_icon=ft.Icon(ft.Icons.COTTAGE, tooltip="Home"),
                label="Home",
            )
        ]
        auth_session = AuthSession()

        if auth_session.user_data:
            for opcao in OPCOES_MENU_PRINCIPAL:
                if (
                    opcao["disponivel_menu"]
                    and opcao["codigo_rotina"]
                    in auth_session.user_data["acessos"]["lista_acesso"]
                ):
                    opcoes_menu_pricipal.append(
                        ft.NavigationRailDestination(
                            icon_content=ft.Icon(
                                opcao["icone"], tooltip=opcao["descricao_menu"]
                            ),
                            selected_icon_content=ft.Icon(
                                opcao["icone_selecionado"],
                                tooltip=opcao["descricao_menu"],
                            ),
                            label=opcao["descricao_menu"],
                        )
                    )

        return opcoes_menu_pricipal
