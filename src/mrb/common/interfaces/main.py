# main.py
import flet as ft

from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.interfaces.auth.login_view import login_view
from src.mrb.common.interfaces.menu_principal_view import menu_principal_view


def main(page: ft.Page):
    page.title = "Portal MRB"
    page.bgcolor = ft.colors.BLUE

    # Função que muda a view com base na rota
    def route_change(route):
        auth_session = AuthSession()
        rota_anterior = page.views[-1].route if len(page.views) > 0 else ""
        page.views.clear()
        if page.route == "/login":
            if auth_session.user_data:
                page.go(rota_anterior)
            else:
                page.views.append(login_view(page))

        elif page.route == "/menu_principal":
            page.views.append(menu_principal_view())

        page.update()

    # Configurações para mudar a rota e voltar
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")  # Define a rota inicial como /login


ft.app(target=main, view=ft.AppView.WEB_BROWSER)
