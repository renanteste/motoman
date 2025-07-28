from datetime import datetime
from fastapi import status
from fastapi.responses import RedirectResponse
from requests import Request, Response
import requests

from src.mrb.common.config import ApiConfiguration
from src.mrb.common.lib.calcula_max_age import calcula_max_age


class PreparaResponse:
    def __init__(
        self, request: Request, novo_token: str = None, nova_validade: datetime = None
    ) -> None:
        self.request = request
        self.novo_token = novo_token
        self.nova_validade = nova_validade
        self.token: str = None
        self.refresh_token: str = None
        self.nome_usuario = ""

    def retorna_response(self, response: RedirectResponse):
        if self.novo_token:
            response.set_cookie(
                key="access_token",
                value=self.novo_token,
                httponly=True,
                secure=self.request.url.scheme == "https",
                samesite="lax",
                max_age=calcula_max_age(self.nova_validade),
            )
            self.token = self.novo_token
            self.novo_token = None
            self.nova_validade = None

        return response

    def valida_tokens(self) -> bool:
        self.token = self.request.cookies.get("access_token")
        self.refresh_token = self.request.cookies.get("refresh_token")
        self.nome_usuario = self.request.cookies.get("nome_usuario", "")
        return self.token or self.refresh_token

    def exec_request(
        self, url: str, metodo: str, headers: dict = None, dados: dict = None
    ) -> Response:
        if headers:
            # Remove a referência caso exista
            headers = headers.copy()

        else:
            # Inicializa o dicionário
            headers = {}

        if self.token:
            # Informa o token atual na autorização
            headers["Authorization"] = f"Bearer {self.token}"

            # Faz a requisição
            response = requests.request(
                method=metodo, url=url, headers=headers, json=dados
            )

        else:
            response: Response = None

        # Caso tenha retorno "não autorizado", chama o refresh token
        if (
            not self.token or response.status_code == status.HTTP_401_UNAUTHORIZED
        ) and self.refresh_token:
            response_refresh = requests.post(
                f"http://{ApiConfiguration.auth.URL}:{ApiConfiguration.auth.PORT}/refresh_token",
                json={"refresh_token": self.refresh_token},
            )

            if response_refresh.status_code == status.HTTP_200_OK:
                self.novo_token = response_refresh.json()["token"]
                self.nova_validade = datetime.fromisoformat(
                    response_refresh.json()["validade"]
                )
                headers["Authorization"] = f"Bearer {self.novo_token}"
                response = requests.request(
                    method=metodo, url=url, headers=headers, json=dados
                )

            else:
                response = response_refresh

        return response
