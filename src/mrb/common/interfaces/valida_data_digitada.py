from datetime import datetime
from typing import Any, Callable
import flet as ft

from src.mrb.common.lib.aviso import Aviso


def valida_data_digitada(
    evento, se_data_valida: Callable[..., Any] = None, *args, **kwargs
):
    """
    Função deve ser chamada pelo evento on_blur de um TextField para garantir que os dados digitados correspondem a uma data válida.
    \n
    Recebe como argumento o evento gerado pelo TextField e uma função ou método que será executado caso a data digitada seja válida.
    \n
    A função valida_data_digitada somente é executada se o programa estiver sendo executado via web.
    """
    page: ft.Page = evento.control.page
    campo_data: ft.TextField = evento.control

    # Executa somente se for chamada via web
    if page.web:
        data_valida = True

        # Primeiro, remove todos os caracteres não numéricos
        somente_digitos = "".join(filter(str.isdigit, campo_data.value))

        # Se o tamanho do conteúdo for 6, insere o século atual
        if len(somente_digitos) == 6:
            somente_digitos = f"{somente_digitos[:4]}{str(datetime.now().year)[:2]}{somente_digitos[-2:]}"

        # Verifica se a data é válida se o tamanho do conteúdo for maior que 0
        if len(somente_digitos) > 0:
            try:
                datetime.strptime(somente_digitos, "%d%m%Y")

            except ValueError:
                Aviso(
                    page, content="A data digitada é inválida!", actions=["Ok"]
                ).exibir()
                data_valida = False

            if data_valida:
                # Se a data é válida, preenche as barras
                campo_data.value = datetime.strptime(
                    somente_digitos, "%d%m%Y"
                ).strftime("%d/%m/%Y")

            else:
                # Se a data é inválida, devolve o valor anterior
                campo_data.value = campo_data.data

            campo_data.update()

        # Se a data formatada é vazia ou tem tamanho igual a 10 e é diferente da anterior, executa o filtro
        if (
            len(campo_data.value) == 0 or len(campo_data.value) == 10
        ) and not campo_data.value == campo_data.data:
            campo_data.data = campo_data.value
            campo_data.update()

            if se_data_valida:
                se_data_valida(*args, **kwargs)
