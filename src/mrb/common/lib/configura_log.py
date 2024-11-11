from datetime import datetime
import logging
import os

from src.mrb.common.config import Environment


def configura_log(nome_aplicao: str):
    # Cria a pasta onde serão armazenados os arquivos de log
    if not os.path.exists(Environment.DIR_LOG_APLICACAO):
        os.makedirs(Environment.DIR_LOG_APLICACAO)

    # Cria um arquivo de log a cada inicialização
    nome_arquivo_log = os.path.join(
        Environment.DIR_LOG_APLICACAO,
        f"{datetime.now().strftime('%Y%m%d')}_{nome_aplicao}.log",
    )

    # Configura o log para gravar as informações do ARQUIVO
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(nome_arquivo_log, mode="a"),
            logging.StreamHandler(),
        ],
    )
