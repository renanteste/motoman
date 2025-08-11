import os


class EmailConfiguration:
    # ADDRESS = "mm.colato@hotmail.com"
    # PASSWORD = ""
    # SMTP_SERVER = "smtp-mail.outlook.com"
    # SMTP_PORT = 587
    # SMTP_AUTENTICACAO = True

    ADDRESS = "senha.portal.mrb@motoman.com.br"
    PASSWORD = "naofazdiferenca"
    SMTP_SERVER = "172.22.8.35"
    SMTP_PORT = 25
    SMTP_AUTENTICACAO = False

    SMTP_AUDITORIA = "ti3@ymb.ind.br"


class ApiConfiguration:
    class auth:
        URL = "127.0.0.1"
        PORT = 8000

    class rh:
        HOST = "0.0.0.0"
        PORT = 8000
        SERVER = "127.0.0.1"

    class comercial:
        HOST = "0.0.0.0"
        PORT = 8001

    class Coletores:
        HOST = "0.0.0.0"
        PORT = 63001
        HOST_BACKEND = "0.0.0.0"
        PORT_BACKEND = 63002
        QUANTIDADE_WORKERS = 1

        class Certificado:
            # Se informados os arquivos, a solução subirá como https
            ARQUIVO_CERTIFICADO = None
            ARQUIVO_CHAVE_CERTIFICADO = None


class SqlConfiguration:
    SERVER = "172.22.8.25"
    USER = "sa"
    PASSWORD = "TW90b0B6dDhodGdkYQ=="
    DATABASE = "ZT8HTG_DEV"


class Environment:
    ROOT = os.path.dirname(__file__)
    DIR_TEMPLATE = os.path.join(ROOT, "templates")
    PORTAL_PY_K = "B7lP8ZqJcN3X9rT1K2sV4W5eY6fG0qF3"
    DIR_LOG_APLICACAO = os.path.join(ROOT, "log")
    IMAGES_PATH = os.path.join("src", "mrb", "common", "assets", "images")
    LOGOTIPO_RELATORIOS = os.path.join(IMAGES_PATH, "logo_yaskawa.png")
    # Substituir com o IP para acesso externo ao servidor
    SERVER_IP = "127.0.0.1"
    CAMINHO_RELATORIOS = os.path.join("src", "mrb", "common", "temp", "relatorios")
    # Chave compartilhada com a aplicação do coletor utilizada na autenticação
    CHAVE_COLETOR = "Q8%pA2!kZzL7$wMEr3#vNgTb@CHAVE_COLETOR"
    # URL do serviço REST do Protheus
    URL_REST_PROTHEUS = "http://172.22.8.25:3001/rest"
