import flet as ft

from src.mrb.rh.interfaces.extrato_horas_extras_view import ExtratoHorasExtras
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
        self.extrato_horas_extras = ExtratoHorasExtras(
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
        if not AuthSession(self.page).user_data() and self.page.route != "/login":
            self.page.go("/login")

        if self.page.route == "/login":
            if AuthSession(self.page).user_data():
                self.page.go(rota_anterior)
            else:
                self.page.views.append(self.login_view.get_login_view())

        elif self.page.route == "/menu_principal":
            self.botoes_menu_principal.navigation_rail.destinations = (
                self.botoes_menu_principal.get_opcoes_menu_principal()
            )
            self.page.views.append(
                self.menu_principal_view.get_menu_principal_view(
                    nome_usuario=AuthSession(self.page).user_data()["nome_usuario"]
                )
            )

        elif self.page.route == "/logout":
            self.logout()
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

        elif self.page.route == "/extrato_he":
            self.page.views.append(self.extrato_horas_extras.get_extrato_horas_extras())
            self.page.update()
            self.extrato_horas_extras.recupera_periodos_banco_horas()
            self.extrato_horas_extras.recupera_extrato()
            self.extrato_horas_extras.recupera_colaboradores_extrato()

        self.page.update()

    # Configurações para mudar a rota e voltar
    def view_pop(self, view):
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

    def valida_acesso_rota(self, rota_destino: str) -> bool:
        acessar = True
        codigo_rotina = None

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
            in AuthSession(self.page).user_data()["acessos"]["lista_acesso"]
        ):
            Aviso(
                self.page,
                content="Sem acesso à rotina 'SOLICITA_HE'. Solicite acesso ao administrador do Portal!",
                actions=["Fechar"],
            ).exibir()
            acessar = False

        return acessar

    def logout(self):
        AuthSession(self.page).clear_auth_data()
        self.login_view.nome_usuario_input.value = None
        self.login_view.senha_input.value = None
        self.navigation_bar.mensagem_login()

    def on_disconnect(self, e):
        self.logout()
