from flet import Page, Container, Row, VerticalDivider

from src.mrb.common.interfaces.infostore.config import Config
from src.mrb.common.interfaces.infostore.home import Home
from src.mrb.common.interfaces.infostore.login import Login
from src.mrb.common.interfaces.infostore.app_bar import MrbAppBar
from src.mrb.common.interfaces.infostore.side_menu import SideMenu


class PortalMrbApp:
    def __init__(self, page: Page) -> None:
        self.page = page

        self.menu = SideMenu(self)

        self.bar = MrbAppBar(self)

        self.page.navigation_bar = self.bar.build()

        self.login = Login(self)
        self.home = Home(self)
        self.routes = {
            "/": self.login,
            "/home": self.home,
        }
        self.calls = {
            "/": self.login.initialize,
            "/home": self.home.initialize,
        }
        self.container = Container(expand=True, content=self.routes["/"])
        self.body = Row(
            expand=True,
            controls=[
                self.menu,
                VerticalDivider(width=1),
                self.container,
            ],
        )
        self.config = Config(self)

    def route_change(self, e):
        # Change View:
        self.container.content = self.routes[e.route]
        self.page.update()

        # Initialize the View
        self.calls[e.route]()

        self.page.update()
