from datetime import datetime
from typing import Any, Callable

import flet as ft

from src.mrb.common.lib.aviso import Aviso


def preenche_data(evento, se_data_valida: Callable[..., Any] = None, *args, **kwargs):
    """
    Função genérica para ser chamada no método on_change de um TextField para digitação de data.
    \n
    Permite somente a entrada de números e impede a entrada de data inválida.
    \n
    Argumentos:
    \n
    'evento': objeto text field recebido pelo evento on_change.
    \n
    se_data_valida: função ou método que será executado caso a data digitada seja uma data válida.
    """
    page: ft.Page = evento.control.page

    # Somente executa se não for chamada via web, pois a atualização do conteúdo do campo
    # está provocando a seleção do que o usuário já digitou
    if not page.web:
        somente_digitos = "".join(filter(str.isdigit, evento.control.value))

        formatado = ""
        if len(somente_digitos) > 0:
            formatado += somente_digitos[:2]
        if len(somente_digitos) > 2:
            formatado += "/" + somente_digitos[2:4]
        if len(somente_digitos) > 4:
            formatado += "/" + somente_digitos[4:8]
        if len(somente_digitos) == 8:
            try:
                datetime.strptime(evento.control.value, "%d/%m/%Y")

            except ValueError:
                Aviso(
                    page, content="A data digitada é inválida!", actions=["Ok"]
                ).exibir()
                formatado = evento.control.data

        # Se a data formatada é vazia ou tem tamanho igual a 10 e é diferente da anterior, executa o filtro
        if (
            len(formatado) == 0 or len(formatado) == 10
        ) and not formatado == evento.control.data:
            evento.control.data = formatado

            if se_data_valida:
                se_data_valida(*args, **kwargs)

        evento.control.value = formatado

        evento.control.update()
