import flet as ft

from src.mrb.common.security.opcoes_acesso import OPCOES_MENU_PRINCIPAL
from src.mrb.rh.interfaces.liberacao_horas_extras_view import LiberacaoHorasExtras
from src.mrb.common.lib.aviso import Aviso
from src.mrb.rh.interfaces.solicitacao_horas_extras_view import SolicitacaoHorasExtras
from src.mrb.common.interfaces.botoes_menu_principal import BotoesMenuPrincipal
from src.mrb.common.interfaces.navigation_bar import NavigationBar

from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.interfaces.auth.login_view import Login
from src.mrb.common.interfaces.menu_principal_view import MenuPrincipal


class PortalMrbApp:
    def __init__(self, page: ft.Page) -> None:
        self.navigation_bar = NavigationBar("Login", page=page)
        self.page = page
        self.auth_session = AuthSession()
        self.login_view = Login(self.page, navigation_bar=self.navigation_bar)
        self.botoes_menu_principal = BotoesMenuPrincipal(self.page)
        self.solicitacao_horas_extras = SolicitacaoHorasExtras(
            page=self.page,
            navigation_bar=self.navigation_bar,
            botoes_menu_principal=self.botoes_menu_principal,
        )
        self.menu_principal_view = MenuPrincipal(
            navigation_bar=self.navigation_bar,
            botoes_menu_principal=self.botoes_menu_principal,
        )
        self.liberacao_horas_extras = LiberacaoHorasExtras(
            page=self.page,
            navigation_bar=self.navigation_bar,
            botoes_menu_principal=self.botoes_menu_principal,
        )

    # Função que muda a view com base na rota
    def route_change(self, route):
        if len(self.page.views) > 0:
            rota_anterior = self.page.views[-1].route
        else:
            rota_anterior = ""

        if not self.valida_acesso_rota(self.page.route):
            self.page.go(rota_anterior)

        self.page.views.clear()
        if not self.auth_session.user_data and self.page.route != "/login":
            self.page.go("/login")

        if self.page.route == "/login":
            if self.auth_session.user_data:
                self.page.go(rota_anterior)
            else:
                self.page.views.append(self.login_view.get_login_view())

        elif self.page.route == "/menu_principal":
            self.page.views.append(
                self.menu_principal_view.get_menu_principal_view(
                    nome_usuario=self.auth_session.user_data["nome_usuario"]
                )
            )

        elif self.page.route == "/logout":
            self.auth_session.clear_auth_data()
            self.page.go("/login")

        elif self.page.route == "/solicita_he":
            self.page.views.append(
                self.solicitacao_horas_extras.get_solicitacao_horas_extras()
            )
            self.solicitacao_horas_extras.carrega_solicitacoes()

        elif self.page.route == "/aprova_he":
            self.page.views.append(
                self.liberacao_horas_extras.get_liberacao_horas_extras()
            )
            self.page.update()
            self.liberacao_horas_extras.carrega_liberacoes()

        self.page.update()

    # Configurações para mudar a rota e voltar
    def view_pop(self, view):
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

    def valida_acesso_rota(self, rota_destino: str) -> bool:
        acessar = True
        codigo_rotina = None
        print(f"Rota destino {rota_destino}")

        # Sempre permite acesso à tela principal e tela de login
        if rota_destino in ["/menu_principal", "/login", "/logout"]:
            return acessar

        # Obtém o código da rotina pela rota
        for opcao in OPCOES_MENU_PRINCIPAL:
            if opcao["url_view"] == rota_destino:
                codigo_rotina = opcao["codigo_rotina"]

        # Se não tem código de rotina, não disponibiliza o acesso
        if not codigo_rotina:
            acessar = False
            Aviso(
                self.page,
                content=f"Rota '{rota_destino}' sem opção de tela definida! Contate o suporte!",
                actions=["Fechar"],
            ).exibir()

        # Usuário deve ter acesso a rotina
        if (
            acessar
            and not codigo_rotina
            in self.auth_session.user_data["acessos"]["lista_acesso"]
        ):
            Aviso(
                self.page,
                content="Sem acesso à rotina 'SOLICITA_HE'. Solicite acesso ao administrador do Portal!",
                actions=["Fechar"],
            ).exibir()
            acessar = False

        return acessar
