import os


class EmailConfiguration:
    ADDRESS = "mm.colato@hotmail.com"
    PASSWORD = "Mm3nd3sS422320"
    SMTP_SERVER = "smtp-mail.outlook.com"
    SMTP_PORT = 587
    SMTP_AUTENTICACAO = True
    SMTP_AUDITORIA = "ti3@ymb.ind.br"
    # ADDRESS = "report@motoman.com.br"
    # PASSWORD = "naofazdiferenca"
    # SMTP_SERVER = "172.22.8.35"
    # SMTP_PORT = 25


class ApiConfiguration:
    class rh:
        HOST = "127.0.0.1"
        PORT = 8000

    class comercial:
        HOST = "127.0.0.1"
        PORT = 8001


class SqlConfiguration:
    SERVER = "172.22.8.25"
    USER = "sa"
    PASSWORD = "Moto@zt8htgda"
    DATABASE = "ZT8HTG_DEV"


class Environment:
    ROOT = os.path.dirname(__file__)
    DIR_TOKENS = os.path.join(ROOT, "tokens")
    DIR_TEMPLATE = os.path.join(ROOT, "templates")
