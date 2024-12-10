import os


class EmailConfiguration:
    # ADDRESS = "mm.colato@hotmail.com"
    # PASSWORD = "Mm3nd3sS422320"
    # SMTP_SERVER = "smtp-mail.outlook.com"
    # SMTP_PORT = 587
    # SMTP_AUTENTICACAO = True

    ADDRESS = "token@motoman.com.br"
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


class SqlConfiguration:
    SERVER = "172.22.8.25"
    USER = "sa"
    PASSWORD = "Moto@zt8htgda"
    DATABASE = "ZT8HTG_DEV"


class Environment:
    ROOT = os.path.dirname(__file__)
    DIR_TEMPLATE = os.path.join(ROOT, "templates")
    PORTAL_PY_K = "B7lP8ZqJcN3X9rT1K2sV4W5eY6fG0qF3"
    DIR_LOG_APLICACAO = os.path.join(ROOT, "log")
    IMAGES_PATH = os.path.join("src", "mrb", "common", "assets", "images")
    # Substituir com o IP para acesso externo ao servidor
    SERVER_IP = "127.0.0.1"
