from flet import (
    UserControl,
    Container,
    padding,
    border_radius,
    NavigationRail,
    NavigationRailLabelType,
    IconButton,
    icons,
    NavigationRailDestination,
)

from src.mrb.common.interfaces.infostore.set_general_config import SetGeneralConfig


class SideMenu(UserControl):
    def __init__(self, route):
        super().__init__()
        self.route = route

        self.cont = Container(
            padding=padding.all(5), border_radius=border_radius.all(5), visible=False
        )

        self.nnrail = NavigationRail(
            extended=False,
            label_type=NavigationRailLabelType.NONE,
            min_width=56,
            min_extended_width=160,
            bgcolor="transparent",
            leading=IconButton(
                icon=icons.SWAP_HORIZ_ROUNDED,
                icon_size=40,
                tooltip="Mostrar/Ocultar Opções",
                on_click=self.menu_clicked,
            ),
            group_alignment=-0.95,
            destinations=[
                NavigationRailDestination(
                    icon=icons.COTTAGE_OUTLINED,
                    selected_icon=icons.COTTAGE,
                    label="Home",
                )
            ],
            trailing=IconButton(icon=icons.SETTINGS, on_click=self.show_config_page),
            on_change=self.nav_clicked,
        )
        self.cont.content = self.nnrail

    def build(self):
        return self.cont

    def menu_clicked(self, e):
        self.nnrail.extended = not self.nnrail.extended
        self.update()

    def nav_clicked(self, e):
        if e.control.selected_index == 0:
            self.page.go("/home")
            self.route.bar.set_title("Pagina Inicial")
            self.route.page.update()
            self.update()

    def show_config_page(self, e):
        dialog = SetGeneralConfig(self.route)
        self.route.page.dialog = dialog
        dialog.open = True
        self.route.page.update()
