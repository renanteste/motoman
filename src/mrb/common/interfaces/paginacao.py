import flet as ft

from typing import Callable


class Paginacao:
    def __init__(
        self,
        on_pagina_mudou: Callable[[int], None],
        pagina_inicial: int = 1,
        total_paginas: int = 1,
    ):
        self.on_pagina_mudou = on_pagina_mudou
        self.pagina_atual = pagina_inicial
        self.total_paginas = total_paginas

        # Componentes de navegação
        self.botao_primeira_pagina = ft.IconButton(
            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_OUTLINED,
            disabled=True,
            tooltip="Primeira página",
            on_click=lambda _: self.mudar_pagina(1),
        )
        self.botao_pagina_anterior = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_LEFT_OUTLINED,
            disabled=True,
            tooltip="Página anterior",
            on_click=lambda _: self.mudar_pagina(self.pagina_atual - 1),
        )
        self.campo_pagina_atual = ft.TextField(
            value=str(self.pagina_atual),
            text_align=ft.TextAlign.CENTER,
            dense=True,
            width=120,
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=self.submeter_pagina,
            label="Página",
            on_change=lambda e: self.on_change_digita_pagina(e),
        )
        self.botao_proxima_pagina = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_RIGHT_OUTLINED,
            disabled=True,
            tooltip="Próxima página",
            on_click=lambda _: self.mudar_pagina(self.pagina_atual + 1),
        )
        self.botao_ultima_pagina = ft.IconButton(
            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT_OUTLINED,
            disabled=True,
            tooltip="Última página",
            on_click=lambda _: self.mudar_pagina(self.total_paginas),
        )
        self.texto_total_paginas = ft.Text(f"de {self.total_paginas}")

        self.row_paginacao = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self.botao_primeira_pagina,
                self.botao_pagina_anterior,
                self.campo_pagina_atual,
                self.texto_total_paginas,
                self.botao_proxima_pagina,
                self.botao_ultima_pagina,
            ],
        )

        # self.atualiza_botoes()

    def mudar_pagina(self, pagina_destino: int):
        if 1 <= pagina_destino <= self.total_paginas:
            self.pagina_atual = pagina_destino
            self.campo_pagina_atual.value = str(pagina_destino)
            self.atualiza_botoes()
            self.on_pagina_mudou(pagina_destino)

    def submeter_pagina(self, e):
        if (
            e.control.value == ""
            or int(e.control.value) < 1
            or int(e.control.value) > self.total_paginas
        ):
            e.control.value = str(self.pagina_atual)
            self.atualiza_botoes()

        else:
            self.mudar_pagina(int(e.control.value))

    def atualiza_botoes(self):
        self.botao_primeira_pagina.disabled = self.pagina_atual == 1
        self.botao_pagina_anterior.disabled = self.pagina_atual == 1
        self.botao_proxima_pagina.disabled = self.pagina_atual == self.total_paginas
        self.botao_ultima_pagina.disabled = self.pagina_atual == self.total_paginas
        self.campo_pagina_atual.disabled = not self.total_paginas > 1

        self.texto_total_paginas.value = f"de {self.total_paginas}"
        self.campo_pagina_atual.update()
        self.row_paginacao.update()

    def get_paginacao(self):
        return self.row_paginacao

    def set_total_paginas(self, total_paginas: int):
        self.total_paginas = total_paginas

        # Se o total de páginas for menor que a página atual, muda a página para 1 e repete a requisição
        if total_paginas < self.pagina_atual:
            self.mudar_pagina(1)

        self.atualiza_botoes()

    def on_change_digita_pagina(self, e):
        """
        Garante que o usuário só irá digitar números no campo página do controle de paginação do browse.
        """
        if not e.control.value.isdigit():
            e.control.value = "".join(filter(str.isdigit, e.control.value))

        e.control.update()
