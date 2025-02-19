# main.py
import flet as ft

from src.mrb.common.interfaces.portal_mrb_app import PortalMrbApp
from src.mrb.common.interfaces.auth.auth_session import AuthSession


def main(page: ft.Page):
    page.window.maximized = True
    page.title = "Portal MRB"
    page.theme_mode = ft.ThemeMode(
        page.client_storage.get("page_theme_mode") or "light"
    )
    page.theme = ft.Theme(
        color_scheme_seed=page.client_storage.get("page_color_scheme_seed")
        or "BLUE_300"
    )

    auth_data = AuthSession(page).get_auth_data()

    portal_mrb_app = PortalMrbApp(page)

    page.on_route_change = portal_mrb_app.route_change
    page.on_view_pop = portal_mrb_app.view_pop
    page.on_disconnect = portal_mrb_app.on_disconnect

    if auth_data["user_data"]:
        page.go("/menu_principal")

    else:
        page.go("/login")


ft.app(target=main, view=ft.AppView.WEB_BROWSER)
