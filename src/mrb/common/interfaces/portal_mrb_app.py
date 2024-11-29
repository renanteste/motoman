import flet as ft
from apscheduler.schedulers.background import BackgroundScheduler

from src.mrb.common.interfaces.instancia_navigation_bar import instancia_navigation_bar
from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.interfaces.auth.login_view import Login
from src.mrb.common.interfaces.menu_principal_view import MenuPrincipal


class PortalMrbApp:
    def __init__(self, page: ft.Page) -> None:
        self.navigation_bar = instancia_navigation_bar.get_navigation_bar()
        self.page = page
        self.auth_session = AuthSession()
        self.login_view = Login(self.page)
        self.menu_principal_view = MenuPrincipal()
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            self.atualiza_navigation_bar,
            "interval",
            seconds=1,
        )
        # if not self.scheduler.running:
        #     self.scheduler.start()

    # Função que muda a view com base na rota
    def route_change(self, route):
        if len(self.page.views) > 0:
            rota_anterior = self.page.views[-1].route
        else:
            rota_anterior = ""

        self.page.views.clear()
        if self.page.route == "/login":
            if self.auth_session.user_data:
                self.page.go(rota_anterior)
            else:
                self.page.views.append(self.login_view.get_login_view())

        elif self.page.route == "/menu_principal":
            self.page.views.append(self.menu_principal_view.get_menu_principal_view())

        self.page.update()

    # Configurações para mudar a rota e voltar
    def view_pop(self, view):
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

    def atualiza_navigation_bar(self):
        instancia_navigation_bar.update_day("Inicial")
