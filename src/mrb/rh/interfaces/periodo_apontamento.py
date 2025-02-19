from datetime import date, datetime

import requests

from src.mrb.common.config import ApiConfiguration


class PeriodoApontamento:
    def __init__(self):
        self.inicio_periodo: date
        self.final_periodo: date
        self.erro_requisicao: str

    def obtem_periodo_apontamento(self, token: str) -> tuple[date, date]:
        """
        Obtém o período de apontamento vigente do ponto eletrônico do Protheus via API
        \n
        Retorna as datas iniciais e finais recuperadas.
        \n
        Em caso de falha na requisição, retorna nulos no lugar
        das datas e o erro fica armazenado na propriedade 'erro_requisicao'
        """
        response_periodo_apontamento = requests.get(
            headers={"Authorization": f"Bearer {token}"},
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
