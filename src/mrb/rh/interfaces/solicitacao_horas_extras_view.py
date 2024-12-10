from datetime import datetime
import flet as ft
import requests

from src.mrb.common.lib.iso_to_date import iso_to_date
from src.mrb.common.lib.aviso import Aviso
from src.mrb.common.config import ApiConfiguration
from src.mrb.common.interfaces.auth.auth_session import AuthSession
from src.mrb.common.interfaces.botoes_menu_principal import BotoesMenuPrincipal
from src.mrb.common.interfaces.navigation_bar import NavigationBar

STATUS_APROVACAO = {
    "0": "Digitação",
    "1": "Aguardando aprovação",
    "2": "Aprovada",
    "3": "Rejeitada",
    "4": "Realizada",
}


class SolicitacaoHorasExtras:
    def __init__(
        self,
        page: ft.Page,
        navigation_bar: NavigationBar,
        botoes_menu_principal: BotoesMenuPrincipal,
    ) -> None:
        self.page = page
        self.navigation_bar = navigation_bar
        self.botoes_menu_principal = botoes_menu_principal

        self.pagina_atual_browse = 0
        self.total_paginas_browse = ft.Text("0")
        self.botao_primeira_pagina = ft.IconButton(
            icon=ft.icons.KEYBOARD_DOUBLE_ARROW_LEFT_OUTLINED,
            icon_size=40,
            disabled=True,
            tooltip="Ir para a primeira página",
            on_click=lambda _: self.vai_para_pagina(1),
        )
        self.botao_pagina_anterior = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_LEFT_OUTLINED,
            icon_size=40,
            disabled=True,
            tooltip="Ir para a página anterior",
            on_click=lambda _: self.vai_para_pagina(self.pagina_atual_browse - 1),
        )
        self.campo_pagina_atual = ft.TextField(
            value="1",
            label="Página",
            text_align=ft.TextAlign.CENTER,
            dense=True,
            tooltip="Digite o número da página e pressione <enter>",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self.on_change_digita_pagina(e),
            on_submit=lambda e: self.enter_pagina_atual(e),
            disabled=True,
        )
        self.botao_proxima_pagina = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_RIGHT_OUTLINED,
            icon_size=40,
            disabled=True,
            tooltip="Ir para a próxima página",
            on_click=lambda _: self.vai_para_pagina(self.pagina_atual_browse + 1),
        )
        self.botao_ultima_pagina = ft.IconButton(
            icon=ft.icons.KEYBOARD_DOUBLE_ARROW_RIGHT_OUTLINED,
            icon_size=40,
            disabled=True,
            tooltip="Ir para a última página",
            on_click=lambda _: self.vai_para_pagina(
                int(self.total_paginas_browse.value)
            ),
        )

        self.botao_limpa_filtros = ft.IconButton(
            icon=ft.icons.CLEAR_ALL_OUTLINED,
            tooltip="Limpar filtros",
            on_click=lambda _: self.limpar_filtros(),
            disabled=True,
        )
        self.texto_data_de = ft.TextField(
            dense=True,
            on_change=lambda e: self.preenche_data(e),
            width=120,
            hint_text="  /  /    ",
            data="",
        )
        self.texto_data_ate = ft.TextField(
            dense=True,
            on_change=lambda e: self.preenche_data(e),
            width=120,
            hint_text="  /  /    ",
            data="",
        )
        self.seletor_aguardando_aprovacao = ft.Switch(
            label="Apenas aguardando aprovação",
            value=False,
            on_change=lambda _: self.carrega_solicitacoes(),
        )
        self.botao_nova_solicitacao = ft.IconButton(
            icon=ft.icons.ADD_OUTLINED,
            tooltip="Nova Solicitação de Hora Extra",
            icon_color="primary",
            icon_size=36,
            on_click=self.nova_solicitacao_hora_extra,
        )
        self.browse_solicitacoes = ft.DataTable(
            expand=True,
            divider_thickness=0.4,
            sort_ascending=True,
            columns=[
                ft.DataColumn(ft.Text("Ações")),
                ft.DataColumn(ft.Text("Id")),
                ft.DataColumn(ft.Text("Dt. Planejada")),
                ft.DataColumn(ft.Text("Qtd. Horas")),
                ft.DataColumn(ft.Text("Dt. Solicitação")),
                ft.DataColumn(ft.Text("Motivo")),
                ft.DataColumn(ft.Text("Status Aprovação")),
                ft.DataColumn(ft.Text("Dt. Aprovação")),
                ft.DataColumn(ft.Text("Matr. Aprovador")),
                ft.DataColumn(ft.Text("Comentário")),
            ],
            rows=[],
        )
        self.coluna_painel_visualizacao = ft.Column()
        self.cartao_painel_visualizacao = ft.Card(
            elevation=1.5,
            animate_scale=200,
            surface_tint_color=ft.colors.INVERSE_PRIMARY,
            content=ft.Container(padding=10, content=self.coluna_painel_visualizacao),
            visible=False,
        )

    def preenche_data(self, e):
        digits_only = "".join(filter(str.isdigit, e.control.value))

        formatted = ""
        if len(digits_only) > 0:
            formatted += digits_only[:2]
        if len(digits_only) > 2:
            formatted += "/" + digits_only[2:4]
        if len(digits_only) > 4:
            formatted += "/" + digits_only[4:8]
        if len(digits_only) == 8:
            try:
                datetime.strptime(e.control.value, "%d/%m/%Y")

            except ValueError:
                Aviso(
                    self.page, content="A data digitada é inválida!", actions=["Ok"]
                ).exibir()
                formatted = e.control.data

        # Se a data formatada é vazia ou tem tamanho igual a 10 e é diferente da anterior, executa o filtro
        if (
            len(formatted) == 0 or len(formatted) == 10
        ) and not formatted == e.control.data:
            e.control.data = formatted
            self.carrega_solicitacoes()

        e.control.value = formatted

        e.control.update()

    def on_change_digita_pagina(self, e):
        if not e.control.value.isdigit():
            e.control.value = "".join(filter(str.isdigit, e.control.value))

        e.control.update()

    def enter_pagina_atual(self, e):
        # Se valor digitado for inválido, atualiza o conteúdo com a página atual
        if (
            e.control.value == ""
            or int(e.control.value) < 1
            or int(e.control.value) > int(self.total_paginas_browse.value)
        ):
            e.control.value = str(self.pagina_atual_browse)
            self.atualiza_barra_navegacao()

        else:
            self.vai_para_pagina(int(e.control.value))

    def vai_para_pagina(self, pagina_destino: int):
        self.pagina_atual_browse = pagina_destino
        self.campo_pagina_atual.value = str(pagina_destino)
        self.carrega_solicitacoes()

    def atualiza_barra_navegacao(self):
        if not self.campo_pagina_atual.value == "":
            self.botao_primeira_pagina.disabled = not (
                int(self.campo_pagina_atual.value) > 1
                and int(self.total_paginas_browse.value) > 1
            )
            self.botao_pagina_anterior.disabled = not (
                int(self.campo_pagina_atual.value) > 1
                and int(self.total_paginas_browse.value) > 1
            )
            self.campo_pagina_atual.disabled = (
                not int(self.total_paginas_browse.value) > 1
            )
            self.botao_proxima_pagina.disabled = not (
                int(self.campo_pagina_atual.value)
                < int(self.total_paginas_browse.value)
                and int(self.total_paginas_browse.value) > 1
            )
            self.botao_ultima_pagina.disabled = not (
                int(self.campo_pagina_atual.value)
                < int(self.total_paginas_browse.value)
                and int(self.total_paginas_browse.value) > 1
            )
            self.page.update()

    def get_solicitacao_horas_extras(self):
        conteudo_solicitacao = ft.Container(
            padding=0,
            border_radius=5,
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Container(
                                    expand=5,
                                    border_radius=5,
                                    padding=15,
                                    content=ft.Column(
                                        expand=True,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=20,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Row(
                                                spacing=20,
                                                controls=[
                                                    self.botao_limpa_filtros,
                                                    ft.Text("A partir da data:"),
                                                    self.texto_data_de,
                                                    ft.Text("Até a data:"),
                                                    self.texto_data_ate,
                                                    self.seletor_aguardando_aprovacao,
                                                    self.botao_nova_solicitacao,
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                            ),
                                            ft.Row(
                                                spacing=20,
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                controls=[
                                                    self.botao_primeira_pagina,
                                                    self.botao_pagina_anterior,
                                                    self.campo_pagina_atual,
                                                    ft.Text("de"),
                                                    self.total_paginas_browse,
                                                    self.botao_proxima_pagina,
                                                    self.botao_ultima_pagina,
                                                ],
                                            ),
                                            ft.ListView(
                                                expand=True,
                                                controls=[
                                                    ft.Row(
                                                        controls=[
                                                            self.browse_solicitacoes
                                                        ],
                                                        expand=True,
                                                        scroll=ft.ScrollMode.ADAPTIVE,
                                                    )
                                                ],
                                                auto_scroll=True,
                                            ),
                                        ],
                                    ),
                                ),
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    expand=2,
                                    border_radius=5,
                                    padding=15,
                                    content=ft.Column(
                                        expand=True,
                                        controls=[
                                            ft.Column(
                                                horizontal_alignment="center",
                                                controls=[
                                                    self.cartao_painel_visualizacao
                                                ],
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    )
                ]
            ),
        )
        return ft.View(
            route="/solicita_he",
            padding=0,
            controls=[
                self.navigation_bar.get_navigation_bar("Solicitações Horas Extras"),
                ft.Row(
                    controls=[
                        self.botoes_menu_principal.get_botoes_menu_principal(),
                        ft.Container(
                            content=conteudo_solicitacao,
                            alignment=ft.alignment.center,
                            expand=True,
                            padding=0,
                            margin=0,
                        ),
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
        )

    def carrega_solicitacoes(self):
        auth_session = AuthSession()
        pagina_destino = self.pagina_atual_browse if self.pagina_atual_browse > 0 else 1
        parametros_requisicao = {
            "matricula": auth_session.user_data["dados_cadastro_recursos"]["matricula"],
            "pagina": str(pagina_destino),
        }

        if self.seletor_aguardando_aprovacao.value:
            parametros_requisicao["status_aprovacao"] = "1"

        if len(self.texto_data_de.data) == 10:
            parametros_requisicao["data_de"] = datetime.strptime(
                self.texto_data_de.data, "%d/%m/%Y"
            )

        if len(self.texto_data_ate.data) == 10:
            parametros_requisicao["data_ate"] = datetime.strptime(
                self.texto_data_ate.data, "%d/%m/%Y"
            )

        response_solicitacoes = requests.get(
            headers={"Authorization": f"Bearer {auth_session.token}"},
            url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/solicitacao_horas_extras",
            params=parametros_requisicao,
        )

        if response_solicitacoes.status_code == 200:
            if len(parametros_requisicao) > 2:
                self.botao_limpa_filtros.disabled = False

            self.cartao_painel_visualizacao.visible = False
            self.browse_solicitacoes.rows.clear()
            retorno_solicitacoes = response_solicitacoes.json()
            # Se o total de páginas resultado for menor que a página atual, muda a página para 1 e repete a requisição
            if (
                retorno_solicitacoes["total_de_paginas"] < pagina_destino
                and retorno_solicitacoes["total_de_paginas"] > 0
            ):
                self.vai_para_pagina(1)
                pass

            self.pagina_atual_browse = retorno_solicitacoes["pagina"]
            self.total_paginas_browse.value = str(
                retorno_solicitacoes["total_de_paginas"]
            )

            for solicitacao in retorno_solicitacoes["solicitacoes_horas_extras"]:
                botoes_da_linha = [
                    ft.IconButton(
                        icon=ft.icons.EDIT_OUTLINED,
                        icon_color="blue",
                        data=solicitacao["id"],
                        tooltip="Editar solicitação",
                        on_click=self.editar_solicitacao,
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE_OUTLINED,
                        icon_color="red",
                        data=solicitacao["id"],
                        tooltip="Apagar solicitacao",
                        on_click=self.apagar_solicitacao,
                    ),
                ]
                if solicitacao["status_aprovacao"] == "0":
                    botoes_da_linha.append(
                        ft.IconButton(
                            icon=ft.icons.ADD_MODERATOR_OUTLINED,
                            icon_color="green",
                            data=(
                                solicitacao["id"],
                                len(self.browse_solicitacoes.rows),
                            ),
                            tooltip="Solicitar liberação",
                            on_click=self.solicitar_liberacao,
                        )
                    )

                self.browse_solicitacoes.rows.append(
                    ft.DataRow(
                        data=solicitacao,
                        cells=[
                            ft.DataCell(
                                ft.Row(botoes_da_linha),
                            ),
                            ft.DataCell(ft.Text(str(solicitacao["id"]))),
                            ft.DataCell(
                                ft.Text(iso_to_date(solicitacao["data_planejada"]))
                            ),
                            ft.DataCell(ft.Text(solicitacao["total_horas_planejada"])),
                            ft.DataCell(
                                ft.Text(iso_to_date(solicitacao["data_solicitacao"]))
                            ),
                            ft.DataCell(ft.Text(solicitacao["motivo"])),
                            ft.DataCell(
                                ft.Text(
                                    STATUS_APROVACAO[solicitacao["status_aprovacao"]]
                                )
                            ),
                            ft.DataCell(
                                ft.Text(iso_to_date(solicitacao["data_aprovacao"]))
                            ),
                            ft.DataCell(ft.Text(solicitacao["matricula_aprovador"])),
                            ft.DataCell(ft.Text(solicitacao["comentario_aprovador"])),
                        ],
                        on_select_changed=lambda e: self.clique_browse_solicitacoes(
                            e.control.data
                        ),
                    )
                )
            self.atualiza_barra_navegacao()
            self.page.update()

        else:
            Aviso(
                self.page,
                content=f"Falha na requisição de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                title="Requisição de Solicitações",
                actions=["Fechar"],
            ).exibir()

    def solicitar_liberacao(self, e):
        confirma_solicitar_liberacao = (
            Aviso(
                self.page,
                content=f"Confirma o envio da Solicitação de Hora Extra Id {e.control.data[0]} para liberação do Gestor?",
                title="Solicita liberação",
                actions=["Sim", "Não"],
            ).exibir()
            == 0
        )
        if confirma_solicitar_liberacao:
            dados_solicitacao = self.browse_solicitacoes.rows[e.control.data[1]].data
            dados_solicitacao["status_aprovacao"] = "1"
            if self.envia_alteracao_solicitacao(dados_solicitacao):
                self.carrega_solicitacoes()

    def envia_alteracao_solicitacao(self, dados_solicitacao) -> bool:
        retorno_atualizacao = True
        auth_session = AuthSession()
        response_solicitacoes = requests.put(
            headers={"Authorization": f"Bearer {auth_session.token}"},
            url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/solicitacao_horas_extras",
            json=dados_solicitacao,
        )
        if not response_solicitacoes.status_code == 200:
            Aviso(
                self.page,
                content=f"Falha na atualização de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                title="Alteração de Solicitação",
                actions=["Fechar"],
            ).exibir()
            retorno_atualizacao = False
        return retorno_atualizacao

    def clique_browse_solicitacoes(self, solicitacao: dict):
        self.cartao_painel_visualizacao.visible = True
        self.coluna_painel_visualizacao.controls.clear()
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"Dados da Solicitação Id: {solicitacao['id']}",
                        text_align=ft.TextAlign.CENTER,
                        expand=True,
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                    )
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Matrícula: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(solicitacao["matricula"]),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Data Planejada: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(iso_to_date(solicitacao["data_planejada"])),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Quantidade de Horas Planejadas: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(solicitacao["total_horas_planejada"]),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(ft.Divider())
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Data da Solicitação: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(iso_to_date(solicitacao["data_solicitacao"])),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Motivo: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(solicitacao["motivo"]),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(ft.Divider())
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Status da Aprovação: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(STATUS_APROVACAO[solicitacao["status_aprovacao"]]),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Data da Aprovação: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(iso_to_date(solicitacao["data_aprovacao"])),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Matrícula do Aprovador: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(solicitacao["matricula_aprovador"]),
                ],
            )
        )
        self.coluna_painel_visualizacao.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                controls=[
                    ft.Text(
                        "Comentários: ",
                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    ),
                    ft.Text(solicitacao["comentario_aprovador"]),
                ],
            )
        )
        self.cartao_painel_visualizacao.update()

    def apagar_solicitacao(self, e):
        confirma_apagar_liberacao = (
            Aviso(
                self.page,
                content=f"Confirma excluir a Solicitação de Hora Extra Id {e.control.data}?\n\nEsta operação não poderá ser desfeita!",
                title="Exclusão de Solicitação",
                actions=["Sim", "Não"],
            ).exibir()
            == 0
        )
        if confirma_apagar_liberacao:
            auth_session = AuthSession()
            response_solicitacoes = requests.delete(
                headers={"Authorization": f"Bearer {auth_session.token}"},
                url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/solicitacao_horas_extras/{e.control.data}",
            )
            if (
                response_solicitacoes.status_code == 204
                or response_solicitacoes.status_code == 200
            ):
                self.carrega_solicitacoes()

            else:
                Aviso(
                    self.page,
                    content=f"Falha na exclusão de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Alteração de Solicitação",
                    actions=["Fechar"],
                ).exibir()

    def editar_solicitacao(self, e):
        print("Editar solicitação")

    def limpar_filtros(self):
        self.texto_data_de.value = ""
        self.texto_data_de.data = ""
        self.texto_data_ate.value = ""
        self.texto_data_ate.data = ""
        self.seletor_aguardando_aprovacao.value = False
        self.botao_limpa_filtros.disabled = True
        self.carrega_solicitacoes()

    def nova_solicitacao_hora_extra(self):
        print("Nova solicitação de hora extra")
