# main.py
import flet as ft

from src.mrb.common.interfaces.portal_mrb_app import PortalMrbApp
from src.mrb.common.interfaces.auth.auth_session import AuthSession


def main(page: ft.Page):
    page.title = "Portal MRB"
    page.bgcolor = ft.colors.BLUE

    portal_mrb_app = PortalMrbApp(page)

    page.on_route_change = portal_mrb_app.route_change
    page.on_view_pop = portal_mrb_app.view_pop
    page.go("/login")


ft.app(target=main, view=ft.AppView.WEB_BROWSER)
