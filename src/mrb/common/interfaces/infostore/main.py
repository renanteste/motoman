from flet import Page, app, Theme, ThemeMode, colors

from src.mrb.common.interfaces.infostore.portal_mrb_app import PortalMrbApp


def main(page: Page):
    page.title = "Portal MRB"
    page.window.min_height = 700
    page.window.min_width = 1360

    page.theme_mode = ThemeMode.LIGHT
    page.theme = Theme(color_scheme_seed=colors.BLUE_300)

    portal_mrb_app = PortalMrbApp(page=page)
    page.on_route_change = portal_mrb_app.route_change

    page.add(portal_mrb_app.body)

    page.go("/")

    page.update()


if __name__ == "__main__":
    app(target=main)
