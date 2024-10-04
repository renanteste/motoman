import uvicorn
import os

from src.mrb.common.config import ApiConfiguration, Environment
from src.mrb.rh.api.authrhhe import app


# Função para realizar a limpeza dos arquivos de token
def limpa_tokens():
    for arquivo in os.listdir(Environment.DIR_TOKENS):
        if os.path.isfile(os.path.join(Environment.DIR_TOKENS, arquivo)):
            os.remove(os.path.join(Environment.DIR_TOKENS, arquivo))


# Execução do serviço REST RH
if __name__ == "__main__":
    # Limpa os arquivos de token sempre que o sistema for iniciado
    limpa_tokens()
    # Inicia o serviço REST
    uvicorn.run(app, host=ApiConfiguration.rh.HOST, port=ApiConfiguration.rh.PORT)
