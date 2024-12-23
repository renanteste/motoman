import logging
import os

from sqlalchemy import Connection, text
from src.mrb.common.database.db_engine import engine


def atualiza_tabelas():
    # Obtém a pasta atual do projeto
    pasta_raiz = os.path.abspath(__file__)
    while "portalpy" in pasta_raiz:
        nome_da_pasta = pasta_raiz[pasta_raiz.rfind("\\") + 1 :]
        if nome_da_pasta.startswith("portalpy"):
            break

        pasta_raiz = os.path.dirname(pasta_raiz)

    pasta_scripts = os.path.join(pasta_raiz, "scripts", "sql")

    # Localiza os arquivos com os scripts para criação das tabelas e índices
    arquivos_sql = []
    for root, _, files in os.walk(pasta_scripts):
        for file in files:
            if file.endswith(".sql"):
                arquivos_sql.append(os.path.join(root, file))

    with engine.connect() as conn:
        for arquivo_sql in arquivos_sql:
            try:
                with open(arquivo_sql, "r", encoding="utf-8") as arquivo:
                    script_sql = arquivo.read()
                    if not tabela_existe(script_sql, conn):
                        executa_script(script_sql, conn)

            except Exception as e:
                logging.error(f"Erro ao verificar ou criar tabelas: {e}")


def executa_script(script_sql: str, conn: Connection):
    instrucoes = [
        instrucao.strip() for instrucao in script_sql.split(";") if instrucao.strip()
    ]
    for instrucao in instrucoes:
        try:
            conn.execute(text(instrucao))
            conn.commit()

        except Exception as e:
            logging.error(f"Erro ao criar tabelas ou índices: {e}")


def tabela_existe(script_sql: str, conn: Connection) -> bool:
    tabela_existe = False
    nome_da_tabela: str = None
    string_inicial = "CREATE TABLE "
    string_final = "("

    posicao_inicial = script_sql.upper().find(string_inicial)

    if posicao_inicial > -1:
        posicao_inicial += len(string_inicial)
        posicao_final = script_sql.find(string_final, posicao_inicial)

        if posicao_final > -1:
            # Nome da tabela sem espaços no começo e no final
            nome_da_tabela = script_sql[posicao_inicial:posicao_final].strip()
            # Elimina eventuais quebras de linha ou tabulações
            nome_da_tabela = "".join(nome_da_tabela.splitlines()).replace("\t", "")

    if nome_da_tabela:
        # Verifica se a tabela existe no BD
        query = text(
            """
                SELECT
                    COUNT(*) AS CNT
                FROM
                    sysobjects
                WHERE
                    name = :nome_da_tabela
                    AND type = 'U'
        """
        )
        result = conn.execute(query, {"nome_da_tabela": nome_da_tabela}).fetchone()
        tabela_existe = result[0] > 0

    return tabela_existe
