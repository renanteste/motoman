import flet as ft

# Configurações
ITEMS_PER_PAGE = 50  # Quantos ícones por página


def main(page: ft.Page):
    page.title = "Visualizador de Ícones com Paginação"
    page.scroll = "auto"
    current_page = ft.Text(value="1", size=20)
    icons_list = []

    # Carregando os ícones do arquivo
    try:
        with open(
            "src/mrb/common/interfaces/teste_icones.py", "r", encoding="utf-8"
        ) as file:
            for line in file:
                # Verifica linhas que definem ícones
                if "=" in line and line.strip().split("=", 1)[0].isupper():
                    icon = line.split("=")[1].strip().replace('"', "").replace("'", "")
                    icons_list.append(icon)
    except FileNotFoundError:
        page.add(ft.Text("Arquivo teste_icones.py não encontrado.", color="red"))
        return

    if not icons_list:
        page.add(ft.Text("Nenhum ícone encontrado no arquivo.", color="red"))
        return

    # Calcula o total de páginas
    total_pages = (len(icons_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    # Função para carregar a página atual
    def load_page(page_number):
        """Carrega os ícones da página especificada."""
        start_index = (page_number - 1) * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        displayed_icons = icons_list[start_index:end_index]

        # Dividindo os ícones em 3 colunas
        column_count = 3
        rows = [[] for _ in range(column_count)]

        for i, icon_name in enumerate(displayed_icons):
            rows[i % column_count].append(
                ft.Row(
                    controls=[
                        ft.Icon(icon_name, size=50),  # Tamanho do ícone ajustado
                        ft.Text(icon_name, expand=True),  # Nome do ícone
                    ],
                    spacing=10,
                )
            )

        # Criando colunas
        columns = [ft.Column(controls=row, expand=True, spacing=20) for row in rows]

        # Atualizando o container
        icons_container.controls = [ft.Row(controls=columns, spacing=20, expand=True)]
        icons_container.update()

    # Função para ir para a página anterior
    def go_to_previous_page(e):
        page_number = max(1, int(current_page.value) - 1)
        current_page.value = str(page_number)
        current_page.update()
        load_page(page_number)

    # Função para ir para a próxima página
    def go_to_next_page(e):
        page_number = min(total_pages, int(current_page.value) + 1)
        current_page.value = str(page_number)
        current_page.update()
        load_page(page_number)

    # Função para criar os controles de paginação
    def create_pagination_controls():
        return ft.Row(
            controls=[
                ft.IconButton(ft.icons.ARROW_BACK, on_click=go_to_previous_page),
                current_page,
                ft.IconButton(ft.icons.ARROW_FORWARD, on_click=go_to_next_page),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

    # Container para os ícones
    icons_container = ft.Column(spacing=10, expand=True)

    # Adicionando os controles na página
    page.add(
        create_pagination_controls(), icons_container, create_pagination_controls()
    )

    # Carregando a primeira página
    load_page(1)


ft.app(target=main)
