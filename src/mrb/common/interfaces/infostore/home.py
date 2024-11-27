from flet import UserControl, colors, Icon, icons, Container, Column, Row, Text


class Home(UserControl):
    def __init__(self, route):
        super().__init__()
        self.route = route
        self.COLOR = [
            colors.PRIMARY,
            colors.SECONDARY,
            colors.ON_PRIMARY_CONTAINER,
            colors.TERTIARY,
            colors.ON_SURFACE_VARIANT,
        ]

        self.icon = Icon(name=icons.ARROW_DROP_UP, color="green")

    def build(self):
        self.home_content = Container(
            expand=True,
            margin=35,
            content=Column(
                expand=True,
                spacing=40,
                controls=[
                    Row(
                        expand=4,
                        spacing=40,
                        controls=[
                            Text("Gráfico de Linha"),
                            Text("Gauge"),
                            Text("Barras"),
                        ],
                    ),
                    Row(
                        expand=5,
                        spacing=40,
                        controls=[
                            Text("Cartão do Cliente"),
                            Text("Cartão de Vendas"),
                            Text("Cartão de Produtos"),
                        ],
                    ),
                ],
            ),
        )

        self.content = Row(expand=True, spacing=10, controls=self.home_content)

        return self.content

    def initialize(self):
        self.route.menu.nnrail.selected_index = 0
        self.route.menu.update()
