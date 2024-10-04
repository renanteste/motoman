import flet as ft
import requests
from src.mrb.common.config import ApiConfiguration
from src.mrb.common.lib import Aviso


def main(page: ft.Page):
    page.title = "Identificação do Usuário"
    page.bgcolor = ft.colors.BLUE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER

    def on_connect(e):
        print("on_route_change")
        if not matricula_input.visible:
            matricula_input.visible = True
            enviar_button.visible = True
            conteiner.content = None
            page.update()

    page.on_connect = on_connect

    # Função de envio
    def on_button_click(e):
        sucesso = False
        enviar_button.disabled = True
        enviar_button.update()
        matricula_input.disabled = True
        matricula_input.update()
        matricula = matricula_input.value
        aviso = Aviso(page, modal=True)

        if not matricula:
            aviso.content = "O campo de matrícula não pode estar vazio!"
            aviso.title = "Atenção"
            aviso.actions = ["Ok"]
            aviso.exibir()
        else:
            # Chama o endpoint
            try:
                response = requests.get(
                    f"http://{ApiConfiguration.rh.HOST}:{ApiConfiguration.rh.PORT}/authrhhe/{matricula}"
                )
                if not response.status_code == 200:
                    aviso.content = response.text
                    aviso.title = "Falha no login"
                    aviso.actions = ["Fechar"]
                    aviso.exibir()
                else:
                    sucesso = True

            except Exception as e:
                aviso.content = f"Erro: {e}"
                aviso.title = "Falha na conexão"
                aviso.actions = ["Fechar"]
                aviso.exibir()

        enviar_button.disabled = False
        matricula_input.disabled = False
        if sucesso:
            enviar_button.visible = False
            matricula_input.visible = False
            matricula_input.value = ""
            conteiner.content = ft.Text(
                "Verifique sua caixa de entrada!",
                theme_style=ft.TextThemeStyle.DISPLAY_SMALL,
                text_align=ft.TextAlign.CENTER,
                color=ft.colors.BLUE_ACCENT_700,
            )

        enviar_button.update()
        matricula_input.update()
        page.update()  # Atualiza a interface

    # Campo de entrada para a matrícula
    matricula_input = ft.TextField(
        label="Informe sua matrícula",
        max_length=4,
        width=250,
        bgcolor=ft.colors.WHITE,
        color=ft.colors.BLACK54,
        input_filter=ft.NumbersOnlyInputFilter(),
    )

    # Botão para enviar a matrícula
    enviar_button = ft.FilledButton(
        text="Enviar", on_click=lambda e: on_button_click(e)
    )

    titulo = ft.Text(
        value="Portal de Recursos Humanos", theme_style=ft.TextThemeStyle.DISPLAY_MEDIUM
    )
    conteiner = ft.Container(
        content=ft.Column(
            controls=[matricula_input, enviar_button],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=350,
        height=150,
        padding=20,
        border_radius=ft.border_radius.all(15),
        bgcolor=ft.colors.WHITE,
        alignment=ft.alignment.center,
    )

    # Adiciona os componentes à página
    page.add(titulo, conteiner)


# Executa a aplicação Flet
ft.app(target=main, port=8550, host="127.0.0.1")  # Acesse via http://<seu_ip>:5000
