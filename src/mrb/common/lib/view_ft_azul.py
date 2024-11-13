import flet as ft


class ViewFtAzul(ft.View):
    def __init__(self, route, controls=None, **kwargs):
        super().__init__(
            route=route,
            controls=controls or [],
            bgcolor=ft.colors.BLUE,
            **kwargs,
        )
