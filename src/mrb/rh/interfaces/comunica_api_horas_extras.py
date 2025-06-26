import flet as ft
import requests

from src.mrb.common.config import ApiConfiguration
from src.mrb.common.lib.aviso import Aviso
from src.mrb.common.interfaces.auth.auth_session import AuthSession


class ComunicaApiHorasExtras:
    def __init__(self, page: ft.Page):
        self.page = page

    def envia_alteracao_solicitacao(self, dados_solicitacao: dict) -> bool:
        retorno_atualizacao = True
        response_solicitacoes = requests.put(
            headers={"Authorization": f"Bearer {AuthSession(self.page).token()}"},
            url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/solicitacao_horas_extras",
            json=dados_solicitacao,
        )
        if not response_solicitacoes.status_code == 200:
            if response_solicitacoes.status_code == 401:
                Aviso(
                    self.page,
                    content=f"Não autorizado: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Alteração de Solicitação",
                    actions=["Fechar"],
                ).exibir()
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

    def envia_inclusao_solicitacao(self, solicitacao_horas_extras: dict) -> bool:
        retorno_envio = False

        response_solicitacoes = requests.post(
            headers={"Authorization": f"Bearer {AuthSession(self.page).token()}"},
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
                Aviso(
                    self.page,
                    content=f"Não autorizado: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Requisição de Solicitações",
                    actions=["Fechar"],
                ).exibir()
                self.page.go("/logout")

            else:
                Aviso(
                    self.page,
                    content=f"Falha na requisição de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Requisição de Solicitações",
                    actions=["Fechar"],
                ).exibir()

        return retorno_envio

    def apagar_solicitacao(self, id_solicitacao: str) -> bool:
        resultado_apagar = False
        confirma_apagar_liberacao = (
            Aviso(
                self.page,
                content=f"Confirma excluir a Solicitação de Hora Extra Id {id_solicitacao}?\n\nEsta operação não poderá ser desfeita!",
                title="Exclusão de Solicitação",
                actions=["Sim", "Não"],
            ).exibir()
            == 0
        )
        if confirma_apagar_liberacao:
            response_solicitacoes = requests.delete(
                headers={"Authorization": f"Bearer {AuthSession(self.page).token()}"},
                url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/solicitacao_horas_extras/{id_solicitacao}",
            )
            if (
                response_solicitacoes.status_code == 204
                or response_solicitacoes.status_code == 200
            ):
                resultado_apagar = True

            else:
                if response_solicitacoes.status_code == 401:
                    Aviso(
                        self.page,
                        content=f"Não autorizado: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                        title="Alteração de Solicitação",
                        actions=["Fechar"],
                    ).exibir()
                    self.page.go("/logout")

                else:
                    Aviso(
                        self.page,
                        content=f"Falha na exclusão de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                        title="Alteração de Solicitação",
                        actions=["Fechar"],
                    ).exibir()

        return resultado_apagar

    def recupera_solicitacoes(self, parametros_requisicao: dict, end_point: str):
        retorno_solicitacoes = None
        response_solicitacoes = requests.get(
            headers={"Authorization": f"Bearer {AuthSession(self.page).token()}"},
            url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/{end_point}",
            params=parametros_requisicao,
        )

        if response_solicitacoes.status_code == 200:
            content_type = response_solicitacoes.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                retorno_solicitacoes = response_solicitacoes.content

            else:
                retorno_solicitacoes = response_solicitacoes.json()

        else:
            if response_solicitacoes.status_code == 401:
                Aviso(
                    self.page,
                    content=f"Não autorizado: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Alteração de Solicitação",
                    actions=["Fechar"],
                ).exibir()
                self.page.go("/logout")

            else:
                Aviso(
                    self.page,
                    content=f"Falha na requisição de dados da api: {response_solicitacoes.status_code} - {response_solicitacoes.json()['detail']}",
                    title="Requisição de Solicitações",
                    actions=["Fechar"],
                ).exibir()

        return retorno_solicitacoes
