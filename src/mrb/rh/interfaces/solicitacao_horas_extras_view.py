from datetime import datetime
from decimal import Decimal
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

        # Componentes da paginação
        self.pagina_atual_browse = 0
        self.total_paginas_browse = ft.Text("0")
        self.botao_primeira_pagina = ft.IconButton(
            icon=ft.icons.KEYBOARD_DOUBLE_ARROW_LEFT_OUTLINED,
            disabled=True,
            tooltip="Ir para a primeira página",
            on_click=lambda _: self.vai_para_pagina(1),
        )
        self.botao_pagina_anterior = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_LEFT_OUTLINED,
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
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self.on_change_digita_pagina(e),
            on_submit=lambda e: self.enter_pagina_atual(e),
            disabled=True,
        )
        self.botao_proxima_pagina = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_RIGHT_OUTLINED,
            disabled=True,
            tooltip="Ir para a próxima página",
            on_click=lambda _: self.vai_para_pagina(self.pagina_atual_browse + 1),
        )
        self.botao_ultima_pagina = ft.IconButton(
            icon=ft.icons.KEYBOARD_DOUBLE_ARROW_RIGHT_OUTLINED,
            disabled=True,
            tooltip="Ir para a última página",
            on_click=lambda _: self.vai_para_pagina(
                int(self.total_paginas_browse.value)
            ),
        )

        # Componentes da filtragem de registros
        self.botao_limpa_filtros = ft.IconButton(
            icon=ft.icons.FILTER_ALT_OFF_OUTLINED,
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
            text_size=14,
        )
        self.texto_data_ate = ft.TextField(
            dense=True,
            on_change=lambda e: self.preenche_data(e),
            width=120,
            hint_text="  /  /    ",
            data="",
            text_size=14,
        )
        self.seletor_aguardando_aprovacao = ft.Switch(
            label="Apenas aguardando aprovação",
            value=False,
            on_change=lambda _: self.carrega_solicitacoes(),
            height=40,
        )

        # Inclusão de novo registro
        self.botao_nova_solicitacao = ft.IconButton(
            icon=ft.icons.ADD_OUTLINED,
            tooltip="Nova Solicitação de Hora Extra",
            icon_color="primary",
            on_click=lambda _: self.interface_edicao_hora_extra(),
        )

        # Componentes do grid de registros
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

        # Componentes do painel lateral direito
        self.coluna_painel_visualizacao = ft.Column()
        self.cartao_painel_visualizacao = ft.Card(
            elevation=1.5,
            animate_scale=200,
            surface_tint_color=ft.colors.INVERSE_PRIMARY,
            content=ft.Container(padding=10, content=self.coluna_painel_visualizacao),
            visible=False,
        )

        # Componentes do painel de edição
        self.dados_solicitacoes = None  # Utilizado como pivô para salvar os registros
        self.titulo_painel_edicao = ft.Text(
            "",
            text_align=ft.TextAlign.CENTER,
            expand=True,
            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
        )
        self.campo_data_planejada = ft.TextField(
            dense=True,
            on_change=lambda e: self.preenche_data(e, atualiza_dados=False),
            width=120,
            hint_text="  /  /    ",
            data="",
            bgcolor=ft.colors.WHITE,
            on_blur=lambda e: self.on_blur_data_planejada(e),
        )
        self.campo_quantidade_horas = ft.TextField(
            dense=True,
            on_change=lambda e: self.preenche_horas(e),
            width=120,
            hint_text="0,00",
            data="",
            bgcolor=ft.colors.WHITE,
            tooltip="Digitar o total de horas decimais planejadas. Ex.: 2h 30m = 2,50h.",
            text_align=ft.TextAlign.RIGHT,
        )
        self.campo_motivo = ft.TextField(
            dense=True,
            expand=True,
            bgcolor=ft.colors.WHITE,
            tooltip="Informe o motivo da necessidade de horas extras",
            max_length=250,
            multiline=True,
            on_change=lambda e: self.on_change_motivo(e),
        )
        self.matricula_painel_edicao = ft.Text("")
        self.coluna_painel_edicao = ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[self.titulo_painel_edicao],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Matrícula:", theme_style=ft.TextThemeStyle.LABEL_LARGE
                        ),
                        self.matricula_painel_edicao,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Data Planejada:", theme_style=ft.TextThemeStyle.LABEL_LARGE
                        ),
                        self.campo_data_planejada,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Quantidade de Horas Planejadas:",
                            theme_style=ft.TextThemeStyle.LABEL_LARGE,
                        ),
                        self.campo_quantidade_horas,
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Text("Motivo:", theme_style=ft.TextThemeStyle.LABEL_LARGE)
                    ]
                ),
                ft.Row(controls=[self.campo_motivo]),
                ft.Divider(),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.CHECK_CIRCLE_OUTLINE_OUTLINED,
                            icon_color=ft.colors.GREEN,
                            icon_size=40,
                            tooltip="Salvar",
                            on_click=lambda _: self.salvar_edicao(
                                self.dados_solicitacoes
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.icons.CANCEL_OUTLINED,
                            icon_color=ft.colors.RED,
                            icon_size=40,
                            tooltip="Cancelar",
                            on_click=lambda _: self.cancelar_edicao(),
                        ),
                    ],
                ),
            ]
        )
        self.cartao_painel_edicao = ft.Card(
            elevation=1.5,
            animate_scale=200,
            surface_tint_color=ft.colors.INVERSE_PRIMARY,
            content=ft.Container(padding=10, content=self.coluna_painel_edicao),
            visible=False,
        )

    def habilitar_desabilitar_edicao(self):
        """
        Método faz a mudança entre os painéis de visualização e edição.
        \n
        Quando é chamado, desativa o que está ativo e vice-versa.
        """
        self.cartao_painel_edicao.visible = not self.cartao_painel_edicao.visible
        self.cartao_painel_visualizacao.visible = (
            not self.cartao_painel_visualizacao.visible
        )
        self.botao_nova_solicitacao.disabled = not self.botao_nova_solicitacao.disabled
        self.page.update()

    def limpa_campos_edicao(self):
        """
        Método deve ser invocado após o fechamento da tela de edição.
        \n
        Reponsável por limpar o conteúdo dos campos da tela para não interferir na próxima operação.
        """
        self.campo_data_planejada.value = ""
        self.campo_quantidade_horas.value = ""
        self.campo_motivo.value = ""

    def cancelar_edicao(self):
        """
        Fecha a tela de edição sem salvar os dados e após confirmação do usuário
        """
        if (
            Aviso(
                self.page,
                content="Descartar as informações digitadas?",
                title="Atenção",
                actions=["Sim", "Não"],
            ).exibir()
            == 0
        ):
            self.habilitar_desabilitar_edicao()
            self.limpa_campos_edicao()

    def salvar_edicao(self, dados_solicitacao: dict = None):
        """
        Valida os dados digitados pelo usuário.
        \n
        Se os dados estão válidos, monta o dicionário de requisição e direciona ao método para incluir ou alterar via API.
        \n
        Se o argumento 'dados_solicitacao' for enviado, indica que é um processo de alteração, não inclusão.
        """
        if (
            self.campo_data_planejada.value == ""
            or self.campo_motivo.value == ""
            or self.campo_quantidade_horas.value == ""
        ):
            Aviso(
                self.page,
                content="Preencha todos os campos antes de salvar!",
                title="Atenção",
                actions=["Ok"],
            ).exibir()

        elif (
            Aviso(
                self.page,
                content="Salvar as informações digitadas?",
                title="Atenção",
                actions=["Sim", "Não"],
            ).exibir()
            == 0
        ):
            auth_session = AuthSession()
            if dados_solicitacao:
                # Alteracao
                solicitacao_horas_extras = dados_solicitacao

            else:
                # Inclusao
                solicitacao_horas_extras = {}
                solicitacao_horas_extras["matricula"] = auth_session.user_data[
                    "dados_cadastro_recursos"
                ]["matricula"]
                solicitacao_horas_extras["data_solicitacao"] = (
                    datetime.now().isoformat()
                )

            # Alimenta os atributos com os dados da interface
            solicitacao_horas_extras["data_planejada"] = datetime.strptime(
                self.campo_data_planejada.value, "%d/%m/%Y"
            ).isoformat()
            solicitacao_horas_extras["motivo"] = self.campo_motivo.value
            solicitacao_horas_extras["total_horas_planejada"] = (
                self.campo_quantidade_horas.value.replace(",", ".")
            )
            solicitacao_horas_extras["status_aprovacao"] = "0"

            if dados_solicitacao:
                retorno_envio = self.envia_alteracao_solicitacao(
                    solicitacao_horas_extras
                )

            else:
                retorno_envio = self.envia_inclusao_solicitacao(
                    solicitacao_horas_extras
                )

            if retorno_envio:
                self.habilitar_desabilitar_edicao()
                self.limpa_campos_edicao()
                self.carrega_solicitacoes()

    def envia_inclusao_solicitacao(self, solicitacao_horas_extras: dict) -> bool:
        """
        Faz o request da API para inclusão dos dados (post) e trata o retorno obtido.
        \n
        Retorna True se a transação foi bem sucedida.
        """
        auth_session = AuthSession()
        retorno_envio = False

        response_solicitacoes = requests.post(
            headers={"Authorization": f"Bearer {auth_session.token}"},
            url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/solicitacao_horas_extras",
            json=solicitacao_horas_extras,
        )

        if response_solicitacoes.status_code == 200:
            retorno_envio = True
            dados_retornados = response_solicitacoes.json()
            Aviso(
                self.page,
                content=f"Salva com id {dados_retornados[0]['id']}!",
                title="Sucesso",
                actions=["Ok"],
            ).exibir()

        else:
            if response_solicitacoes.status_code == 401:
                self.page.go("/logout")

            else:
                Aviso(
                    self.page,
                    content=f"Falha na requisição de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Requisição de Solicitações",
                    actions=["Fechar"],
                ).exibir()

        return retorno_envio

    def preenche_horas(self, e):
        """
        Método trata a digitação do campo de quantidade de horas decimais.
        \n
        Permite apenas números e preenche automaticamente a vírgula decimal e o formato do dado digitado.
        \n
        Caso o usuário informe um conteúdo inválido, restaura o conteúdo anterior utilizando a
        propriedade 'data' do TextField como pivô.
        """
        apenas_numeros = "".join(c for c in e.control.value if c.isdigit())

        apenas_numeros = apenas_numeros.zfill(3)

        inteiro = apenas_numeros[:-2]
        decimal = apenas_numeros[-2:]

        if int(inteiro) > 24 or (int(inteiro) == 24 and int(decimal) > 0):
            Aviso(
                self.page,
                content="Total de horas não pode ser maior que 24!",
                title="Atenção",
                actions=["Ok"],
            ).exibir()
            e.control.value = e.control.data

        else:
            e.control.value = f"{int(inteiro)},{decimal}"
            e.control.data = e.control.value

        e.control.update()

    def on_blur_data_planejada(self, e):
        """
        Método executado ao entrar ou sair do TextField data data planejada.
        \n
        Garante que o usuário tenha informado uma data válida, limpando o conteúdo do campo em caso contrário.
        """
        if e.control.value and len(e.control.value) == 10:
            try:
                datetime.strptime(e.control.value, "%d/%m/%Y")

            except ValueError:
                e.control.value = ""
                e.control.update()

    def preenche_data(self, e, atualiza_dados: bool = True):
        """
        Método genérico para os campos de data.
        \n
        Garante a formatação e que seja uma data válida.
        \n
        Atualiza os registros do browse caso o argumento 'atualiza_dados' seja True.
        """
        somente_digitos = "".join(filter(str.isdigit, e.control.value))

        formatado = ""
        if len(somente_digitos) > 0:
            formatado += somente_digitos[:2]
        if len(somente_digitos) > 2:
            formatado += "/" + somente_digitos[2:4]
        if len(somente_digitos) > 4:
            formatado += "/" + somente_digitos[4:8]
        if len(somente_digitos) == 8:
            try:
                datetime.strptime(e.control.value, "%d/%m/%Y")

            except ValueError:
                Aviso(
                    self.page, content="A data digitada é inválida!", actions=["Ok"]
                ).exibir()
                formatado = e.control.data

        # Se a data formatada é vazia ou tem tamanho igual a 10 e é diferente da anterior, executa o filtro
        if (
            len(formatado) == 0 or len(formatado) == 10
        ) and not formatado == e.control.data:
            e.control.data = formatado

            if atualiza_dados:
                self.carrega_solicitacoes()

        e.control.value = formatado

        e.control.update()

    def on_change_digita_pagina(self, e):
        """
        Garante que o usuário só irá digitar números no campo página do controle de paginação do browse.
        """
        if not e.control.value.isdigit():
            e.control.value = "".join(filter(str.isdigit, e.control.value))

        e.control.update()

    def on_change_motivo(self, e):
        """
        Método remove <enter> do motivo da necessidade de horas extras
        """
        e.control.value = e.control.value.replace("\n", "")
        e.control.update()

    def enter_pagina_atual(self, e):
        """
        Método executado quando o usuário pressionar <enter> no campo de página atual no controle de paginação do browse.
        \n
        Valida se o número de página digitado é válido e executa o método da mudança de página dos registros.
        """
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
        """
        Altera a página atual do browse de registros para a página enviada no argumento 'pagina_destino'
        """
        self.pagina_atual_browse = pagina_destino
        self.campo_pagina_atual.value = str(pagina_destino)
        self.carrega_solicitacoes()

    def atualiza_barra_navegacao(self):
        """
        Método habilita ou desabilita os botões da barra de paginação de acordo com a página atual e
        a quantidade de páginas.
        """
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
        """
        Montagem e retorno da view com a tela de solicitações de horas extras
        """
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
                                                    ft.Text("Dt. Planejada de:"),
                                                    self.texto_data_de,
                                                    ft.Text("Até:"),
                                                    self.texto_data_ate,
                                                    self.seletor_aguardando_aprovacao,
                                                    self.botao_nova_solicitacao,
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            ),
                                            ft.Row(
                                                spacing=20,
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
                                                    self.cartao_painel_visualizacao,
                                                    self.cartao_painel_edicao,
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
        """
        Método para recuperação dos dados de solicitações de horas extras da api.
        """
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
                        data=(solicitacao["id"], len(self.browse_solicitacoes.rows)),
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

            if retorno_solicitacoes["solicitacoes_horas_extras"]:
                self.clique_browse_solicitacoes(
                    retorno_solicitacoes["solicitacoes_horas_extras"][0]
                )

            self.atualiza_barra_navegacao()
            self.page.update()

        else:
            if response_solicitacoes.status_code == 401:
                self.page.go("/logout")

            else:
                Aviso(
                    self.page,
                    content=f"Falha na requisição de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Requisição de Solicitações",
                    actions=["Fechar"],
                ).exibir()

    def solicitar_liberacao(self, e):
        """
        Método altera o status da solicitação de liberação para 1=Aguardando aprovação.
        """
        # Não é necessário verificar o status atual, pois o botão só fica disponível quando o status é igual a "0"
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

    def envia_alteracao_solicitacao(self, dados_solicitacao: dict) -> bool:
        """
        Consome o PUT da API para realizar a persistência da alteração da solicitação de hora extra.
        \n
        Recebe os dados pelo argumento 'dados_solicitacao'.
        """
        retorno_atualizacao = True
        auth_session = AuthSession()
        response_solicitacoes = requests.put(
            headers={"Authorization": f"Bearer {auth_session.token}"},
            url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/solicitacao_horas_extras",
            json=dados_solicitacao,
        )
        if not response_solicitacoes.status_code == 200:
            if response_solicitacoes.status_code == 401:
                self.page.go("/logout")

            else:
                Aviso(
                    self.page,
                    content=f"Falha na atualização de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Alteração de Solicitação",
                    actions=["Fechar"],
                ).exibir()
                retorno_atualizacao = False
        return retorno_atualizacao

    def clique_browse_solicitacoes(self, solicitacao: dict):
        """
        Atualiza o cartão de visualização da solicitação de hora extra a partir da linha clicada no browse.
        """
        if not self.cartao_painel_edicao.visible:
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
                        ft.Text(solicitacao["motivo"], expand=True),
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
                        ft.Text(solicitacao["comentario_aprovador"], expand=True),
                    ],
                )
            )
            self.page.update()

    def apagar_solicitacao(self, e):
        """
        Consome o método DELETE da api para realizar a exclusão de uma solicitação de hora extra.
        \n
        Acionado pelo clique no botão posicionado em cada linha de solicitação.
        """
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
                if response_solicitacoes.status_code == 401:
                    self.page.go("/logout")

                else:
                    Aviso(
                        self.page,
                        content=f"Falha na exclusão de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                        title="Alteração de Solicitação",
                        actions=["Fechar"],
                    ).exibir()

    def editar_solicitacao(self, e):
        """
        Método para controlar a chamada para edição da solicitação de hora extra.
        \n
        Acionado pelo clique no botão posicionado em cada linha de solicitação.
        """
        if self.cartao_painel_edicao.visible:
            Aviso(
                self.page,
                content="Confirme ou cancele a edição atual antes de abrir outra!",
                title="Atenção",
                actions=["Ok"],
            ).exibir()

        else:
            self.interface_edicao_hora_extra(
                self.browse_solicitacoes.rows[e.control.data[1]].data
            )

    def limpar_filtros(self):
        """
        Limpa os parâmetros de seleção de registros no browse e chama sua atualização.
        """
        self.texto_data_de.value = ""
        self.texto_data_de.data = ""
        self.texto_data_ate.value = ""
        self.texto_data_ate.data = ""
        self.seletor_aguardando_aprovacao.value = False
        self.botao_limpa_filtros.disabled = True
        self.carrega_solicitacoes()

    def interface_edicao_hora_extra(self, dados_solicitacao: dict = None):
        """
        Controla a abertura da tela de edição das solicitações de horas extras.
        \n
        Se o argumento 'dados_solicitacao' for enviado, é um processo de alteração. Caso contrário, trata-se de inclusão.
        """
        if dados_solicitacao:
            self.titulo_painel_edicao.value = (
                f"Dados da Solicitação Id: {dados_solicitacao['id']}"
            )
            self.campo_data_planejada.value = iso_to_date(
                dados_solicitacao["data_planejada"]
            )
            self.campo_quantidade_horas.value = dados_solicitacao[
                "total_horas_planejada"
            ].replace(".", ",")
            self.campo_motivo.value = dados_solicitacao["motivo"]

        else:
            self.titulo_painel_edicao.value = "Dados da Nova Solicitação"

        auth_session = AuthSession()
        self.matricula_painel_edicao.value = auth_session.user_data[
            "dados_cadastro_recursos"
        ]["matricula"]

        self.dados_solicitacoes = dados_solicitacao

        self.habilitar_desabilitar_edicao()
