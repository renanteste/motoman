import time
import flet as ft


class Aviso:

    def __init__(
        self,
        page,
        content: str = "",
        modal: bool = False,
        title: str = "Aviso",
        actions: list = [],
    ) -> None:
        self.page = page
        self.content = content
        self.modal = modal
        self.title = title
        self.actions = actions
        self.alert_dialog = None
        self.acao_selecionada = None
        self.finalizado = False

    def fechar(self):
        if self.alert_dialog:
            self.page.close(self.alert_dialog)

    def opcao_selecionada(self, index):
        self.acao_selecionada = index
        self.fechar()
        self.finalizado = True

    def exibir(self):
        actions = [
            ft.ElevatedButton(
                text=option,
                on_click=lambda e, i=i: self.opcao_selecionada(i),
                autofocus=True,
            )
            for i, option in enumerate(self.actions)
        ]

        self.alert_dialog = ft.AlertDialog(
            modal=self.modal,
            title=ft.Text(self.title),
            content=ft.Text(self.content),
            actions=actions,
        )
        self.page.overlay.append(self.alert_dialog)
        self.alert_dialog.open = True
        self.page.update()

        # Aguarda a finalização do usuário
        while not self.finalizado:
            time.sleep(0.5)

        return self.acao_selecionada
