from datetime import date, datetime

import requests

from src.mrb.common.config import ApiConfiguration
from src.mrb.common.interfaces.auth.auth_session import AuthSession


class PeriodoApontamento:
    def __init__(self):
        self.inicio_periodo: date
        self.final_periodo: date
        self.erro_requisicao: str

    def obtem_periodo_apontamento(self) -> tuple[date, date]:
        """
        Obtém o período de apontamento vigente do ponto eletrônico do Protheus via API
        \n
        Retorna as datas iniciais e finais recuperadas.
        \n
        Em caso de falha na requisição, retorna nulos no lugar
        das datas e o erro fica armazenado na propriedade 'erro_requisicao'
        """
        auth_session = AuthSession()
        response_periodo_apontamento = requests.get(
            headers={"Authorization": f"Bearer {auth_session.token}"},
            url=f"http://{ApiConfiguration.rh.SERVER}:{ApiConfiguration.rh.PORT}/recupera_parametro_sx6/MV_PONMES",
        )
        if response_periodo_apontamento.status_code == 200:
            self.erro_requisicao = None
            retorno_periodo_apontamento: str = response_periodo_apontamento.json()[
                "conteudo_parametro"
            ]
            self.inicio_periodo = datetime.strptime(
                retorno_periodo_apontamento.split("/")[0], "%Y%m%d"
            ).date()
            self.final_periodo = datetime.strptime(
                retorno_periodo_apontamento.split("/")[1], "%Y%m%d"
            ).date()

        else:
            self.erro_requisicao = f"Código: {response_periodo_apontamento.status_code} - {response_periodo_apontamento.json()['detail']}"
            self.inicio_periodo = None
            self.final_periodo = None

        return (self.inicio_periodo, self.final_periodo)

    def verifica_data_periodo(self, data_informada: date) -> bool:
        """
        Retorna True se a data informada no argumento 'data_informada' está no período de apontamento vigente
        """
        self.obtem_periodo_apontamento()
        data_periodo = False

        if (
            self.inicio_periodo
            and self.final_periodo
            and data_informada >= self.inicio_periodo
            and data_informada <= self.final_periodo
        ):
            data_periodo = True

        return data_periodo
