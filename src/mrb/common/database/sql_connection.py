import pymssql
from src.mrb.common.config import SqlConfiguration


def get_connection():
    try:
        connection = pymssql.connect(
            server=SqlConfiguration.SERVER,
            user=SqlConfiguration.USER,
            password=SqlConfiguration.PASSWORD,
            database=SqlConfiguration.DATABASE,
        )
        return connection
    except Exception as e:
        return f"Erro ao conectar ao banco de dados: {e}"
